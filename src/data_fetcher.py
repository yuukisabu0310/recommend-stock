"""
市場データ取得モジュール
APIからデータを取得し、統一フォーマットで返す
"""

import yaml
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from pathlib import Path

try:
    import yfinance as yf
except ImportError:
    yf = None

logger = logging.getLogger(__name__)


class DataFetcher:
    """市場データ取得クラス"""
    
    def __init__(self, config_path: str = "config/config.yml"):
        """初期化"""
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.output_dir = Path(self.config['output']['directory'])
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.fallback_dir = self.output_dir / "fallback"
        self.fallback_dir.mkdir(parents=True, exist_ok=True)
        
        # API設定
        self.use_yahoo = self.config['api'].get('yahoo_finance', {}).get('enabled', True)
    
    def get_index_data(self, index_code: str, country_code: str, days: int = 365) -> Optional[Dict]:
        """
        インデックスデータを取得
        
        Args:
            index_code: インデックスコード（SPX, N225等）
            country_code: 国コード（US, JP, CN）
            days: 取得日数
        
        Returns:
            インデックスデータの辞書
        """
        try:
            # Yahoo Finance用のティッカーに変換
            ticker_map = {
                "SPX": "^GSPC",  # S&P500
                "NDX": "^NDX",   # NASDAQ100
                "N225": "^N225", # 日経225
                "TPX": "^TPX",   # TOPIX
                "SSE": "000001.SS",  # 上海総合
                "HSI": "^HSI",   # ハンセン指数
            }
            
            ticker = ticker_map.get(index_code)
            if not ticker or not yf:
                logger.warning(f"データ取得不可: {index_code}")
                return self._load_fallback_data(f"{country_code}_{index_code}")
            
            # データ取得
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            stock = yf.Ticker(ticker)
            hist = stock.history(start=start_date, end=end_date)
            
            if hist.empty:
                return self._load_fallback_data(f"{country_code}_{index_code}")
            
            # 最新価格とMA200の計算
            latest_price = float(hist['Close'].iloc[-1])
            ma200 = float(hist['Close'].tail(200).mean()) if len(hist) >= 200 else latest_price
            
            # ボラティリティ計算（過去30日）
            recent_returns = hist['Close'].pct_change().tail(30)
            volatility = float(recent_returns.std() * (252 ** 0.5))  # 年率換算
            
            # 出来高データ
            avg_volume_30 = float(hist['Volume'].tail(30).mean())
            latest_volume = float(hist['Volume'].iloc[-1])
            
            data = {
                "index_code": index_code,
                "country_code": country_code,
                "latest_price": latest_price,
                "ma200": ma200,
                "price_vs_ma200": (latest_price / ma200 - 1) * 100,  # パーセンテージ
                "volatility": volatility,
                "volume_ratio": latest_volume / avg_volume_30 if avg_volume_30 > 0 else 1.0,
                "date": datetime.now().isoformat(),
                "historical_prices": hist['Close'].tail(30).tolist()  # 直近30日
            }
            
            # フォールバックデータとして保存
            self._save_fallback_data(f"{country_code}_{index_code}", data)
            
            return data
            
        except Exception as e:
            logger.error(f"データ取得エラー ({index_code}): {e}")
            return self._load_fallback_data(f"{country_code}_{index_code}")
    
    def get_macro_indicators(self, country_code: str) -> Dict:
        """
        マクロ経済指標を取得（モックデータ、実際はAPIから取得）
        
        Args:
            country_code: 国コード
        
        Returns:
            マクロ指標の辞書
        """
        # 実際の実装では、FRED API、各国統計局APIなどを使用
        # ここではモックデータを返す
        return {
            "country_code": country_code,
            "PMI": None,  # 実装時はAPIから取得
            "CPI": None,
            "employment_rate": None,
            "date": datetime.now().isoformat()
        }
    
    def get_financial_indicators(self, country_code: str) -> Dict:
        """
        金融指標を取得（モックデータ）
        
        Args:
            country_code: 国コード
        
        Returns:
            金融指標の辞書
        """
        return {
            "country_code": country_code,
            "policy_rate": None,
            "long_term_rate": None,
            "credit_spread": None,
            "date": datetime.now().isoformat()
        }
    
    def get_stock_universe(self, universe_name: str, country_code: str) -> List[str]:
        """
        銘柄ユニバースを取得
        
        Args:
            universe_name: ユニバース名（S&P500等）
            country_code: 国コード
        
        Returns:
            ティッカーリスト
        """
        # 実際の実装では、各ユニバースのリストを取得
        # ここでは限定的なモックリストを返す
        
        mock_universes = {
            "US": {
                "S&P500": ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK-B", "V", "JNJ"],
                "NASDAQ100": ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AVGO", "COST", "ADBE"]
            },
            "JP": {
                "TOPIX Core30": ["7203.T", "6758.T", "6861.T", "9984.T", "8035.T"],
                "TOPIX Large70": ["7203.T", "6758.T", "6861.T", "9984.T", "8035.T", "4063.T", "6098.T"],
                "TOPIX Mid400": ["7203.T", "6758.T", "6861.T"]
            },
            "CN": {
                "CSI300": ["000001.SS", "000002.SS", "600000.SS"]
            }
        }
        
        return mock_universes.get(country_code, {}).get(universe_name, [])
    
    def get_stock_data(self, ticker: str, days: int = 365) -> Optional[Dict]:
        """
        個別銘柄データを取得
        
        Args:
            ticker: ティッカーシンボル
            days: 取得日数
        
        Returns:
            銘柄データの辞書
        """
        try:
            if not yf:
                return None
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            stock = yf.Ticker(ticker)
            hist = stock.history(start=start_date, end=end_date)
            info = stock.info
            
            if hist.empty:
                return None
            
            latest_price = float(hist['Close'].iloc[-1])
            ma200 = float(hist['Close'].tail(200).mean()) if len(hist) >= 200 else latest_price
            
            data = {
                "ticker": ticker,
                "name": info.get("longName", ticker),
                "latest_price": latest_price,
                "ma200": ma200,
                "price_vs_ma200": (latest_price / ma200 - 1) * 100,
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "date": datetime.now().isoformat()
            }
            
            return data
            
        except Exception as e:
            logger.error(f"銘柄データ取得エラー ({ticker}): {e}")
            return None
    
    def _save_fallback_data(self, key: str, data: Dict):
        """フォールバックデータを保存"""
        try:
            filepath = self.fallback_dir / f"{key}.json"
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"フォールバックデータ保存失敗 ({key}): {e}")
    
    def _load_fallback_data(self, key: str) -> Optional[Dict]:
        """フォールバックデータを読み込み"""
        try:
            filepath = self.fallback_dir / f"{key}.json"
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"フォールバックデータを使用: {key}")
                    return data
        except Exception as e:
            logger.warning(f"フォールバックデータ読み込み失敗 ({key}): {e}")
        
        return None
    
    def fetch_all_data(self) -> Dict:
        """
        全データを取得
        
        Returns:
            全データの辞書
        """
        all_data = {
            "countries": {},
            "timestamp": datetime.now().isoformat()
        }
        
        for country_config in self.config['countries']:
            country_code = country_config['code']
            country_name = country_config['name']
            
            country_data = {
                "name": country_name,
                "code": country_code,
                "indices": {},
                "macro": self.get_macro_indicators(country_code),
                "financial": self.get_financial_indicators(country_code)
            }
            
            # インデックスデータ取得
            for index_code in country_config['indices']:
                index_data = self.get_index_data(index_code, country_code)
                if index_data:
                    country_data["indices"][index_code] = index_data
            
            all_data["countries"][country_code] = country_data
        
        return all_data


"""
市場データ取得モジュール
APIからデータを取得し、統一フォーマットで返す
"""

import yaml
import os
import json
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from pathlib import Path
import time


try:
    import yfinance as yf
except ImportError:
    yf = None

try:
    from fredapi import Fred
    FRED_AVAILABLE = True
except ImportError:
    Fred = None
    FRED_AVAILABLE = False

import requests

logger = logging.getLogger(__name__)

# logger定義後に警告を出力
if not FRED_AVAILABLE:
    logger.warning("fredapiライブラリがインストールされていません。FRED API機能は無効化されます。")


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
        
        # FRED API設定
        self.fred_api_key = os.getenv('FRED_API_KEY')
        self.fred_client = None
        if not FRED_AVAILABLE:
            logger.error("fredapiライブラリがインストールされていません。FRED API機能は無効化されます。pip install fredapi を実行してください。")
        elif not self.fred_api_key:
            logger.error("FRED_API_KEYが設定されていません。FRED API機能は無効化されます。環境変数またはGitHub SecretsにFRED_API_KEYを設定してください。")
        else:
            try:
                self.fred_client = Fred(api_key=self.fred_api_key)
                logger.info("FRED APIクライアントを初期化しました")
            except Exception as e:
                logger.error(f"FRED API初期化エラー: {e}")
        
        # e-Stat API設定
        self.estat_app_id = os.getenv('ESTAT_APP_ID')
        if not self.estat_app_id:
            logger.error("ESTAT_APP_IDが設定されていません。e-Stat API機能は無効化されます。環境変数またはGitHub SecretsにESTAT_APP_IDを設定してください。")
    
    def get_index_data(self, index_code: str, country_code: str, days: int = 365) -> Optional[Dict]:
        """
        インデックスデータを取得
        
        Args:
            index_code: インデックスコード（SPX, N225等）
            country_code: 国コード（US, JP）
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
            
            # データ取得（リトライロジック付き）
            max_retries = 3
            retry_delay = 2  # 秒
            
            for attempt in range(max_retries):
                try:
                    stock = yf.Ticker(ticker)
                    # 期間に応じたデータ取得（start/endを使用して正確な期間を指定）
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=days)
                    
                    # Yahoo Financeのperiodパラメータも試行（フォールバック用）
                    if days <= 30:
                        period = "1mo"
                    elif days <= 90:
                        period = "3mo"
                    elif days <= 180:
                        period = "6mo"
                    elif days <= 365:
                        period = "1y"
                    elif days <= 730:
                        period = "2y"
                    elif days <= 1825:
                        period = "5y"
                    else:
                        period = "10y"
                    
                    # start/endで取得を試行（より正確）
                    hist = stock.history(start=start_date, end=end_date)
                    
                    if not hist.empty:
                        break
                    
                    # 空の場合はperiodパラメータで再試行
                    if attempt < max_retries - 1:
                        hist = stock.history(period=period)
                        if not hist.empty:
                            break
                    
                    if attempt < max_retries - 1:
                        logger.warning(f"データ取得失敗 ({index_code}), リトライ中... ({attempt + 1}/{max_retries})")
                        time.sleep(retry_delay)
                    
                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"データ取得エラー ({index_code}): {e}, リトライ中... ({attempt + 1}/{max_retries})")
                        time.sleep(retry_delay)
                    else:
                        logger.error(f"データ取得最終失敗 ({index_code}): {e}")
                        return self._load_fallback_data(f"{country_code}_{index_code}")
            
            if hist.empty:
                logger.warning(f"データが空です ({index_code})")
                return self._load_fallback_data(f"{country_code}_{index_code}")
            
            # 最新価格
            latest_price = float(hist['Close'].iloc[-1])
            
            # 時系列データを取得（日次終値と日付）
            historical_prices = [float(x) for x in hist['Close'].tolist()]
            historical_dates = [d.strftime("%Y-%m-%d") if hasattr(d, 'strftime') else str(d) for d in hist.index]
            
            # 移動平均の計算（20日、75日、200日）- 最新値のみ（既存ロジック維持）
            ma20 = float(hist['Close'].tail(20).mean()) if len(hist) >= 20 else latest_price
            ma75 = float(hist['Close'].tail(75).mean()) if len(hist) >= 75 else latest_price
            ma200 = float(hist['Close'].tail(200).mean()) if len(hist) >= 200 else latest_price
            
            # トレンド判定（移動平均の順序で判定）
            # 上昇トレンド: 価格 > MA20 > MA75 > MA200
            # 下降トレンド: 価格 < MA20 < MA75 < MA200
            trend_score = 0  # -2 (超弱気) ～ +2 (超強気)
            if latest_price > ma20 > ma75 > ma200:
                trend_score = 2  # 強気
            elif latest_price > ma20 > ma75:
                trend_score = 1  # やや強気
            elif ma20 > ma75 > ma200:
                trend_score = 1  # やや強気
            elif latest_price < ma20 < ma75 < ma200:
                trend_score = -2  # 弱気
            elif latest_price < ma20 < ma75:
                trend_score = -1  # やや弱気
            elif ma20 < ma75 < ma200:
                trend_score = -1  # やや弱気
            
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
                "ma20": ma20,
                "ma75": ma75,
                "ma200": ma200,
                "price_vs_ma20": (latest_price / ma20 - 1) * 100,  # パーセンテージ
                "price_vs_ma75": (latest_price / ma75 - 1) * 100,
                "price_vs_ma200": (latest_price / ma200 - 1) * 100,
                "trend_score": trend_score,  # トレンドスコア
                "volatility": volatility,
                "volume_ratio": latest_volume / avg_volume_30 if avg_volume_30 > 0 else 1.0,
                "date": datetime.now().isoformat(),
                "historical_prices": historical_prices,  # 時系列データ（全期間）
                "historical_dates": historical_dates  # 時系列日付データ
            }
            
            # フォールバックデータとして保存
            self._save_fallback_data(f"{country_code}_{index_code}", data)
            
            return data
            
        except Exception as e:
            logger.error(f"データ取得エラー ({index_code}): {e}")
            return self._load_fallback_data(f"{country_code}_{index_code}")
    
    def _get_fred_data(self, series_id: str, country_code: str, max_retries: int = 3) -> Optional[float]:
        """
        FRED APIからデータを取得（リトライ付き）
        
        Args:
            series_id: FREDシリーズID
            country_code: 国コード
            max_retries: 最大リトライ回数
        
        Returns:
            最新値（float）またはNone
        """
        if not self.fred_client:
            logger.warning(f"FRED APIクライアントが初期化されていません ({series_id}, {country_code})")
            return None
        
        for attempt in range(max_retries):
            try:
                data = self.fred_client.get_series(series_id, limit=1)
                if not data.empty:
                    value = float(data.iloc[-1])
                    logger.debug(f"FRED API取得成功 ({series_id}, {country_code}): {value}")
                    return value
                else:
                    logger.warning(f"FRED APIデータが空です ({series_id}, {country_code}, 試行 {attempt + 1}/{max_retries})")
            except Exception as e:
                logger.warning(f"FRED API取得エラー ({series_id}, {country_code}, 試行 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数バックオフ
        
        logger.error(f"FRED API取得最終失敗 ({series_id}, {country_code})")
        return None
    
    def _get_fred_series_data(self, series_id: str, country_code: str, start_date: Optional[datetime] = None, max_retries: int = 3) -> Optional[List[Dict[str, Any]]]:
        """
        FRED APIから時系列データを取得（リトライ付き）
        
        Args:
            series_id: FREDシリーズID
            country_code: 国コード
            start_date: 開始日（Noneの場合は取得可能な最大期間）
            max_retries: 最大リトライ回数
        
        Returns:
            時系列データのリスト [{"date": str, "value": float}, ...] またはNone
        """
        if not self.fred_client:
            logger.warning(f"FRED APIクライアントが初期化されていません ({series_id}, {country_code})")
            return None
        
        for attempt in range(max_retries):
            try:
                if start_date:
                    data = self.fred_client.get_series(series_id, start=start_date)
                else:
                    # 取得可能な最大期間を取得（limit指定なし）
                    data = self.fred_client.get_series(series_id)
                
                if not data.empty:
                    # 日付と値をリストに変換（pandas Seriesから）
                    series_list = []
                    for date in data.index:
                        value = data[date]
                        # NaNチェック
                        try:
                            # pandasのNaNチェック（math.isnan()でNaNをチェック）
                            if value is not None and not (isinstance(value, float) and math.isnan(value)):
                                series_list.append({
                                    "date": date.strftime("%Y-%m-%d") if hasattr(date, 'strftime') else str(date),
                                    "value": float(value)
                                })
                        except (ValueError, TypeError, OverflowError):
                            continue
                    # 日付でソート（既にソートされているはずだが念のため）
                    series_list.sort(key=lambda x: x["date"])
                    logger.debug(f"FRED API時系列データ取得成功 ({series_id}, {country_code}): {len(series_list)}件")
                    return series_list
                else:
                    logger.warning(f"FRED API時系列データが空です ({series_id}, {country_code}, 試行 {attempt + 1}/{max_retries})")
            except Exception as e:
                logger.warning(f"FRED API時系列取得エラー ({series_id}, {country_code}, 試行 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数バックオフ
        
        logger.error(f"FRED API時系列取得最終失敗 ({series_id}, {country_code})")
        return None
    
    def _calculate_cpi_yoy_series(self, cpi_raw_series: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        CPI生データから前年比（YoY）時系列を計算
        
        Args:
            cpi_raw_series: CPI生データの時系列 [{"date": str, "value": float}, ...]（月次データ）
        
        Returns:
            前年比（YoY）時系列 [{"date": str, "value": float}, ...]
        """
        if not cpi_raw_series or len(cpi_raw_series) < 13:
            return []
        
        # 日付でソート（月次データなので、時系列順に並んでいることを前提）
        sorted_series = sorted(cpi_raw_series, key=lambda x: x["date"])
        
        yoy_series = []
        # 12ヶ月前のデータと比較（月次データなので、インデックスで12個前を参照）
        for i in range(12, len(sorted_series)):
            current_item = sorted_series[i]
            prev_item = sorted_series[i - 12]  # 12ヶ月前
            
            try:
                current_value = float(current_item["value"])
                prev_value = float(prev_item["value"])
                
                if prev_value > 0:
                    yoy = ((current_value / prev_value) - 1) * 100
                    yoy_series.append({
                        "date": current_item["date"],
                        "value": yoy
                    })
            except (ValueError, KeyError, TypeError) as e:
                logger.debug(f"CPI YoY計算エラー ({current_item.get('date', 'unknown')}): {e}")
                continue
        
        return yoy_series
    
    def get_macro_indicators(self, country_code: str, index_data: Optional[Dict] = None) -> Dict:
        """
        マクロ経済指標を取得（実データ）
        
        Args:
            country_code: 国コード
            index_data: インデックスデータ（PMI推測に使用）
        
        Returns:
            マクロ指標の辞書（CPI時系列データを含む）
        """
        # FRED APIシリーズIDマッピング
        fred_series = {
            "US": {
                "CPI": "CPIAUCSL",  # Consumer Price Index for All Urban Consumers: All Items in U.S. City Average
                "employment_rate": "EMRATIO",  # Employment-Population Ratio
            },
            "JP": {
                "CPI": "JPNCPIALLMINMEI",  # Consumer Price Index: All Items for Japan
                "employment_rate": "LRAC64TTJPM156S",  # Labor Force Participation Rate: Aged 15-64: All Persons for Japan
            }
        }
        
        # CPI: FRED APIから取得（最新値と時系列データ）
        cpi = None
        cpi_series = None
        if country_code == "US":
            if not self.fred_client:
                logger.error(f"FRED APIクライアントが初期化されていません。CPIを取得できません ({country_code})")
            else:
                # 時系列データを取得（最大10年分）
                cpi_raw_series = self._get_fred_series_data(fred_series["US"]["CPI"], country_code, start_date=None)
                if cpi_raw_series:
                    # 前年比（YoY）時系列を計算
                    cpi_series = self._calculate_cpi_yoy_series(cpi_raw_series)
                    # 最新値（時系列の最後の値）
                    if cpi_series:
                        cpi = cpi_series[-1]["value"]
                        logger.info(f"CPI時系列データ取得成功 ({country_code}): {len(cpi_series)}件, 最新値: {cpi:.2f}%")
        elif country_code == "JP":
            # 日本: FRED APIから取得を試行
            if fred_series["JP"]["CPI"] and self.fred_client:
                cpi_raw_series = self._get_fred_series_data(fred_series["JP"]["CPI"], country_code, start_date=None)
                if cpi_raw_series:
                    cpi_series = self._calculate_cpi_yoy_series(cpi_raw_series)
                    if cpi_series:
                        cpi = cpi_series[-1]["value"]
                        logger.info(f"CPI時系列データ取得成功 ({country_code}): {len(cpi_series)}件, 最新値: {cpi:.2f}%")
            
            # FRED APIが失敗した場合はe-Stat APIから取得を試行（最新値のみ）
            if cpi is None:
                cpi = self._get_japan_cpi()
        
        # 雇用率: FRED APIから取得
        employment_rate = None
        if country_code == "US":
            if not self.fred_client:
                logger.error(f"FRED APIクライアントが初期化されていません。雇用率を取得できません ({country_code})")
            else:
                employment_rate = self._get_fred_data(fred_series["US"]["employment_rate"], country_code)
                if employment_rate is not None:
                    logger.info(f"雇用率取得成功 ({country_code}): {employment_rate:.2f}%")
                else:
                    logger.error(f"雇用率取得失敗 ({country_code})")
        elif country_code == "JP":
            # 日本: e-Stat APIから取得を試行（公式データを優先）
            employment_rate = self._get_japan_employment_rate()
            
            # e-Stat APIが失敗した場合はFRED APIをフォールバックとして使用
            if employment_rate is None and fred_series["JP"]["employment_rate"]:
                employment_rate = self._get_fred_data(fred_series["JP"]["employment_rate"], country_code)
        
        # PMI: インデックスデータから推測（実データ取得が困難なため）
        pmi = None
        if index_data:
            price_vs_ma = index_data.get("price_vs_ma200", 0)
            if price_vs_ma > 2:
                pmi = 52.0
            elif price_vs_ma > 0:
                pmi = 50.5
            elif price_vs_ma > -2:
                pmi = 49.5
            else:
                pmi = 48.0
        
        result = {
            "country_code": country_code,
            "PMI": pmi,
            "CPI": cpi,
            "CPI_series": cpi_series,  # 時系列データ（前年比YoY）
            "employment_rate": employment_rate,
            "date": datetime.now().isoformat()
        }
        # 返り値をログ出力（nullチェック）
        logger.info(f"get_macro_indicators返り値 ({country_code}): PMI={pmi}, CPI={cpi}, employment_rate={employment_rate}")
        if cpi is None:
            logger.warning(f"CPIがnullです ({country_code})")
        if cpi_series:
            logger.info(f"CPI時系列データ ({country_code}): {len(cpi_series)}件")
        if employment_rate is None:
            logger.warning(f"雇用率がnullです ({country_code})")
        return result
    
    def _get_japan_cpi(self) -> Optional[float]:
        """日本のCPIを取得（総務省統計局API）"""
        # 総務省統計局のe-Stat APIを使用
        # 簡易実装: 日本銀行統計データAPIから取得
        try:
            # 日本銀行統計データAPI（無料、APIキー不要）
            url = "https://www.stat-search.boj.or.jp/ssi/mtshtml/csv/m_ir_m_1.csv"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                # CSVをパースして最新のCPIデータを取得
                # 実際の実装では、適切なCSVパースが必要
                logger.info("日本のCPIデータ取得を試行しました（実装要）")
        except Exception as e:
            logger.warning(f"日本のCPI取得エラー: {e}")
        
        return None
    
    def _get_japan_employment_rate(self) -> Optional[float]:
        """日本の雇用率を取得（e-Stat API）"""
        if not self.estat_app_id:
            logger.debug("ESTAT_APP_IDが設定されていません。e-Stat APIから雇用率を取得できません。")
            return None
        
        try:
            # e-Stat API: 労働力調査から雇用率を取得
            # 統計表ID: 0000022181 (労働力調査 基本集計 全国 月次)
            # 詳細: https://www.e-stat.go.jp/stat-search/files?page=1&toukei=00200531&tstat=000000330001
            
            url = "https://api.e-stat.go.jp/rest/3.0/app/json/getStatsData"
            params = {
                "appId": self.estat_app_id,
                "lang": "J",
                "statsDataId": "0000022181",  # 労働力調査の統計データID
                "metaGetFlg": "N",
                "cntGetFlg": "N",
                "explanationGetFlg": "Y",
                "annotationGetFlg": "Y",
                "sectionHeaderFlg": "1",
                "replaceSpChars": "0"
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                # JSONレスポンスをパースして最新の雇用率データを取得
                if "GET_STATS_DATA" in data and "STATISTICAL_DATA" in data["GET_STATS_DATA"]:
                    logger.info("e-Stat APIから雇用率データを取得しました（パース実装要）")
                    # TODO: 実際の雇用率データをパースして返す
        except Exception as e:
            logger.warning(f"日本の雇用率取得エラー (e-Stat API): {e}")
        
        return None
    
    
    def get_financial_indicators(self, country_code: str, index_data: Optional[Dict] = None) -> Dict:
        """
        金融指標を取得（実データ）
        
        Args:
            country_code: 国コード
            index_data: インデックスデータ（クレジットスプレッド推測に使用）
        
        Returns:
            金融指標の辞書（最新値と時系列データを含む）
        """
        # FRED APIシリーズIDマッピング
        fred_series = {
            "US": {
                "policy_rate": "FEDFUNDS",  # Effective Federal Funds Rate
                "long_term_rate": "DGS10",  # 10-Year Treasury Constant Maturity Rate
            },
            "JP": {
                "policy_rate": "IRSTCI01JPM156N",  # Immediate Rates: Call Money/Interbank Rate: Total: Total for Japan (代替指標)
                "long_term_rate": "IRLTLT01JPM156N",  # Long-Term Government Bond Yields: 10-year: Main (Including Benchmark) for Japan
            }
        }
        
        # 政策金利: FRED APIから取得（最新値と時系列データ）
        policy_rate = None
        policy_rate_series = None
        if country_code == "US":
            if not self.fred_client:
                logger.error(f"FRED APIクライアントが初期化されていません。政策金利を取得できません ({country_code})")
            else:
                policy_rate = self._get_fred_data(fred_series["US"]["policy_rate"], country_code)
                if policy_rate is not None:
                    logger.info(f"政策金利取得成功 ({country_code}): {policy_rate:.2f}%")
                    # 時系列データも取得
                    policy_rate_series = self._get_fred_series_data(fred_series["US"]["policy_rate"], country_code)
                else:
                    logger.error(f"政策金利取得失敗 ({country_code})")
        elif country_code == "JP":
            # 日本: FRED APIから取得を試行（無担保コール翌日物金利の代替指標）
            if fred_series["JP"]["policy_rate"]:
                policy_rate = self._get_fred_data(fred_series["JP"]["policy_rate"], country_code)
                if policy_rate is not None:
                    policy_rate_series = self._get_fred_series_data(fred_series["JP"]["policy_rate"], country_code)
            
            # FRED APIが失敗した場合は別の方法を試行
            if policy_rate is None:
                policy_rate = self._get_japan_policy_rate()
        
        # 長期金利: FRED APIまたはyfinanceから取得（最新値と時系列データ）
        long_term_rate = None
        long_term_rate_series = None
        if country_code == "US":
            # FRED APIから取得
            long_term_rate = self._get_fred_data(fred_series["US"]["long_term_rate"], country_code)
            if long_term_rate is not None:
                # 時系列データも取得
                long_term_rate_series = self._get_fred_series_data(fred_series["US"]["long_term_rate"], country_code)
            # FRED APIが失敗した場合はyfinanceから取得（最新値のみ）
            if long_term_rate is None and yf:
                try:
                    rate_stock = yf.Ticker("^TNX")
                    hist = rate_stock.history(period="5d")
                    if not hist.empty:
                        long_term_rate = float(hist['Close'].iloc[-1])
                except Exception as e:
                    logger.warning(f"長期金利取得エラー (yfinance, {country_code}): {e}")
        elif country_code == "JP":
            # 日本: 日本銀行統計データAPIから取得を試行（公式データを優先）
            long_term_rate = self._get_japan_long_term_rate()
            
            # 日本銀行統計データAPIが失敗した場合はFRED APIをフォールバックとして使用
            if long_term_rate is None and fred_series["JP"]["long_term_rate"]:
                long_term_rate = self._get_fred_data(fred_series["JP"]["long_term_rate"], country_code)
                if long_term_rate is not None:
                    long_term_rate_series = self._get_fred_series_data(fred_series["JP"]["long_term_rate"], country_code)
        
        # クレジットスプレッド: インデックスデータから推測（実データ取得が困難なため）
        credit_spread = None
        if index_data:
            volatility = index_data.get("volatility", 0)
            if volatility > 0:
                base_spread = 1.5
                volatility_factor = (volatility - 15) / 10
                credit_spread = base_spread + volatility_factor
                credit_spread = max(0.5, min(5.0, credit_spread))
        
        result = {
            "country_code": country_code,
            "policy_rate": policy_rate,
            "long_term_rate": long_term_rate,
            "credit_spread": credit_spread,
            "policy_rate_series": policy_rate_series,  # 時系列データ
            "long_term_rate_series": long_term_rate_series,  # 時系列データ
            "date": datetime.now().isoformat()
        }
        # 返り値をログ出力（nullチェック）
        logger.info(f"get_financial_indicators返り値 ({country_code}): policy_rate={policy_rate}, long_term_rate={long_term_rate}, credit_spread={credit_spread}")
        if policy_rate is None:
            logger.warning(f"政策金利がnullです ({country_code})")
        if long_term_rate is None:
            logger.warning(f"長期金利がnullです ({country_code})")
        if policy_rate_series:
            logger.info(f"政策金利時系列データ取得成功 ({country_code}): {len(policy_rate_series)}件")
        if long_term_rate_series:
            logger.info(f"長期金利時系列データ取得成功 ({country_code}): {len(long_term_rate_series)}件")
        return result
    
    def _get_japan_policy_rate(self) -> Optional[float]:
        """日本の政策金利を取得（日本銀行統計データAPI）"""
        try:
            # 日本銀行の無担保コール翌日物金利（政策金利）を取得
            # FRED APIには直接的なシリーズがないため、日本銀行統計データAPIから取得
            
            # 簡易実装: 日本銀行統計データ検索サイトから取得
            # 実際の実装では、日本銀行統計データAPIまたはCSVダウンロードを使用
            # 現在は、FRED APIで短期金利を取得して推測
            
            # 代替方法: yfinanceで日本の短期債券から推測
            if yf:
                try:
                    # 日本短期債券ETFから推測（簡易的）
                    # より正確な実装には、日本銀行統計データAPIの実装が必要
                    pass
                except Exception as e:
                    logger.warning(f"日本の政策金利取得エラー (yfinance): {e}")
            
            logger.info("日本の政策金利データ取得を試行しました（実装要）")
        except Exception as e:
            logger.warning(f"日本の政策金利取得エラー: {e}")
        
        return None
    
    def _get_japan_long_term_rate(self) -> Optional[float]:
        """日本の長期金利を取得（日本銀行統計データ）"""
        try:
            # 日本10年債利回りを取得
            # 日本銀行統計データ検索サイトからCSVをダウンロード（認証不要）
            url = "https://www.stat-search.boj.or.jp/ssi/mtshtml/csv/m_ir_m_1.csv"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                # CSVをパースして最新の長期金利データを取得
                import csv
                import io
                csv_data = response.text
                reader = csv.reader(io.StringIO(csv_data))
                # CSVの構造に応じてパース（実装要）
                # 簡易実装: 詳細なパースは後で実装
                logger.info("日本銀行統計データから長期金利データを取得しました（パース実装要）")
                # TODO: 実際の長期金利データをパースして返す
        except Exception as e:
            logger.warning(f"日本の長期金利取得エラー (日本銀行統計データ): {e}")
        
        return None
    
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
            
            # 移動平均の計算（20日、75日、200日）
            ma20 = float(hist['Close'].tail(20).mean()) if len(hist) >= 20 else latest_price
            ma75 = float(hist['Close'].tail(75).mean()) if len(hist) >= 75 else latest_price
            ma200 = float(hist['Close'].tail(200).mean()) if len(hist) >= 200 else latest_price
            
            # 出来高データ
            avg_volume_30 = float(hist['Volume'].tail(30).mean()) if len(hist) >= 30 else 0
            latest_volume = float(hist['Volume'].iloc[-1])
            volume_trend = "増加" if latest_volume > avg_volume_30 * 1.2 else ("減少" if latest_volume < avg_volume_30 * 0.8 else "横ばい")
            
            # ファンダメンタル指標の取得
            revenue_growth = info.get("revenueGrowth")  # 売上成長率（年率）
            operating_margin = info.get("operatingMargins")  # 営業利益率
            roe = info.get("returnOnEquity")  # ROE
            market_cap = info.get("marketCap")
            
            # 時価総額区分
            market_cap_category = None
            if market_cap:
                if market_cap >= 10_000_000_000_000:  # 10兆円以上
                    market_cap_category = "超大規模"
                elif market_cap >= 1_000_000_000_000:  # 1兆円以上
                    market_cap_category = "大規模"
                elif market_cap >= 100_000_000_000:  # 1000億円以上
                    market_cap_category = "中規模"
                else:
                    market_cap_category = "小規模"
            
            data = {
                "ticker": ticker,
                "name": info.get("longName", ticker),
                "latest_price": latest_price,
                "ma20": ma20,
                "ma75": ma75,
                "ma200": ma200,
                "price_vs_ma20": (latest_price / ma20 - 1) * 100,
                "price_vs_ma75": (latest_price / ma75 - 1) * 100,
                "price_vs_ma200": (latest_price / ma200 - 1) * 100,
                "market_cap": market_cap,
                "market_cap_category": market_cap_category,
                "pe_ratio": info.get("trailingPE"),
                "revenue_growth": revenue_growth * 100 if revenue_growth else None,  # パーセンテージに変換
                "operating_margin": operating_margin * 100 if operating_margin else None,  # パーセンテージに変換
                "roe": roe * 100 if roe else None,  # パーセンテージに変換
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "business_summary": info.get("longBusinessSummary", "")[:200] if info.get("longBusinessSummary") else "",  # 事業概要（簡潔）
                "volume_trend": volume_trend,
                "volume_ratio": latest_volume / avg_volume_30 if avg_volume_30 > 0 else 1.0,
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
            
            # インデックスデータを先に取得（マクロ・金融指標の推測に使用）
            # 最大期間（10年=3650日）で取得し、html_generatorで期間フィルタリング
            indices_data = {}
            for index_code in country_config['indices']:
                index_data = self.get_index_data(index_code, country_code, days=3650)
                if index_data:
                    indices_data[index_code] = index_data
            
            # 最初のインデックスデータを使用してマクロ・金融指標を推測
            first_index = list(indices_data.values())[0] if indices_data else None
            
            country_data = {
                "name": country_name,
                "code": country_code,
                "indices": indices_data,
                "macro": self.get_macro_indicators(country_code, first_index),
                "financial": self.get_financial_indicators(country_code, first_index)
            }
            
            all_data["countries"][country_code] = country_data
        
        return all_data


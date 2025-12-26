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
                    # 【改善①】MA200計算用に最低200営業日以上のデータを取得
                    # 表示期間が6か月でも、MA計算用データは内部的に拡張して保持
                    # 1年分（約252営業日）を取得してMA200計算に使用
                    period = "1y"  # MA200計算用に最低1年分を取得
                    
                    hist = stock.history(period=period)
                    
                    if not hist.empty:
                        break
                    
                    # 空の場合はstart/endで再試行
                    if attempt < max_retries - 1:
                        end_date = datetime.now()
                        start_date = end_date - timedelta(days=min(days, 365))
                        hist = stock.history(start=start_date, end=end_date)
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
            
            # 最新価格と移動平均の計算（20日、75日、200日）
            latest_price = float(hist['Close'].iloc[-1])
            
            # 移動平均の計算
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
            
            # 【改善①】表示用データ（直近6か月分、約130営業日）とMA計算用データを分離
            # 表示期間は6か月だが、MA計算用データは全期間を使用
            display_days = min(130, len(hist))  # 6か月分（約130営業日）
            hist_display = hist.tail(display_days)
            
            # 表示用の価格データと日付
            historical_prices = hist_display['Close'].tolist()
            historical_dates = [date.strftime('%Y-%m-%d') for date in hist_display.index]
            
            # 【改善①】MAを時系列配列として計算（全期間のhistを使用して計算）
            # MA20, MA75, MA200の時系列データを生成
            ma20_series = hist['Close'].rolling(window=20, min_periods=1).mean().tail(display_days).tolist()
            ma75_series = hist['Close'].rolling(window=75, min_periods=1).mean().tail(display_days).tolist()
            ma200_series = hist['Close'].rolling(window=200, min_periods=1).mean().tail(display_days).tolist()
            
            # データ数が不足している場合は、最新値で埋める
            if len(ma20_series) < len(historical_prices):
                ma20_series = [ma20] * (len(historical_prices) - len(ma20_series)) + ma20_series
            if len(ma75_series) < len(historical_prices):
                ma75_series = [ma75] * (len(historical_prices) - len(ma75_series)) + ma75_series
            if len(ma200_series) < len(historical_prices):
                ma200_series = [ma200] * (len(historical_prices) - len(ma200_series)) + ma200_series
            
            # 【改善】トップ10銘柄集中度を時価総額ベースで計算（米国・日本共通）
            # 集中度 = (上位10銘柄の時価総額合計) ÷ (指数全体の時価総額) × 100（%）
            concentration = None
            composition_ratios = None
            
            # 米国（S&P500）または日本（TOPIX/日経平均）の場合、実際の時価総額データから構成比を計算
            if (index_code == "SPX" and country_code == "US") or (country_code == "JP" and (index_code == "TPX" or index_code == "N225")):
                top10_composition = self._calculate_top10_concentration(index_code, country_code)
                if top10_composition:
                    composition_ratios = top10_composition["ratios"]
                    concentration = top10_composition["top10_ratio"]
            
            # データ取得に失敗した場合は簡易計算を使用（後方互換性）
            if concentration is None:
                concentration = min(0.4, max(0.1, volatility / 100.0))  # 0.1～0.4の範囲に正規化（構造スコア計算用）
                # 簡易フォールバック：固定比率を使用
                composition_ratios = {
                    "その他": 1.0 - concentration
                }
            
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
                "historical_prices": historical_prices,  # 【改善①】直近6か月分の終値
                "historical_dates": historical_dates,  # 【改善①】直近6か月分の日付
                "historical_ma20": ma20_series,  # 【改善①】MA20の時系列配列
                "historical_ma75": ma75_series,  # 【改善①】MA75の時系列配列
                "historical_ma200": ma200_series,  # 【改善①】MA200の時系列配列
                "top_stocks_concentration": concentration,  # 構造スコア計算用の集中度（後方互換性）
                "top_stocks_composition": composition_ratios  # 【改善】トップ10銘柄構成比（時価総額ベース、指数全体に対する比率）
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
    
    def _get_fred_series_data(self, series_id: str, country_code: str, days: int = 730, max_retries: int = 3, is_daily: bool = False) -> Optional[Dict]:
        """
        FRED APIから時系列データを取得（リトライ付き）
        
        Args:
            series_id: FREDシリーズID
            country_code: 国コード
            days: 取得日数（日次データの場合は営業日数、月次データの場合は月数）
            max_retries: 最大リトライ回数
            is_daily: Trueの場合は日次データ、Falseの場合は月次データとして扱う
        
        Returns:
            {"dates": List[str], "values": List[float], "latest": float} またはNone
        """
        if not self.fred_client:
            logger.warning(f"FRED APIクライアントが初期化されていません ({series_id}, {country_code})")
            return None
        
        # データタイプに応じてlimitを計算
        if is_daily:
            # 日次データの場合（長期金利など）：営業日数ベースで約252日/年
            limit = min(365, days)  # 最大365日分
        else:
            # 月次データの場合（CPIなど）：約24ヶ月分を取得
            limit = min(36, days // 30) if days > 30 else 24  # 最大36ヶ月分
        
        for attempt in range(max_retries):
            try:
                # FRED APIから時系列データを取得
                data = self.fred_client.get_series(series_id, limit=limit)
                if not data.empty:
                    # 最新から指定期間分を取得
                    data_tail = data.tail(min(limit, len(data)))
                    dates = [date.strftime('%Y-%m-%d') for date in data_tail.index]
                    values = [float(val) for val in data_tail.values]
                    latest = float(data_tail.iloc[-1])
                    
                    logger.debug(f"FRED API時系列データ取得成功 ({series_id}, {country_code}): {len(values)}件")
                    return {
                        "dates": dates,
                        "values": values,
                        "latest": latest
                    }
                else:
                    logger.warning(f"FRED API時系列データが空です ({series_id}, {country_code}, 試行 {attempt + 1}/{max_retries})")
            except Exception as e:
                logger.warning(f"FRED API時系列データ取得エラー ({series_id}, {country_code}, 試行 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数バックオフ
        
        logger.error(f"FRED API時系列データ取得最終失敗 ({series_id}, {country_code})")
        return None
    
    def get_macro_indicators(self, country_code: str, index_data: Optional[Dict] = None) -> Dict:
        """
        マクロ経済指標を取得（実データ）
        
        Args:
            country_code: 国コード
            index_data: インデックスデータ（PMI推測に使用）
        
        Returns:
            マクロ指標の辞書
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
        
        # 【改善②】CPI: FRED APIから取得（最新値と時系列データ）
        cpi = None
        cpi_series = None  # CPIの時系列データ（前年比YoY）
        
        if country_code == "US":
            if not self.fred_client:
                logger.error(f"FRED APIクライアントが初期化されていません。CPIを取得できません ({country_code})")
            else:
                # CPIの時系列データを取得（過去1年～2年分、月次データ）
                cpi_raw_series = self._get_fred_series_data(fred_series["US"]["CPI"], country_code, days=730)
                if cpi_raw_series:
                    try:
                        # 前年比（YoY）を計算（各月について12ヶ月前との比較）
                        raw_values = cpi_raw_series["values"]
                        raw_dates = cpi_raw_series["dates"]
                        
                        # 前年比を計算（簡易実装：最新値と12ヶ月前の値を比較）
                        if len(raw_values) >= 13:
                            current = raw_values[-1]
                            previous = raw_values[-13] if len(raw_values) >= 13 else raw_values[0]
                            cpi = ((current / previous) - 1) * 100  # 年率換算（%）
                            
                            # 時系列データも生成（各月について前年比を計算）
                            cpi_yoy_values = []
                            cpi_yoy_dates = []
                            for i in range(len(raw_values)):
                                if i >= 12:
                                    # 12ヶ月前の値と比較
                                    yoy = ((raw_values[i] / raw_values[i-12]) - 1) * 100
                                    cpi_yoy_values.append(yoy)
                                    cpi_yoy_dates.append(raw_dates[i])
                            
                            cpi_series = {
                                "dates": cpi_yoy_dates,
                                "values": cpi_yoy_values,
                                "latest": cpi
                            }
                            
                            logger.info(f"CPI取得成功 ({country_code}): {cpi:.2f}%")
                        else:
                            logger.warning(f"CPIデータが不足しています ({country_code}): {len(raw_values)}件")
                    except Exception as e:
                        logger.error(f"CPI計算エラー ({country_code}): {e}")
                else:
                    logger.error(f"CPI取得失敗 ({country_code})")
        elif country_code == "JP":
            # 日本: e-Stat APIから取得を試行（公式データを優先）
            cpi = self._get_japan_cpi()
            
            # e-Stat APIが失敗した場合はFRED APIをフォールバックとして使用
            if cpi is None and fred_series["JP"]["CPI"]:
                cpi_raw_series = self._get_fred_series_data(fred_series["JP"]["CPI"], country_code, days=730)
                if cpi_raw_series:
                    try:
                        raw_values = cpi_raw_series["values"]
                        raw_dates = cpi_raw_series["dates"]
                        
                        if len(raw_values) >= 13:
                            current = raw_values[-1]
                            previous = raw_values[-13] if len(raw_values) >= 13 else raw_values[0]
                            cpi = ((current / previous) - 1) * 100  # 年率換算（%）
                            
                            # 時系列データも生成
                            cpi_yoy_values = []
                            cpi_yoy_dates = []
                            for i in range(len(raw_values)):
                                if i >= 12:
                                    yoy = ((raw_values[i] / raw_values[i-12]) - 1) * 100
                                    cpi_yoy_values.append(yoy)
                                    cpi_yoy_dates.append(raw_dates[i])
                            
                            cpi_series = {
                                "dates": cpi_yoy_dates,
                                "values": cpi_yoy_values,
                                "latest": cpi
                            }
                    except Exception as e:
                        logger.warning(f"日本のCPI計算エラー (FRED API): {e}")
        
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
            "employment_rate": employment_rate,
            "date": datetime.now().isoformat(),
            "cpi_series": cpi_series  # 【改善②】CPIの時系列データ（前年比YoY）
        }
        # 返り値をログ出力（nullチェック）
        logger.info(f"get_macro_indicators返り値 ({country_code}): PMI={pmi}, CPI={cpi}, employment_rate={employment_rate}")
        if cpi is None:
            logger.warning(f"CPIがnullです ({country_code})")
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
            金融指標の辞書
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
        
        # 政策金利: FRED APIから取得
        policy_rate = None
        if country_code == "US":
            if not self.fred_client:
                logger.error(f"FRED APIクライアントが初期化されていません。政策金利を取得できません ({country_code})")
            else:
                policy_rate = self._get_fred_data(fred_series["US"]["policy_rate"], country_code)
                if policy_rate is not None:
                    logger.info(f"政策金利取得成功 ({country_code}): {policy_rate:.2f}%")
                else:
                    logger.error(f"政策金利取得失敗 ({country_code})")
        elif country_code == "JP":
            # 日本: FRED APIから取得を試行（無担保コール翌日物金利の代替指標）
            if fred_series["JP"]["policy_rate"]:
                policy_rate = self._get_fred_data(fred_series["JP"]["policy_rate"], country_code)
            
            # FRED APIが失敗した場合は別の方法を試行
            if policy_rate is None:
                policy_rate = self._get_japan_policy_rate()
        
        # 【改善②】長期金利: FRED APIまたはyfinanceから取得（時系列データ含む）
        long_term_rate = None
        long_term_rate_series = None  # 時系列データ
        
        if country_code == "US":
            # FRED APIから時系列データを取得（過去6か月～1年、日次データ）
            if self.fred_client:
                long_term_rate_series = self._get_fred_series_data(fred_series["US"]["long_term_rate"], country_code, days=365, is_daily=True)
                if long_term_rate_series:
                    long_term_rate = long_term_rate_series["latest"]
            
            # FRED APIが失敗した場合はyfinanceから取得
            if long_term_rate is None and yf:
                try:
                    rate_stock = yf.Ticker("^TNX")
                    hist = rate_stock.history(period="6mo")
                    if not hist.empty:
                        long_term_rate = float(hist['Close'].iloc[-1])
                        # yfinanceから時系列データも取得
                        hist_tail = hist.tail(min(130, len(hist)))
                        long_term_rate_series = {
                            "dates": [date.strftime('%Y-%m-%d') for date in hist_tail.index],
                            "values": hist_tail['Close'].tolist(),
                            "latest": long_term_rate
                        }
                except Exception as e:
                    logger.warning(f"長期金利取得エラー (yfinance, {country_code}): {e}")
        elif country_code == "JP":
            # 日本: FRED APIから時系列データを取得（日次データ）
            if self.fred_client and fred_series["JP"]["long_term_rate"]:
                long_term_rate_series = self._get_fred_series_data(fred_series["JP"]["long_term_rate"], country_code, days=365, is_daily=True)
                if long_term_rate_series:
                    long_term_rate = long_term_rate_series["latest"]
            
            # FRED APIが失敗した場合は日本銀行統計データAPIから取得を試行
            if long_term_rate is None:
                long_term_rate = self._get_japan_long_term_rate()
        
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
            "date": datetime.now().isoformat(),
            "long_term_rate_series": long_term_rate_series  # 【改善②】長期金利の時系列データ
        }
        # 返り値をログ出力（nullチェック）
        logger.info(f"get_financial_indicators返り値 ({country_code}): policy_rate={policy_rate}, long_term_rate={long_term_rate}, credit_spread={credit_spread}")
        if policy_rate is None:
            logger.warning(f"政策金利がnullです ({country_code})")
        if long_term_rate is None:
            logger.warning(f"長期金利がnullです ({country_code})")
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
    
    def _calculate_top10_concentration(self, index_code: str, country_code: str) -> Optional[Dict]:
        """
        時価総額上位10銘柄の指数ベース構成比を計算（米国・日本共通）
        
        Args:
            index_code: インデックスコード（SPX, TPX, N225等）
            country_code: 国コード（US, JP）
        
        Returns:
            {"ratios": Dict, "top10_ratio": float, "top10_stocks": List[Dict]} またはNone
        """
        if not yf:
            logger.warning("yfinanceが利用できません。トップ10銘柄集中度を計算できません。")
            return None
        
        # 主要銘柄リスト（指数構成銘柄の代表的な銘柄）
        # 実際の実装では、指数の全構成銘柄リストから取得するのが理想だが、
        # ここでは主要銘柄から時価総額上位10銘柄を抽出
        if country_code == "US" and index_code == "SPX":
            # S&P500の主要構成銘柄（上位50銘柄程度を想定）
            major_stocks = [
                ("AAPL", "Apple"), ("MSFT", "Microsoft"), ("NVDA", "Nvidia"), ("AMZN", "Amazon"),
                ("META", "Meta"), ("GOOGL", "Alphabet"), ("GOOG", "Alphabet"), ("TSLA", "Tesla"),
                ("BRK-B", "Berkshire Hathaway"), ("V", "Visa"), ("JNJ", "Johnson & Johnson"),
                ("WMT", "Walmart"), ("JPM", "JPMorgan Chase"), ("MA", "Mastercard"), ("PG", "Procter & Gamble"),
                ("UNH", "UnitedHealth"), ("HD", "Home Depot"), ("DIS", "Disney"), ("BAC", "Bank of America"),
                ("ADBE", "Adobe"), ("NFLX", "Netflix"), ("AVGO", "Broadcom"), ("COST", "Costco"),
                ("CRM", "Salesforce"), ("PYPL", "PayPal"), ("ABBV", "AbbVie"), ("MRK", "Merck"),
                ("TMO", "Thermo Fisher"), ("CSCO", "Cisco"), ("ACN", "Accenture"), ("PEP", "PepsiCo"),
                ("NKE", "Nike"), ("TXN", "Texas Instruments"), ("ABT", "Abbott"), ("CVX", "Chevron"),
                ("LIN", "Linde"), ("NEE", "NextEra Energy"), ("ORCL", "Oracle"), ("AMD", "AMD"),
                ("HON", "Honeywell"), ("PM", "Philip Morris"), ("INTU", "Intuit"), ("UNP", "Union Pacific"),
                ("LOW", "Lowe's"), ("RTX", "Raytheon Technologies"), ("UPS", "UPS"), ("SPGI", "S&P Global"),
                ("QCOM", "Qualcomm"), ("DE", "Deere"), ("CAT", "Caterpillar"), ("MDT", "Medtronic"),
                ("GE", "GE"), ("BKNG", "Booking Holdings"), ("AXP", "American Express")
            ]
        elif country_code == "JP":
            # 日本株の主要銘柄（日経225/TOPIX主要構成銘柄）
            if index_code == "N225" or index_code == "TPX":
                major_stocks = [
                    ("7203.T", "トヨタ自動車"), ("6758.T", "ソニーグループ"), ("6861.T", "キーエンス"),
                    ("9984.T", "ソフトバンクグループ"), ("8035.T", "東京エレクトロン"), ("4063.T", "信越化学工業"),
                    ("6098.T", "リクルートホールディングス"), ("4519.T", "中外製薬"), ("6501.T", "日立製作所"),
                    ("8306.T", "三菱UFJフィナンシャル・グループ"), ("7267.T", "ホンダ"), ("8058.T", "三菱商事"),
                    ("6752.T", "パナソニック"), ("7733.T", "オリンパス"), ("4503.T", "アステラス製薬"),
                    ("4901.T", "富士フイルムホールディングス"), ("9434.T", "ソフトバンク"), ("6367.T", "ダイキン工業"),
                    ("4543.T", "テルモ"), ("7741.T", "HOYA"), ("9022.T", "東日本旅客鉄道"), ("8802.T", "三菱地所"),
                    ("2914.T", "日本たばこ産業"), ("8766.T", "東京海上ホールディングス"), ("8411.T", "みずほフィナンシャルグループ"),
                    ("4661.T", "オリエンタルランド"), ("3382.T", "セブン&アイ・ホールディングス"), ("6954.T", "ファナック"),
                    ("8001.T", "伊藤忠商事"), ("7974.T", "任天堂"), ("9433.T", "KDDI"), ("6971.T", "京セラ"),
                    ("9020.T", "東日本旅客鉄道"), ("7201.T", "日産自動車"), ("4502.T", "武田薬品工業"),
                    ("3405.T", "クラレ"), ("5201.T", "AGC"), ("6471.T", "日本精工"), ("4452.T", "花王"),
                    ("7743.T", "セイコーエプソン"), ("7732.T", "トプコン"), ("6902.T", "デンソー"),
                    ("5401.T", "日本製鉄"), ("3401.T", "帝人"), ("4061.T", "デンカ"), ("5411.T", "JFEホールディングス"),
                    ("5801.T", "古河電気工業"), ("5108.T", "ブリヂストン"), ("5713.T", "住友金属鉱山"),
                    ("5714.T", "DOWAホールディングス"), ("5233.T", "太平洋セメント"), ("3402.T", "東レ")
                ]
            else:
                logger.warning(f"未対応の指数コード: {index_code}")
                return None
        else:
            logger.warning(f"未対応の指数・国コード: {index_code}, {country_code}")
            return None
        
        try:
            # 各銘柄の時価総額を取得
            stock_market_caps = []
            alphabet_cap = None  # Alphabet（GOOGL + GOOG）の合算時価総額
            
            for ticker, name in major_stocks:
                # Alphabet（GOOGL + GOOG）を特別に処理
                if name == "Alphabet":
                    if ticker == "GOOGL":
                        try:
                            googl_stock = yf.Ticker("GOOGL")
                            googl_info = googl_stock.info
                            googl_cap = googl_info.get("marketCap")
                            
                            goog_stock = yf.Ticker("GOOG")
                            goog_info = goog_stock.info
                            goog_cap = goog_info.get("marketCap")
                            
                            if googl_cap and goog_cap:
                                alphabet_cap = googl_cap + goog_cap
                            elif googl_cap:
                                alphabet_cap = googl_cap
                            elif goog_cap:
                                alphabet_cap = goog_cap
                            
                            if alphabet_cap and alphabet_cap > 0:
                                stock_market_caps.append({
                                    "ticker": "GOOGL+GOOG",
                                    "name": "Alphabet",
                                    "market_cap": alphabet_cap
                                })
                        except Exception as e:
                            logger.debug(f"Alphabet ({ticker}) 時価総額取得エラー: {e}")
                    # GOOGはスキップ（GOOGLで既に処理済み）
                    continue
                
                try:
                    stock = yf.Ticker(ticker)
                    info = stock.info
                    market_cap = info.get("marketCap")
                    if market_cap and market_cap > 0:
                        stock_market_caps.append({
                            "ticker": ticker,
                            "name": name,
                            "market_cap": market_cap
                        })
                except Exception as e:
                    logger.debug(f"{name} ({ticker}) 時価総額取得エラー: {e}")
                    continue
            
            if len(stock_market_caps) < 10:
                logger.warning(f"時価総額データが10銘柄未満です（{len(stock_market_caps)}銘柄）。トップ10銘柄集中度を計算できません。")
                return None
            
            # 時価総額でソート（降順）
            stock_market_caps.sort(key=lambda x: x["market_cap"], reverse=True)
            
            # 上位10銘柄を抽出
            top10_stocks = stock_market_caps[:10]
            top10_total_market_cap = sum(stock["market_cap"] for stock in top10_stocks)
            
            # 指数全体の時価総額を推定
            # 上位50銘柄程度の時価総額合計から、指数全体を推定
            # 一般的に上位50銘柄で指数の約80-85%をカバーするため、その逆算で全体を推定
            top50_stocks = stock_market_caps[:min(50, len(stock_market_caps))]
            top50_total_market_cap = sum(stock["market_cap"] for stock in top50_stocks)
            
            # 上位50銘柄が指数全体の約82.5%を占めると仮定（80-85%の中間値）
            index_total_market_cap = top50_total_market_cap / 0.825
            
            # 構成比を計算
            composition_ratios = {}
            for stock in top10_stocks:
                ratio = stock["market_cap"] / index_total_market_cap
                composition_ratios[stock["name"]] = ratio
            
            # その他は残り
            top10_ratio = top10_total_market_cap / index_total_market_cap
            composition_ratios["その他"] = 1.0 - top10_ratio
            
            logger.info(f"トップ10銘柄集中度計算完了 ({country_code}, {index_code}): {top10_ratio*100:.2f}%")
            
            return {
                "ratios": composition_ratios,
                "top10_ratio": top10_ratio,
                "top10_stocks": [{"name": s["name"], "ticker": s["ticker"]} for s in top10_stocks]
            }
            
        except Exception as e:
            logger.error(f"トップ10銘柄集中度計算エラー ({country_code}, {index_code}): {e}")
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
            indices_data = {}
            for index_code in country_config['indices']:
                index_data = self.get_index_data(index_code, country_code)
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


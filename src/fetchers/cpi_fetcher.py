"""
CPI（消費者物価指数）データ取得
"""
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
from fredapi import Fred
import os
import requests
from dotenv import load_dotenv
from .base_fetcher import BaseFetcher

load_dotenv()


class CPIFetcher(BaseFetcher):
    """CPIデータを取得するクラス"""
    
    def __init__(self, market_code: str):
        """
        Args:
            market_code: 市場コード（"US" or "JP"）
        """
        super().__init__(market_code)
        
        if market_code == "US":
            # FRED APIキーの取得（環境変数から取得）
            api_key = os.getenv("FRED_API_KEY")
            if not api_key:
                raise RuntimeError("FRED_API_KEYが設定されていません（GitHub Secretsを確認してください）")
            self.fred = Fred(api_key=api_key)
            self.series_id = "CPIAUCSL"  # Consumer Price Index for All Urban Consumers: All Items
        elif market_code == "JP":
            # e-Stat APIキーの取得（環境変数から取得）
            self.estat_api_key = os.getenv("ESTAT_API_KEY")
            if not self.estat_api_key:
                raise RuntimeError("ESTAT_API_KEYが設定されていません（GitHub Secretsを確認してください）")
            # 消費者物価指数（全国・総合）の統計表ID
            # 2020年基準の消費者物価指数（全国・総合指数）の統計表ID
            # e-Statサイト: https://www.e-stat.go.jp/api/info-cat/news/cpi-info202107
            # 統計表ID: 0003427113（2020年基準）
            self.estat_stats_data_id = "0003427113"
        else:
            raise ValueError(f"サポートされていない市場コード: {market_code}")
    
    def _fetch_from_fred(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> pd.DataFrame:
        """
        FRED APIからCPIデータを取得
        
        Args:
            start_date: 開始日
            end_date: 終了日
        
        Returns:
            DataFrame: CPIデータ（CPI, CPI_YoY）
        """
        try:
            # FREDからデータ取得
            data = self.fred.get_series(self.series_id, start=start_date, end=end_date)
            
            if data.empty:
                return pd.DataFrame()
            
            # DataFrameに変換
            df = pd.DataFrame({
                'CPI': data
            })
            
            # 前年比（YoY）を計算
            df['CPI_YoY'] = df['CPI'].pct_change(periods=12, fill_method=None) * 100  # 12ヶ月前との比較
            
            # 日付をindexに設定
            if not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index)
            
            return df
            
        except Exception as e:
            print(f"FRED CPIデータ取得エラー: {e}")
            return pd.DataFrame()
    
    def _fetch_from_estat(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> pd.DataFrame:
        """
        e-Stat APIからCPIデータを取得
        
        Args:
            start_date: 開始日
            end_date: 終了日
        
        Returns:
            DataFrame: CPIデータ（CPI, CPI_YoY）
        """
        try:
            # APIキーは初期化時にチェック済みだが、念のため再確認
            if not self.estat_api_key:
                raise RuntimeError("ESTAT_API_KEYが設定されていません")
            
            # e-Stat APIのエンドポイント
            url = "https://api.e-stat.go.jp/rest/3.0/app/json/getStatsData"
            
            # パラメータ設定（API側でフィルタリング）
            params = {
                "appId": self.estat_api_key,
                "statsDataId": self.estat_stats_data_id,
                "lang": "J",
                "metaGetFlg": "N",
                "cntGetFlg": "N",
                "cdCat01": "0001",  # 総合
                "cdArea": "00000"    # 全国
            }
            
            # データ取得
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data_json = response.json()
            
            # データが取得できない場合
            if "GET_STATS_DATA" not in data_json or "STATISTICAL_DATA" not in data_json["GET_STATS_DATA"]:
                print("e-Stat APIからデータを取得できませんでした")
                return pd.DataFrame()
            
            # データをパース（e-Stat APIのレスポンス構造に応じて調整が必要）
            stats_data = data_json.get("GET_STATS_DATA", {}).get("STATISTICAL_DATA", {})
            
            # 統計表情報を確認（デバッグ用）
            table_inf = stats_data.get("TABLE_INF", {})
            stat_name = table_inf.get("STAT_NAME", {})
            if isinstance(stat_name, dict):
                stat_name_value = stat_name.get("$", "")
                if "国勢調査" in stat_name_value or "人口" in stat_name_value:
                    print(f"警告: 統計表ID {self.estat_stats_data_id} は国勢調査データです。正しいCPI統計表IDを設定してください。")
                    return pd.DataFrame()
            
            # データポイントを抽出
            data_points = []
            
            if "DATA_INF" in stats_data:
                data_inf = stats_data["DATA_INF"]
                # VALUEが配列の場合
                if isinstance(data_inf.get("VALUE"), list):
                    for value_info in data_inf["VALUE"]:
                        # 日付と値を取得
                        # 月次データの場合: @time は "YYYYMM" 形式
                        # 年次データの場合: @time は "YYYY000000" 形式
                        date_str = value_info.get("@time", "") or value_info.get("time", "")
                        value_str = value_info.get("@value", "") or value_info.get("value", "")
                        
                        if date_str and value_str:
                            try:
                                # 年次データ（YYYY000000形式）をスキップ
                                if len(date_str) == 10 and date_str.endswith("000000"):
                                    continue
                                
                                # 月次データ（YYYYMM形式）を処理
                                # API側でフィルタリング済みのため、すべてのデータを取得
                                if len(date_str) == 6:
                                    date = datetime.strptime(date_str, "%Y%m")
                                    value = float(value_str)
                                    data_points.append({"date": date, "CPI": value})
                            except (ValueError, TypeError) as e:
                                continue
                # VALUEが単一オブジェクトの場合
                elif isinstance(data_inf.get("VALUE"), dict):
                    value_info = data_inf["VALUE"]
                    date_str = value_info.get("@time", "") or value_info.get("time", "")
                    value_str = value_info.get("@value", "") or value_info.get("value", "")
                    
                    if date_str and value_str:
                        try:
                            # 年次データをスキップ
                            if len(date_str) == 10 and date_str.endswith("000000"):
                                pass
                            elif len(date_str) == 6:
                                date = datetime.strptime(date_str, "%Y%m")
                                value = float(value_str)
                                data_points.append({"date": date, "CPI": value})
                        except (ValueError, TypeError) as e:
                            pass
            
            # 別の構造パターン: VALUEが直接stats_dataに含まれる場合
            if not data_points and "VALUE" in stats_data:
                value_data = stats_data["VALUE"]
                if isinstance(value_data, list):
                    for value_info in value_data:
                        date_str = value_info.get("@time", "") or value_info.get("time", "")
                        value_str = value_info.get("@value", "") or value_info.get("value", "")
                        
                        if date_str and value_str:
                            try:
                                # 年次データをスキップ
                                if len(date_str) == 10 and date_str.endswith("000000"):
                                    continue
                                elif len(date_str) == 6:
                                    date = datetime.strptime(date_str, "%Y%m")
                                    value = float(value_str)
                                    data_points.append({"date": date, "CPI": value})
                            except (ValueError, TypeError) as e:
                                continue
            
            if not data_points:
                print("e-Stat APIから有効なCPIデータを取得できませんでした")
                print(f"デバッグ: 統計表名: {stat_name}")
                return pd.DataFrame()
            
            # DataFrameに変換
            df = pd.DataFrame(data_points)
            df.set_index("date", inplace=True)
            df.sort_index(inplace=True)
            
            # API側でフィルタリング済みのため、ローカル側でのフィルタリングは行わない
            # （start_date, end_dateは使用しない）
            
            if df.empty:
                return pd.DataFrame()
            
            # 前年比（YoY）を計算
            df['CPI_YoY'] = df['CPI'].pct_change(periods=12, fill_method=None) * 100  # 12ヶ月前との比較
            
            return df
            
        except requests.exceptions.RequestException as e:
            print(f"e-Stat APIリクエストエラー: {e}")
            return pd.DataFrame()
        except Exception as e:
            print(f"e-Stat CPIデータ取得エラー: {e}")
            return pd.DataFrame()
    
    def fetch(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> pd.DataFrame:
        """
        CPIデータを取得し、前年比（YoY）を計算
        
        Args:
            start_date: 開始日
            end_date: 終了日
        
        Returns:
            DataFrame: CPI前年比データ
                - index: 日付（月次）
                - columns: ['CPI', 'CPI_YoY']
        """
        try:
            # 市場コードに応じて取得元を切り替え
            if self.market_code == "US":
                df = self._fetch_from_fred(start_date, end_date)
            elif self.market_code == "JP":
                df = self._fetch_from_estat(start_date, end_date)
            else:
                print(f"サポートされていない市場コード: {self.market_code}")
                return pd.DataFrame()
            
            if df.empty:
                return pd.DataFrame()
            
            # 生データを保存
            self.save_raw_data(df, "cpi_yoy")
            
            return df
            
        except Exception as e:
            print(f"CPIデータ取得エラー ({self.market_code}): {e}")
            return pd.DataFrame()


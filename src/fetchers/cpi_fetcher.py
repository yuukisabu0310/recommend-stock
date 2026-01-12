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
            # 消費者物価指数（全国）の統計表ID
            # 統計表IDはe-Statサイトで「消費者物価指数」を検索して取得
            # 一般的な統計表ID:
            # - 0003410379: 消費者物価指数（全国・総合）
            # - 0003410380: 消費者物価指数（全国・総合・前年同月比）
            # 実際の統計表IDはe-Statサイトで確認してください
            # e-Statサイト: https://www.e-stat.go.jp/stat-search/files?page=1&toukei=00200573
            # 暫定的に一般的なIDを設定（実際のAPIレスポンスに合わせて調整が必要）
            # 注意: 実際のAPIレスポンス構造を確認し、パース処理を調整してください
            self.estat_stats_data_id = "0003410379"  # 消費者物価指数（全国・総合）
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
            
            # パラメータ設定
            params = {
                "appId": self.estat_api_key,
                "statsDataId": self.estat_stats_data_id,
                "lang": "J",
                "metaGetFlg": "N",
                "cntGetFlg": "N"
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
            
            # データポイントを抽出
            data_points = []
            
            # e-Stat APIのレスポンス構造は統計表によって異なるため、
            # 実際のレスポンス構造に合わせて調整が必要
            # 一般的な構造例:
            # - CLASS_INF: 分類情報
            # - DATA_INF: データ情報（VALUE配列）
            # デバッグ用: レスポンス構造を確認
            if not stats_data:
                print("デバッグ: e-Stat APIレスポンスが空です")
            else:
                print(f"デバッグ: e-Stat APIレスポンス構造のキー: {list(stats_data.keys())}")
            
            if "DATA_INF" in stats_data:
                data_inf = stats_data["DATA_INF"]
                # VALUEが配列の場合
                if isinstance(data_inf.get("VALUE"), list):
                    for value_info in data_inf["VALUE"]:
                        # 日付と値を取得（実際のJSON構造に応じて調整が必要）
                        # 例: {"@time": "202401", "@value": "105.5"}
                        date_str = value_info.get("@time", "") or value_info.get("time", "")
                        value_str = value_info.get("@value", "") or value_info.get("value", "")
                        
                        if date_str and value_str:
                            try:
                                # 日付をdatetimeに変換（YYYYMM形式）
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
                                date = datetime.strptime(date_str, "%Y%m")
                                value = float(value_str)
                                data_points.append({"date": date, "CPI": value})
                            except (ValueError, TypeError) as e:
                                continue
            
            if not data_points:
                print("e-Stat APIから有効なデータを取得できませんでした")
                print(f"デバッグ: レスポンス構造の詳細: {data_json}")
                return pd.DataFrame()
            
            # DataFrameに変換
            df = pd.DataFrame(data_points)
            df.set_index("date", inplace=True)
            df.sort_index(inplace=True)
            
            # 期間でフィルタリング
            if start_date:
                df = df[df.index >= start_date]
            if end_date:
                df = df[df.index <= end_date]
            
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


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
        e-Stat APIからCPIデータを取得（直近10年間の月次データのみ）
        """
        try:
            if not self.estat_api_key:
                raise RuntimeError("ESTAT_API_KEYが設定されていません")
            
            url = "https://api.e-stat.go.jp/rest/3.0/app/json/getStatsData"
            
            # statsDataId=0003427113 (2020年基準 消費者物価指数) の構造:
            # - cat01: 品目 (0001 = 総合)
            # - area: 地域 (00000 = 全国)
            # - cat02: 存在しないため指定してはいけない
            # - 時間指定（timeFrom / timeTo / cdTime）は使用不可
            # - 月次コードは YYYY00MM00 形式（例: 2020000100 → 2020年1月）
            # - sectionHeaderFlg を指定しないと VALUE 構造が不安定
            
            stats_id = "0003427113"
            cat01 = "0001"   # 総合
            area = "00000"   # 全国
            
            params = {
                "appId": self.estat_api_key,
                "lang": "J",
                "statsDataId": stats_id,
                "cdCat01": cat01,
                "cdArea": area,
                "metaGetFlg": "N",
                "cntGetFlg": "N",
                "sectionHeaderFlg": "1"   # ★必須
            }
            
            # データ取得
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data_json = response.json()
            
            get_stats_data = data_json.get("GET_STATS_DATA", {})
            if not get_stats_data:
                print(f"APIレスポンスエラー: {data_json}")  # エラー詳細を見るために出力変更
                return pd.DataFrame()

            statistical_data = get_stats_data.get("STATISTICAL_DATA", {})
            data_inf = statistical_data.get("DATA_INF", {})
            value_list = data_inf.get("VALUE")
            
            if not value_list:
                print(f"e-Stat CPI取得失敗: statsDataId={stats_id}, cat01={cat01}, area={area} (VALUEなし)")
                return pd.DataFrame()

            data_points = []
            
            # リストか辞書かで分岐する処理 (既存コードのロジックを使用)
            # 正規化してリストとして扱うとコードが短くなります
            if isinstance(value_list, dict):
                value_list = [value_list]
                
            for value_info in value_list:
                date_str = value_info.get("@time") or value_info.get("time")
                value_str = value_info.get("@value") or value_info.get("value") or value_info.get("$")
                
                if date_str and value_str:
                    try:
                        # e-Stat CPI の月次コード仕様: YYYY00MM00
                        # 例: 2020000100 → 2020年1月
                        # 月次判定条件: len == 10, [4:6] == "00", [8:10] == "00"
                        if len(date_str) == 10 and date_str[4:6] == "00" and date_str[8:10] == "00":
                            year = date_str[0:4]
                            month = date_str[6:8]
                            
                            # 年次・平均値の除外（month == "00"）
                            if month == "00":
                                continue
                            
                            # YYYYMM に変換して datetime に変換
                            date = datetime(int(year), int(month), 1)
                            value = float(value_str)
                            data_points.append({"date": date, "CPI": value})
                    except Exception:
                        continue

            if not data_points:
                print("有効なデータポイントが見つかりませんでした")
                return pd.DataFrame()

            df = pd.DataFrame(data_points)
            df.set_index("date", inplace=True)
            df.sort_index(inplace=True)
            
            # 成功判定条件（ログで確認）:
            # - 取得件数: 600件前後（全期間）
            # - 直近10年: 約120件
            # - 月次が連続している
            # - TradingView（ECONOMICS:JPCPI）と水準一致
            print(f"e-Stat CPI取得成功: 全期間{len(df)}件")
            
            # 直近10年フィルタ（Python側で実施）
            ten_years_ago = pd.Timestamp.today() - pd.DateOffset(years=10)
            df = df[df.index >= ten_years_ago]
            
            print(f"e-Stat CPI取得成功: 直近10年{len(df)}件")
            
            # YoY計算
            df['CPI_YoY'] = df['CPI'].pct_change(12) * 100
            
            return df

        except Exception as e:
            print(f"e-Stat CPIデータ取得エラー: {e}")
            return pd.DataFrame()
    
    def fetch(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> pd.DataFrame:
        """
        CPIデータを取得し、前年比（YoY）を計算
        
        Args:
            start_date: 開始日（USのみ有効、JPの場合は無視して直近10年を自動取得）
            end_date: 終了日（USのみ有効、JPの場合は無視して直近10年を自動取得）
        
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
                # JPの場合はstart_date/end_dateを無視し、API側で直近10年を自動計算
                df = self._fetch_from_estat(start_date=None, end_date=None)
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


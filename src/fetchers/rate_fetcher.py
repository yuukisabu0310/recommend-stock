"""
政策金利・長期金利データ取得
"""
import pandas as pd
from datetime import datetime
from typing import Optional
from fredapi import Fred
import os
from dotenv import load_dotenv
from .base_fetcher import BaseFetcher

load_dotenv()


class RateFetcher(BaseFetcher):
    """政策金利・長期金利データを取得するクラス"""
    
    def __init__(self, market_code: str, rate_type: str):
        """
        Args:
            market_code: 市場コード（"US" or "JP"）
            rate_type: "policy"（政策金利） or "long_10y"（長期金利10年）
        """
        super().__init__(market_code)
        self.rate_type = rate_type
        
        # FRED APIキーの取得（環境変数から取得）
        api_key = os.getenv("FRED_API_KEY")
        if not api_key:
            raise RuntimeError("FRED_API_KEYが設定されていません（GitHub Secretsを確認してください）")
        
        self.fred = Fred(api_key=api_key)
        
        # シリーズIDのマッピング
        self.series_ids = {
            "US": {
                "policy": "DFF",  # Federal Funds Effective Rate
                "long_10y": "DGS10"  # 10-Year Treasury Constant Maturity Rate
            },
            "JP": {
                "policy": "IRLTLT01JPM156N",  # Long-Term Government Bond Yields: 10-year
                "long_10y": "IRLTLT01JPM156N"  # 同じシリーズを使用
            }
        }
    
    def fetch(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> pd.DataFrame:
        """
        金利データを取得
        
        Args:
            start_date: 開始日
            end_date: 終了日
        
        Returns:
            DataFrame: 金利データ
                - index: 日付
                - columns: ['rate']
        """
        try:
            series_id = self.series_ids.get(self.market_code, {}).get(self.rate_type)
            if not series_id:
                print(f"シリーズIDが見つかりません: {self.market_code}, {self.rate_type}")
                return pd.DataFrame()
            
            # FREDからデータ取得
            data = self.fred.get_series(series_id, start=start_date, end=end_date)
            
            if data.empty:
                return pd.DataFrame()
            
            # DataFrameに変換
            column_name = "policy_rate" if self.rate_type == "policy" else "long_rate_10y"
            df = pd.DataFrame({
                column_name: data
            })
            
            # 日付をindexに設定
            if not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index)
            
            # 生データを保存
            filename = "policy_rate" if self.rate_type == "policy" else "long_rate_10y"
            self.save_raw_data(df, filename)
            
            return df
            
        except Exception as e:
            print(f"金利データ取得エラー ({self.market_code}, {self.rate_type}): {e}")
            return pd.DataFrame()


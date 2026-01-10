"""
CPI（消費者物価指数）データ取得
"""
import pandas as pd
from datetime import datetime
from typing import Optional
from fredapi import Fred
import os
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
        
        # FRED APIキーの取得（環境変数または直接指定）
        api_key = os.getenv("FRED_API_KEY", "812d0bbe6c3dbedf34d7ea5aa7f401fc")
        if not api_key:
            raise ValueError("FRED_API_KEY環境変数が設定されていません")
        
        self.fred = Fred(api_key=api_key)
        
        # シリーズIDのマッピング
        self.series_ids = {
            "US": "CPIAUCSL",  # Consumer Price Index for All Urban Consumers: All Items
            "JP": "JPNCPIALLMINMEI"  # Consumer Price Index: Total All Items for Japan
        }
    
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
            series_id = self.series_ids.get(self.market_code)
            if not series_id:
                print(f"シリーズIDが見つかりません: {self.market_code}")
                return pd.DataFrame()
            
            # FREDからデータ取得
            data = self.fred.get_series(series_id, start=start_date, end=end_date)
            
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
            
            # 生データを保存
            self.save_raw_data(df, "cpi_yoy")
            
            return df
            
        except Exception as e:
            print(f"CPIデータ取得エラー ({self.market_code}): {e}")
            return pd.DataFrame()


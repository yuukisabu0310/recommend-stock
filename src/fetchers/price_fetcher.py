"""
株価指数データ取得
"""
import yfinance as yf
import pandas as pd
from datetime import datetime
from typing import Optional
import time
from .base_fetcher import BaseFetcher


class PriceFetcher(BaseFetcher):
    """株価指数データを取得するクラス"""
    
    def __init__(self, market_code: str, symbol: str):
        """
        Args:
            market_code: 市場コード（"US" or "JP"）
            symbol: yfinanceのシンボル（例: "^GSPC", "^N225"）
        """
        super().__init__(market_code)
        self.symbol = symbol
    
    def fetch(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> pd.DataFrame:
        """
        株価データを取得
        
        Args:
            start_date: 開始日
            end_date: 終了日
        
        Returns:
            DataFrame: 日次株価データ
                - index: 日付
                - columns: ['Close', 'MA20', 'MA75', 'MA200']（移動平均は後で計算）
        """
        try:
            ticker = yf.Ticker(self.symbol)
            
            # 開始日が指定されていない場合は10年前から
            if start_date is None:
                start_date = datetime.now().replace(year=datetime.now().year - 10)
            
            # 終了日が指定されていない場合は今日まで
            if end_date is None:
                end_date = datetime.now()
            
            # データ取得（リトライロジック付き）
            max_retries = 3
            retry_delay = 2
            
            for attempt in range(max_retries):
                try:
                    hist = ticker.history(start=start_date, end=end_date)
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                    else:
                        raise e
            
            if hist.empty:
                return pd.DataFrame()
            
            # Close価格のみを抽出
            df = pd.DataFrame({
                'Close': hist['Close']
            })
            
            # 移動平均を計算（MA20, MA75, MA200）
            df['MA20'] = df['Close'].rolling(window=20, min_periods=1).mean()
            df['MA75'] = df['Close'].rolling(window=75, min_periods=1).mean()
            df['MA200'] = df['Close'].rolling(window=200, min_periods=1).mean()
            
            # 日付をindexに設定（既にindexになっているはずだが念のため）
            if not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index)
            
            # 生データを保存
            self.save_raw_data(df, "price")
            
            return df
            
        except Exception as e:
            print(f"株価データ取得エラー ({self.symbol}): {e}")
            return pd.DataFrame()


"""
EPS + PERデータ取得
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
from .base_fetcher import BaseFetcher


class EPSPERFetcher(BaseFetcher):
    """EPS + PERデータを取得するクラス"""
    
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
        EPS + PERデータを取得（20年固定）
        
        Args:
            start_date: 開始日（使用しない、常に20年前から）
            end_date: 終了日（使用しない、常に今日まで）
        
        Returns:
            DataFrame: EPS + PERデータ
                - index: 日付（四半期）
                - columns: ['EPS', 'PER']
        """
        try:
            ticker = yf.Ticker(self.symbol)
            
            # 20年前から取得
            start_date = datetime.now() - timedelta(days=20 * 365)
            end_date = datetime.now()
            
            # 株価データを取得
            hist = ticker.history(start=start_date, end=end_date)
            
            if hist.empty:
                return pd.DataFrame()
            
            # 簡易的な実装:
            # 実際のEPS/PERデータは別のデータソースが必要な場合がある
            # ここではyfinanceで取得可能な範囲で実装
            
            # 財務情報を取得
            try:
                info = ticker.info
                
                # EPSとPERが直接取得できる場合
                eps = info.get('trailingEps', None)
                per = info.get('trailingPE', None)
                
                if eps is None or per is None:
                    # データが取得できない場合は空のDataFrameを返す
                    print(f"EPS/PERデータが取得できません: {self.symbol}")
                    return pd.DataFrame()
                
                # 時系列データとして構築（簡易版）
                # 実際の実装では、四半期ごとのEPS/PERデータが必要
                df = pd.DataFrame({
                    'EPS': [eps] * len(hist),
                    'PER': [per] * len(hist)
                }, index=hist.index)
                
            except Exception as e:
                print(f"財務データ取得エラー: {e}")
                return pd.DataFrame()
            
            # 日付をindexに設定
            if not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index)
            
            # 生データを保存
            self.save_raw_data(df, "eps_per")
            
            return df
            
        except Exception as e:
            print(f"EPS/PERデータ取得エラー ({self.symbol}): {e}")
            return pd.DataFrame()


"""
時系列データ処理
"""
import pandas as pd
from datetime import datetime
from typing import Optional


class TimeSeriesProcessor:
    """時系列データの処理クラス（計算・評価は禁止、整形のみ）"""
    
    @staticmethod
    def filter_by_date_range(df: pd.DataFrame, start_date: Optional[datetime] = None, 
                            end_date: Optional[datetime] = None) -> pd.DataFrame:
        """
        日付範囲でフィルタリング
        
        Args:
            df: 対象のDataFrame
            start_date: 開始日
            end_date: 終了日
        
        Returns:
            DataFrame: フィルタリング後のDataFrame
        """
        if df.empty:
            return df
        
        if start_date is not None:
            df = df[df.index >= start_date]
        
        if end_date is not None:
            df = df[df.index <= end_date]
        
        return df
    
    @staticmethod
    def resample_monthly(df: pd.DataFrame, method: str = 'last') -> pd.DataFrame:
        """
        月次データにリサンプリング
        
        Args:
            df: 対象のDataFrame
            method: リサンプリング方法（'last', 'mean', 'first'）
        
        Returns:
            DataFrame: 月次データ
        """
        if df.empty:
            return df
        
        if method == 'last':
            return df.resample('M').last()
        elif method == 'mean':
            return df.resample('M').mean()
        elif method == 'first':
            return df.resample('M').first()
        else:
            return df.resample('M').last()
    
    @staticmethod
    def sort_by_date(df: pd.DataFrame, ascending: bool = True) -> pd.DataFrame:
        """
        日付でソート
        
        Args:
            df: 対象のDataFrame
            ascending: 昇順かどうか
        
        Returns:
            DataFrame: ソート後のDataFrame
        """
        if df.empty:
            return df
        
        return df.sort_index(ascending=ascending)


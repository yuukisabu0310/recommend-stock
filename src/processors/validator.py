"""
データ検証（欠損・異常値チェックのみ）
"""
import pandas as pd
import numpy as np
from typing import List, Tuple


class DataValidator:
    """データの妥当性をチェックするクラス（評価・判定は禁止、チェックのみ）"""
    
    @staticmethod
    def check_missing_values(df: pd.DataFrame) -> dict:
        """
        欠損値をチェック
        
        Args:
            df: 対象のDataFrame
        
        Returns:
            dict: 各カラムの欠損値数と割合
        """
        if df.empty:
            return {}
        
        missing_count = df.isnull().sum()
        missing_rate = (missing_count / len(df)) * 100
        
        result = {}
        for col in df.columns:
            result[col] = {
                'count': int(missing_count[col]),
                'rate': float(missing_rate[col])
            }
        
        return result
    
    @staticmethod
    def check_date_range(df: pd.DataFrame) -> Tuple[pd.Timestamp, pd.Timestamp]:
        """
        日付範囲を取得
        
        Args:
            df: 対象のDataFrame
        
        Returns:
            tuple: (開始日, 終了日)
        """
        if df.empty:
            return None, None
        
        return df.index.min(), df.index.max()
    
    @staticmethod
    def is_valid(df: pd.DataFrame) -> bool:
        """
        データが有効かどうかをチェック
        
        Args:
            df: 対象のDataFrame
        
        Returns:
            bool: データが有効な場合True
        """
        if df is None or df.empty:
            return False
        
        if len(df.columns) == 0:
            return False
        
        # すべての値が欠損値の場合は無効
        if df.isnull().all().all():
            return False
        
        return True


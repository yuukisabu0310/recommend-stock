"""
データリサンプリング処理
"""
import pandas as pd
from typing import Literal, Tuple


class Resampler:
    """データのリサンプリング処理クラス"""
    
    @staticmethod
    def resample(df: pd.DataFrame, freq: str, method: Literal['last', 'mean', 'first'] = 'last') -> pd.DataFrame:
        """
        データを指定頻度にリサンプリング
        
        Args:
            df: 対象のDataFrame
            freq: 頻度（'D': 日次, 'W': 週次, 'M': 月次, 'Q': 四半期, 'Y': 年次）
            method: リサンプリング方法
        
        Returns:
            DataFrame: リサンプリング後のDataFrame
        """
        if df.empty:
            return df
        
        if method == 'last':
            return df.resample(freq).last()
        elif method == 'mean':
            return df.resample(freq).mean()
        elif method == 'first':
            return df.resample(freq).first()
        else:
            return df.resample(freq).last()
    
    @staticmethod
    def align_frequencies(df1: pd.DataFrame, df2: pd.DataFrame, 
                         target_freq: str = 'D') -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        2つのDataFrameを同じ頻度に揃える
        
        Args:
            df1: 1つ目のDataFrame
            df2: 2つ目のDataFrame
            target_freq: 目標頻度
        
        Returns:
            tuple: (df1_resampled, df2_resampled)
        """
        if df1.empty or df2.empty:
            return df1, df2
        
        # 両方を同じ頻度にリサンプリング
        df1_resampled = Resampler.resample(df1, target_freq)
        df2_resampled = Resampler.resample(df2, target_freq)
        
        # インデックスを揃える（共通の日付範囲）
        common_index = df1_resampled.index.intersection(df2_resampled.index)
        df1_aligned = df1_resampled.loc[common_index]
        df2_aligned = df2_resampled.loc[common_index]
        
        return df1_aligned, df2_aligned


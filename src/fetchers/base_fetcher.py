"""
ベースフェッチャークラス
すべてのデータ取得クラスの基底クラス
"""
from abc import ABC, abstractmethod
from typing import Optional
import pandas as pd
from datetime import datetime, timedelta


class BaseFetcher(ABC):
    """データ取得の基底クラス"""
    
    def __init__(self, market_code: str):
        """
        Args:
            market_code: 市場コード（"US" or "JP"）
        """
        self.market_code = market_code
    
    @abstractmethod
    def fetch(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> pd.DataFrame:
        """
        データを取得する
        
        Args:
            start_date: 開始日（Noneの場合は可能な限り過去から）
            end_date: 終了日（Noneの場合は今日まで）
        
        Returns:
            DataFrame: 時系列データ（indexは日付、列は値）
        """
        pass
    
    def validate_data(self, df: pd.DataFrame) -> bool:
        """
        データの妥当性をチェック
        
        Args:
            df: チェック対象のDataFrame
        
        Returns:
            bool: データが有効な場合True
        """
        if df is None or df.empty:
            return False
        if len(df.columns) == 0:
            return False
        return True
    
    def save_raw_data(self, df: pd.DataFrame, filename: str):
        """
        生データをCSVとして保存
        
        Args:
            df: 保存するDataFrame
            filename: ファイル名（拡張子なし）
        """
        import os
        output_dir = f"data/raw/{self.market_code.lower()}"
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, f"{filename}.csv")
        df.to_csv(filepath, encoding='utf-8-sig')
    
    def get_years_ago_date(self, years: int) -> datetime:
        """
        指定年数前の日付を取得
        
        Args:
            years: 年数
        
        Returns:
            datetime: 指定年数前の日付
        """
        return datetime.now() - timedelta(days=years * 365)


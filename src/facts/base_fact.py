"""
ベースFactクラス
すべてのFactクラスの基底クラス
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Tuple
import pandas as pd
from datetime import datetime


class BaseFact(ABC):
    """Factの基底クラス"""
    
    def __init__(self, market_code: str):
        """
        Args:
            market_code: 市場コード（"US" or "JP"）
        """
        self.market_code = market_code
        self.data: Optional[pd.DataFrame] = None
        self.is_valid: bool = False
    
    @abstractmethod
    def load_data(self, df: pd.DataFrame) -> bool:
        """
        データを読み込んで構造化
        
        Args:
            df: 取得したデータ
        
        Returns:
            bool: データが有効な場合True
        """
        pass
    
    def get_latest_value(self, column: str) -> Optional[float]:
        """
        最新値を取得
        
        Args:
            column: カラム名
        
        Returns:
            float: 最新値（存在しない場合はNone）
        """
        if self.data is None or self.data.empty:
            return None
        
        if column not in self.data.columns:
            return None
        
        return float(self.data[column].iloc[-1])
    
    def get_date_range(self) -> Tuple[Optional[datetime], Optional[datetime]]:
        """
        データの日付範囲を取得
        
        Returns:
            tuple: (開始日, 終了日)
        """
        if self.data is None or self.data.empty:
            return None, None
        
        return self.data.index.min(), self.data.index.max()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Factを辞書形式に変換
        
        Returns:
            dict: Factの情報
        """
        start_date, end_date = self.get_date_range()
        
        return {
            'market_code': self.market_code,
            'is_valid': self.is_valid,
            'start_date': start_date.isoformat() if start_date else None,
            'end_date': end_date.isoformat() if end_date else None,
            'data_points': len(self.data) if self.data is not None else 0
        }


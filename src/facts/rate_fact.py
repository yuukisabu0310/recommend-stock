"""
政策金利・長期金利Fact
"""
from typing import Optional
import pandas as pd
from .base_fact import BaseFact
from src.processors.validator import DataValidator


class RateFact(BaseFact):
    """政策金利・長期金利のFactクラス"""
    
    def __init__(self, market_code: str, rate_type: str):
        """
        Args:
            market_code: 市場コード
            rate_type: "policy" or "long_10y"
        """
        super().__init__(market_code)
        self.rate_type = rate_type
    
    def load_data(self, df: pd.DataFrame) -> bool:
        """
        金利データを読み込んで構造化
        
        Args:
            df: 金利データ
        
        Returns:
            bool: データが有効な場合True
        """
        if df is None or df.empty:
            self.is_valid = False
            return False
        
        # データ検証
        validator = DataValidator()
        if not validator.is_valid(df):
            self.is_valid = False
            return False
        
        self.data = df.copy()
        self.is_valid = True
        
        return True
    
    def get_current_rate(self) -> Optional[float]:
        """現在の金利を取得"""
        column_name = "policy_rate" if self.rate_type == "policy" else "long_rate_10y"
        return self.get_latest_value(column_name)
    
    def to_dict(self) -> dict:
        """Factを辞書形式に変換"""
        base_dict = super().to_dict()
        base_dict.update({
            'rate_type': self.rate_type,
            'current_rate': self.get_current_rate()
        })
        return base_dict


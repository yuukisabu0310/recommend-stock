"""
CPI Fact
"""
from typing import Optional
import pandas as pd
from .base_fact import BaseFact
from src.processors.validator import DataValidator


class CPIFact(BaseFact):
    """CPIのFactクラス"""
    
    def load_data(self, df: pd.DataFrame) -> bool:
        """
        CPIデータを読み込んで構造化
        
        Args:
            df: CPIデータ（CPI, CPI_YoY）
        
        Returns:
            bool: データが有効な場合True
        """
        if df is None or df.empty:
            self.is_valid = False
            return False
        
        # 必須カラムのチェック
        required_columns = ['CPI_YoY']
        if not all(col in df.columns for col in required_columns):
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
    
    def get_current_cpi_yoy(self) -> Optional[float]:
        """現在のCPI前年比を取得"""
        return self.get_latest_value('CPI_YoY')
    
    def to_dict(self) -> dict:
        """Factを辞書形式に変換"""
        base_dict = super().to_dict()
        base_dict.update({
            'current_cpi_yoy': self.get_current_cpi_yoy()
        })
        return base_dict


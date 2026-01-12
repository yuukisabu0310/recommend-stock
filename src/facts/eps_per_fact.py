"""
EPS + PER Fact
"""
from typing import Optional
import pandas as pd
from .base_fact import BaseFact
from src.processors.validator import DataValidator


class EPSPERFact(BaseFact):
    """EPS + PERのFactクラス"""
    
    def load_data(self, df: pd.DataFrame) -> bool:
        """
        EPS + PERデータを読み込んで構造化
        
        Args:
            df: EPS + PERデータ（EPS, PER）
        
        Returns:
            bool: データが有効な場合True
        """
        if df is None or df.empty:
            self.is_valid = False
            return False
        
        # 必須カラムのチェック（USの場合はPERのみ、JPの場合はEPSとPER）
        # USの場合はEPSがNoneでもOK
        if 'PER' not in df.columns:
            self.is_valid = False
            return False
        # JPの場合はEPSも必要
        if 'EPS' not in df.columns:
            # USの場合、EPSがNoneでもOK
            pass
        
        # データ検証
        validator = DataValidator()
        if not validator.is_valid(df):
            self.is_valid = False
            return False
        
        self.data = df.copy()
        self.is_valid = True
        
        return True
    
    def get_current_eps(self) -> Optional[float]:
        """現在のEPSを取得"""
        return self.get_latest_value('EPS')
    
    def get_current_per(self) -> Optional[float]:
        """現在のPERを取得"""
        return self.get_latest_value('PER')
    
    def to_dict(self) -> dict:
        """Factを辞書形式に変換"""
        base_dict = super().to_dict()
        base_dict.update({
            'current_eps': self.get_current_eps(),
            'current_per': self.get_current_per()
        })
        return base_dict


"""
株価指数Fact
"""
from typing import Optional
import pandas as pd
from .base_fact import BaseFact
from src.processors.validator import DataValidator


class PriceFact(BaseFact):
    """株価指数のFactクラス"""
    
    def load_data(self, df: pd.DataFrame) -> bool:
        """
        株価データを読み込んで構造化
        
        Args:
            df: 株価データ（Close, MA20, MA75, MA200）
        
        Returns:
            bool: データが有効な場合True
        """
        if df is None or df.empty:
            self.is_valid = False
            return False
        
        # 必須カラムのチェック
        required_columns = ['Close']
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
    
    def get_current_price(self) -> Optional[float]:
        """現在の株価を取得"""
        return self.get_latest_value('Close')
    
    def get_ma20(self) -> Optional[float]:
        """20日移動平均を取得"""
        return self.get_latest_value('MA20')
    
    def get_ma75(self) -> Optional[float]:
        """75日移動平均を取得"""
        return self.get_latest_value('MA75')
    
    def get_ma200(self) -> Optional[float]:
        """200日移動平均を取得"""
        return self.get_latest_value('MA200')
    
    def to_dict(self) -> dict:
        """Factを辞書形式に変換"""
        base_dict = super().to_dict()
        base_dict.update({
            'current_price': self.get_current_price(),
            'ma20': self.get_ma20(),
            'ma75': self.get_ma75(),
            'ma200': self.get_ma200()
        })
        return base_dict


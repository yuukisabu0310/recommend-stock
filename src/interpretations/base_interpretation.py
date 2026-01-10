"""
ベースInterpretationクラス
すべてのInterpretationクラスの基底クラス
"""
from abc import ABC, abstractmethod
from typing import Optional
from src.facts.base_fact import BaseFact


class BaseInterpretation(ABC):
    """Interpretationの基底クラス（文章要約のみ、判断は禁止）"""
    
    def __init__(self, fact: BaseFact):
        """
        Args:
            fact: 対応するFactオブジェクト
        """
        self.fact = fact
    
    @abstractmethod
    def generate_summary(self) -> str:
        """
        Factを文章で要約（事実の説明のみ、判断は禁止）
        
        Returns:
            str: 要約文章
        """
        pass
    
    def is_data_available(self) -> bool:
        """データが利用可能かどうか"""
        return self.fact.is_valid if self.fact else False


"""
EPS + PER Interpretation
"""
from src.interpretations.base_interpretation import BaseInterpretation
from src.facts.eps_per_fact import EPSPERFact
from datetime import datetime


class EPSPERInterpretation(BaseInterpretation):
    """EPS + PERのInterpretationクラス"""
    
    def generate_summary(self) -> str:
        """
        EPS + PERの状態を文章で要約
        
        Returns:
            str: 要約文章
        """
        if not self.is_data_available():
            return "EPS/PERデータは現在取得できません。"
        
        fact: EPSPERFact = self.fact
        current_eps = fact.get_current_eps()
        current_per = fact.get_current_per()
        start_date, end_date = fact.get_date_range()
        
        summary_parts = []
        
        # 現在のEPS
        if current_eps is not None:
            summary_parts.append(f"現在のEPSは{current_eps:.2f}です。")
        
        # 現在のPER
        if current_per is not None:
            summary_parts.append(f"現在のPERは{current_per:.2f}です。")
        
        # データ期間
        if start_date and end_date:
            summary_parts.append(f"データ期間は{start_date.strftime('%Y年%m月%d日')}から{end_date.strftime('%Y年%m月%d日')}までです。")
        
        if not summary_parts:
            return "EPS/PERデータの要約を生成できませんでした。"
        
        return " ".join(summary_parts)


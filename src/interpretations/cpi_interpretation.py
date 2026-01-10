"""
CPI Interpretation
"""
from src.interpretations.base_interpretation import BaseInterpretation
from src.facts.cpi_fact import CPIFact
from datetime import datetime


class CPIIntepretation(BaseInterpretation):
    """CPIのInterpretationクラス"""
    
    def generate_summary(self) -> str:
        """
        CPIの状態を文章で要約
        
        Returns:
            str: 要約文章
        """
        if not self.is_data_available():
            return "CPIデータは現在取得できません。"
        
        fact: CPIFact = self.fact
        current_cpi_yoy = fact.get_current_cpi_yoy()
        start_date, end_date = fact.get_date_range()
        
        summary_parts = []
        
        # 現在のCPI前年比
        if current_cpi_yoy is not None:
            summary_parts.append(f"現在のCPI前年比は{current_cpi_yoy:.2f}%です。")
        
        # データ期間
        if start_date and end_date:
            summary_parts.append(f"データ期間は{start_date.strftime('%Y年%m月%d日')}から{end_date.strftime('%Y年%m月%d日')}までです。")
        
        if not summary_parts:
            return "CPIデータの要約を生成できませんでした。"
        
        return " ".join(summary_parts)


"""
政策金利・長期金利Interpretation
"""
from src.interpretations.base_interpretation import BaseInterpretation
from src.facts.rate_fact import RateFact
from datetime import datetime


class RateInterpretation(BaseInterpretation):
    """政策金利・長期金利のInterpretationクラス"""
    
    def generate_summary(self) -> str:
        """
        金利の状態を文章で要約
        
        Returns:
            str: 要約文章
        """
        if not self.is_data_available():
            rate_type_name = "政策金利" if self.fact.rate_type == "policy" else "長期金利"
            return f"{rate_type_name}データは現在取得できません。"
        
        fact: RateFact = self.fact
        current_rate = fact.get_current_rate()
        start_date, end_date = fact.get_date_range()
        
        rate_type_name = "政策金利" if fact.rate_type == "policy" else "長期金利（10年）"
        
        summary_parts = []
        
        # 現在の金利
        if current_rate is not None:
            summary_parts.append(f"現在の{rate_type_name}は{current_rate:.2f}%です。")
        
        # データ期間
        if start_date and end_date:
            summary_parts.append(f"データ期間は{start_date.strftime('%Y年%m月%d日')}から{end_date.strftime('%Y年%m月%d日')}までです。")
        
        if not summary_parts:
            return f"{rate_type_name}データの要約を生成できませんでした。"
        
        return " ".join(summary_parts)


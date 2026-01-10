"""
株価指数Interpretation
"""
from src.interpretations.base_interpretation import BaseInterpretation
from src.facts.price_fact import PriceFact
from datetime import datetime


class PriceInterpretation(BaseInterpretation):
    """株価指数のInterpretationクラス"""
    
    def generate_summary(self) -> str:
        """
        株価指数の状態を文章で要約
        
        Returns:
            str: 要約文章
        """
        if not self.is_data_available():
            return "株価データは現在取得できません。"
        
        fact: PriceFact = self.fact
        current_price = fact.get_current_price()
        ma20 = fact.get_ma20()
        ma75 = fact.get_ma75()
        ma200 = fact.get_ma200()
        
        start_date, end_date = fact.get_date_range()
        
        summary_parts = []
        
        # 現在の株価
        if current_price is not None:
            summary_parts.append(f"現在の株価は{current_price:,.0f}です。")
        
        # 移動平均との関係（事実のみ）
        if current_price is not None and ma20 is not None:
            if current_price > ma20:
                summary_parts.append("株価は20日移動平均を上回っています。")
            elif current_price < ma20:
                summary_parts.append("株価は20日移動平均を下回っています。")
            else:
                summary_parts.append("株価は20日移動平均とほぼ同水準です。")
        
        if ma20 is not None and ma75 is not None:
            if ma20 > ma75:
                summary_parts.append("20日移動平均は75日移動平均を上回っています。")
            elif ma20 < ma75:
                summary_parts.append("20日移動平均は75日移動平均を下回っています。")
        
        if ma75 is not None and ma200 is not None:
            if ma75 > ma200:
                summary_parts.append("75日移動平均は200日移動平均を上回っています。")
            elif ma75 < ma200:
                summary_parts.append("75日移動平均は200日移動平均を下回っています。")
        
        # データ期間
        if start_date and end_date:
            summary_parts.append(f"データ期間は{start_date.strftime('%Y年%m月%d日')}から{end_date.strftime('%Y年%m月%d日')}までです。")
        
        if not summary_parts:
            return "株価データの要約を生成できませんでした。"
        
        return " ".join(summary_parts)


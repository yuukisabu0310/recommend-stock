"""
セクション生成
"""
from typing import Dict, Any, Optional


class SectionRenderer:
    """セクションをレンダリングするクラス"""
    
    @staticmethod
    def render_price_section(page_data: Dict[str, Any], is_details: bool = False) -> str:
        """株価指数セクションをレンダリング"""
        chart_html = page_data.get("charts", {}).get("price", "<p>この指標は現在データを取得できません</p>")
        interpretation = page_data.get("interpretations", {}).get("price", "データが取得できません。")
        
        # 経済指標方向矢印を追加
        price_data = page_data.get("facts", {}).get("price")
        arrow_html = ""
        if price_data and price_data.get("is_valid"):
            arrow_html = SectionRenderer._get_direction_arrow(price_data, "Close")
        
        years = page_data.get("years", 1)
        switchable_years = page_data.get("switchable_years", [])
        period_selector = ""
        
        if switchable_years:
            from .layout import Layout
            period_selector = Layout.get_period_selector(years, switchable_years, "price-chart")
        
        from .layout import Layout
        title = f"① 株価指数チャート{arrow_html}"
        section_html = Layout.get_section(
            title,
            chart_html,
            interpretation,
            period_selector,
            is_details
        )
        # セクション1にクラスを追加
        return section_html.replace('<div class="section">', '<div class="section section-1">')
    
    @staticmethod
    def render_rate_section(page_data: Dict[str, Any], is_details: bool = False) -> str:
        """政策金利・長期金利セクションをレンダリング"""
        chart_html = page_data.get("charts", {}).get("rate", "<p>この指標は現在データを取得できません</p>")
        interpretation = page_data.get("interpretations", {}).get("rate", "データが取得できません。")
        
        # 経済指標方向矢印を追加（政策金利と長期金利の両方）
        policy_data = page_data.get("facts", {}).get("policy_rate")
        long_rate_data = page_data.get("facts", {}).get("long_rate")
        
        arrows = []
        if policy_data and policy_data.get("is_valid"):
            arrow = SectionRenderer._get_direction_arrow(policy_data, "policy_rate")
            arrows.append(f"政策金利{arrow}")
        if long_rate_data and long_rate_data.get("is_valid"):
            arrow = SectionRenderer._get_direction_arrow(long_rate_data, "long_rate_10y")
            arrows.append(f"長期金利{arrow}")
        
        title = "② 政策金利 + 長期金利（10年）"
        if arrows:
            title = f"② 政策金利 + 長期金利（10年） - {' / '.join(arrows)}"
        
        years = page_data.get("years", 1)
        switchable_years = page_data.get("switchable_years", [])
        period_selector = ""
        
        if switchable_years:
            from .layout import Layout
            period_selector = Layout.get_period_selector(years, switchable_years, "rate-chart")
        
        from .layout import Layout
        section_html = Layout.get_section(
            title,
            chart_html,
            interpretation,
            period_selector,
            is_details
        )
        # セクション2にクラスを追加
        return section_html.replace('<div class="section">', '<div class="section section-2">')
    
    @staticmethod
    def render_cpi_section(page_data: Dict[str, Any], is_details: bool = False) -> str:
        """CPIセクションをレンダリング"""
        chart_html = page_data.get("charts", {}).get("cpi", "<p>この指標は現在データを取得できません</p>")
        interpretation = page_data.get("interpretations", {}).get("cpi", "データが取得できません。")
        
        # 経済指標方向矢印を追加
        cpi_data = page_data.get("facts", {}).get("cpi")
        arrow_html = ""
        if cpi_data and cpi_data.get("is_valid"):
            arrow_html = SectionRenderer._get_direction_arrow(cpi_data, "CPI_YoY")
        
        years = page_data.get("years", 1)
        switchable_years = page_data.get("switchable_years", [])
        period_selector = ""
        
        if switchable_years:
            from .layout import Layout
            period_selector = Layout.get_period_selector(years, switchable_years, "cpi-chart")
        
        from .layout import Layout
        title = f"③ CPI（消費者物価指数）前年比{arrow_html}"
        section_html = Layout.get_section(
            title,
            chart_html,
            interpretation,
            period_selector,
            is_details
        )
        # セクション3にクラスを追加
        return section_html.replace('<div class="section">', '<div class="section section-3">')
    
    @staticmethod
    def render_eps_per_section(page_data: Dict[str, Any], is_details: bool = False) -> str:
        """EPS + PERセクションをレンダリング"""
        chart_html = page_data.get("charts", {}).get("eps_per", "<p>この指標は現在データを取得できません</p>")
        interpretation = page_data.get("interpretations", {}).get("eps_per", "データが取得できません。")
        
        from .layout import Layout
        section_html = Layout.get_section(
            "④ EPS + PER（20年固定）",
            chart_html,
            interpretation,
            "",
            is_details
        )
        # セクション4にクラスを追加（全幅表示用）
        return section_html.replace('<div class="section">', '<div class="section section-4">')
    
    @staticmethod
    def _get_direction_arrow(fact_data: Dict[str, Any], column_name: str) -> str:
        """
        経済指標の方向矢印を生成（直近値 - 前回値の符号のみで判定）
        
        Args:
            fact_data: Factデータ（dataフィールドにDataFrameを含む）
            column_name: カラム名
        
        Returns:
            str: 矢印HTML
        """
        import pandas as pd
        
        if not fact_data or not fact_data.get("is_valid"):
            return ""
        
        data = fact_data.get("data")
        if data is None or data.empty or column_name not in data.columns:
            return ""
        
        # 直近値と前回値を取得
        values = data[column_name].dropna()
        if len(values) < 2:
            return ""
        
        current_value = float(values.iloc[-1])
        previous_value = float(values.iloc[-2])
        
        # 符号のみで判定（しきい値・評価ロジックは禁止）
        diff = current_value - previous_value
        
        if diff > 0:
            return '<span class="econ-arrow up">▲</span>'
        elif diff < 0:
            return '<span class="econ-arrow down">▼</span>'
        else:
            return '<span class="econ-arrow flat">■</span>'


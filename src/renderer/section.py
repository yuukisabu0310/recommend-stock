"""
セクション生成
"""
from typing import Dict, Any


class SectionRenderer:
    """セクションをレンダリングするクラス"""
    
    @staticmethod
    def render_price_section(page_data: Dict[str, Any], is_details: bool = False) -> str:
        """株価指数セクションをレンダリング"""
        chart_html = page_data.get("charts", {}).get("price", "<p>この指標は現在データを取得できません</p>")
        interpretation = page_data.get("interpretations", {}).get("price", "データが取得できません。")
        
        years = page_data.get("years", 1)
        switchable_years = page_data.get("switchable_years", [])
        period_selector = ""
        
        if switchable_years:
            from .layout import Layout
            period_selector = Layout.get_period_selector(years, switchable_years, "price-chart")
        
        from .layout import Layout
        return Layout.get_section(
            "① 株価指数チャート",
            chart_html,
            interpretation,
            period_selector,
            is_details
        )
    
    @staticmethod
    def render_rate_section(page_data: Dict[str, Any], is_details: bool = False) -> str:
        """政策金利・長期金利セクションをレンダリング"""
        chart_html = page_data.get("charts", {}).get("rate", "<p>この指標は現在データを取得できません</p>")
        interpretation = page_data.get("interpretations", {}).get("rate", "データが取得できません。")
        
        years = page_data.get("years", 1)
        switchable_years = page_data.get("switchable_years", [])
        period_selector = ""
        
        if switchable_years:
            from .layout import Layout
            period_selector = Layout.get_period_selector(years, switchable_years, "rate-chart")
        
        from .layout import Layout
        return Layout.get_section(
            "② 政策金利 + 長期金利（10年）",
            chart_html,
            interpretation,
            period_selector,
            is_details
        )
    
    @staticmethod
    def render_cpi_section(page_data: Dict[str, Any], is_details: bool = False) -> str:
        """CPIセクションをレンダリング"""
        chart_html = page_data.get("charts", {}).get("cpi", "<p>この指標は現在データを取得できません</p>")
        interpretation = page_data.get("interpretations", {}).get("cpi", "データが取得できません。")
        
        years = page_data.get("years", 1)
        switchable_years = page_data.get("switchable_years", [])
        period_selector = ""
        
        if switchable_years:
            from .layout import Layout
            period_selector = Layout.get_period_selector(years, switchable_years, "cpi-chart")
        
        from .layout import Layout
        return Layout.get_section(
            "③ CPI（消費者物価指数）前年比",
            chart_html,
            interpretation,
            period_selector,
            is_details
        )
    
    @staticmethod
    def render_eps_per_section(page_data: Dict[str, Any], is_details: bool = False) -> str:
        """EPS + PERセクションをレンダリング"""
        chart_html = page_data.get("charts", {}).get("eps_per", "<p>この指標は現在データを取得できません</p>")
        interpretation = page_data.get("interpretations", {}).get("eps_per", "データが取得できません。")
        
        from .layout import Layout
        return Layout.get_section(
            "④ EPS + PER（20年固定）",
            chart_html,
            interpretation,
            "",
            is_details
        )


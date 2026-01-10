"""
セクション生成
"""
from typing import Dict, Any, Optional


class SectionRenderer:
    """セクションをレンダリングするクラス"""
    
    @staticmethod
    def render_price_section(page_data: Dict[str, Any]) -> str:
        """株価指数セクションをレンダリング"""
        chart_html = page_data.get("charts", {}).get("price", "<p>この指標は現在データを取得できません</p>")
        interpretation = page_data.get("interpretations", {}).get("price", "データが取得できません。")
        
        # Factを箇条書きに変換
        interpretation = SectionRenderer._format_fact_list(interpretation)
        
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
            period_selector
        )
        # block-1クラスを追加（全幅表示）
        return section_html.replace('<section class="card">', '<section class="card block-1">')
    
    @staticmethod
    def render_rate_section(page_data: Dict[str, Any]) -> str:
        """政策金利・長期金利セクションをレンダリング"""
        chart_html = page_data.get("charts", {}).get("rate", "<p>この指標は現在データを取得できません</p>")
        interpretation = page_data.get("interpretations", {}).get("rate", "データが取得できません。")
        
        # Factを箇条書きに変換
        interpretation = SectionRenderer._format_fact_list(interpretation)
        
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
            period_selector
        )
        # block-2クラスを追加
        return section_html.replace('<section class="card">', '<section class="card block-2">')
    
    @staticmethod
    def render_cpi_section(page_data: Dict[str, Any]) -> str:
        """CPIセクションをレンダリング"""
        chart_html = page_data.get("charts", {}).get("cpi", "<p>この指標は現在データを取得できません</p>")
        interpretation = page_data.get("interpretations", {}).get("cpi", "データが取得できません。")
        
        # Factを箇条書きに変換
        interpretation = SectionRenderer._format_fact_list(interpretation)
        
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
            period_selector
        )
        # block-3クラスを追加
        return section_html.replace('<section class="card">', '<section class="card block-3">')
    
    @staticmethod
    def render_eps_per_section(page_data: Dict[str, Any]) -> str:
        """EPS + PERセクションをレンダリング"""
        chart_html = page_data.get("charts", {}).get("eps_per", "<p>この指標は現在データを取得できません</p>")
        interpretation = page_data.get("interpretations", {}).get("eps_per", "データが取得できません。")
        
        # Factを箇条書きに変換
        interpretation = SectionRenderer._format_fact_list(interpretation)
        
        from .layout import Layout
        section_html = Layout.get_section(
            "④ EPS + PER（20年固定）",
            chart_html,
            interpretation,
            ""
        )
        # block-4クラスを追加
        return section_html.replace('<section class="card">', '<section class="card block-4">')
    
    @staticmethod
    def _format_fact_list(text: str) -> str:
        """
        Fact文章を箇条書き形式に変換
        
        Args:
            text: Fact文章
        
        Returns:
            str: 箇条書きHTML
        """
        if not text or text.strip() == "" or text == "データが取得できません。":
            return text
        
        # 文章を文単位で分割（句点で区切る）
        sentences = [s.strip() for s in text.split('。') if s.strip()]
        
        if not sentences:
            return text
        
        # 最後の文が空でない場合は句点を追加
        formatted_sentences = []
        for i, sentence in enumerate(sentences):
            if i < len(sentences) - 1:
                formatted_sentences.append(sentence + '。')
            else:
                # 最後の文は句点があればそのまま、なければ追加
                if not sentence.endswith('。'):
                    formatted_sentences.append(sentence + '。')
                else:
                    formatted_sentences.append(sentence)
        
        # 箇条書きHTMLに変換
        list_items = "\n".join([f"<li>{s}</li>" for s in formatted_sentences])
        return f'<ul class="fact-list">\n{list_items}\n</ul>'
    
    @staticmethod
    def render_fact_section(page_data: Dict[str, Any]) -> str:
        """① 観測事実セクションをレンダリング"""
        from .layout import Layout
        
        # すべてのFactを収集して箇条書きに変換
        facts = page_data.get("facts", {})
        fact_items = []
        
        # 株価指数のFact
        price_fact = facts.get("price")
        if price_fact and price_fact.get("is_valid"):
            price_interp = page_data.get("interpretations", {}).get("price", "")
            if price_interp:
                fact_items.append(price_interp)
        
        # 政策金利のFact
        policy_fact = facts.get("policy_rate")
        if policy_fact and policy_fact.get("is_valid"):
            rate_interp = page_data.get("interpretations", {}).get("rate", "")
            if rate_interp:
                fact_items.append(rate_interp)
        
        # CPIのFact
        cpi_fact = facts.get("cpi")
        if cpi_fact and cpi_fact.get("is_valid"):
            cpi_interp = page_data.get("interpretations", {}).get("cpi", "")
            if cpi_interp:
                fact_items.append(cpi_interp)
        
        # EPS+PERのFact
        eps_per_fact = facts.get("eps_per")
        if eps_per_fact and eps_per_fact.get("is_valid"):
            eps_per_interp = page_data.get("interpretations", {}).get("eps_per", "")
            if eps_per_interp:
                fact_items.append(eps_per_interp)
        
        # Factを箇条書きに変換
        if fact_items:
            fact_content = SectionRenderer._format_fact_list("\n".join(fact_items))
        else:
            fact_content = "<ul class=\"fact-list\"><li>データが取得できません。</li></ul>"
        
        section_html = Layout.get_section(
            "① 観測事実",
            "",
            fact_content,
            ""
        )
        return section_html.replace('<section class="card">', '<section class="card block-1">')
    
    @staticmethod
    def render_interpretation_section(page_data: Dict[str, Any]) -> str:
        """② 解釈セクションをレンダリング"""
        from .layout import Layout
        
        interpretation_content = "<p>解釈情報は現在準備中です。</p>"
        
        section_html = Layout.get_section(
            "② 解釈",
            "",
            interpretation_content,
            ""
        )
        return section_html.replace('<section class="card">', '<section class="card block-2">')
    
    @staticmethod
    def render_assumption_section(page_data: Dict[str, Any]) -> str:
        """③ 前提セクションをレンダリング"""
        from .layout import Layout
        
        assumption_content = "<p>前提情報は現在準備中です。</p>"
        
        section_html = Layout.get_section(
            "③ 前提",
            "",
            assumption_content,
            ""
        )
        return section_html.replace('<section class="card">', '<section class="card block-3">')
    
    @staticmethod
    def render_turning_point_section(page_data: Dict[str, Any]) -> str:
        """④ 転換条件セクションをレンダリング"""
        from .layout import Layout
        
        turning_point_content = "<p>転換条件情報は現在準備中です。</p>"
        
        section_html = Layout.get_section(
            "④ 転換条件",
            "",
            turning_point_content,
            ""
        )
        return section_html.replace('<section class="card">', '<section class="card block-4">')
    
    @staticmethod
    def render_reference_section(page_data: Dict[str, Any]) -> str:
        """⑤ 参考情報セクションをレンダリング"""
        from .layout import Layout
        
        reference_content = "<p>参考情報は現在準備中です。</p>"
        
        section_html = Layout.get_section(
            "⑤ 参考情報",
            "",
            reference_content,
            ""
        )
        return section_html.replace('<section class="card">', '<section class="card block-5">')
    
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


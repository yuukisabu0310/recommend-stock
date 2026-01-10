"""
HTML生成
"""
from typing import Dict, Any
from .layout import Layout
from .section import SectionRenderer


class HTMLGenerator:
    """HTMLを生成するクラス"""
    
    @staticmethod
    def generate_page_html(page_data: Dict[str, Any]) -> str:
        """
        ページHTMLを生成
        
        Args:
            page_data: ページデータ
        
        Returns:
            str: HTML文字列
        """
        market_name = page_data.get("market_name", "")
        timeframe_name = page_data.get("timeframe_name", "")
        
        # ヘッダー
        header = Layout.get_header(market_name, timeframe_name)
        
        # セクション
        sections = []
        
        # ① 株価指数チャート
        sections.append(SectionRenderer.render_price_section(page_data))
        
        # ② 政策金利 + 長期金利
        sections.append(SectionRenderer.render_rate_section(page_data))
        
        # ③ CPI
        sections.append(SectionRenderer.render_cpi_section(page_data))
        
        # ④ EPS + PER
        sections.append(SectionRenderer.render_eps_per_section(page_data))
        
        # コンテンツ結合
        content = header + "\n".join(sections)
        
        # ベースHTML生成
        title = f"{market_name} - {timeframe_name}市場レポート"
        html = Layout.get_base_html(title, content)
        
        return html
    
    @staticmethod
    def generate_index_html() -> str:
        """
        インデックスページを生成
        
        Returns:
            str: HTML文字列
        """
        links = [
            ("US-short.html", "米国 - 短期"),
            ("US-medium.html", "米国 - 中期"),
            ("US-long.html", "米国 - 長期"),
            ("JP-short.html", "日本 - 短期"),
            ("JP-medium.html", "日本 - 中期"),
            ("JP-long.html", "日本 - 長期"),
        ]
        
        link_items = "\n".join([
            f'<li><a href="logs/{filename}" style="color: #2563eb; text-decoration: none; font-weight: 500;">{name}</a></li>'
            for filename, name in links
        ])
        
        content = f"""<header>
            <h1>v2 Market Report</h1>
            <p class="subtitle">実データに基づく市場分析レポート</p>
        </header>
        <div class="section">
            <h2 class="section-title">レポート一覧</h2>
            <ul style="list-style: none; padding: 0;">
                {link_items}
            </ul>
        </div>"""
        
        return Layout.get_base_html("v2 Market Report - インデックス", content)


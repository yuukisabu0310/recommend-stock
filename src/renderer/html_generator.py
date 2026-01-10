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
        ページHTMLを生成（CSP準拠、UI改善版）
        
        Args:
            page_data: ページデータ
        
        Returns:
            str: HTML文字列
        """
        market_name = page_data.get("market_name", "")
        timeframe_name = page_data.get("timeframe_name", "")
        market_code = page_data.get("market_code", "US")
        timeframe_code = page_data.get("timeframe_code", "short")
        
        # ヘッダー（市場・期間選択UIを含む）
        header = Layout.get_header(market_name, timeframe_name, market_code, timeframe_code)
        
        # セクション
        sections = []
        
        # ① 株価指数チャート（ファーストビューに表示）
        sections.append(SectionRenderer.render_price_section(page_data, is_details=False))
        
        # ② 政策金利 + 長期金利（詳細に折りたたみ）
        sections.append(SectionRenderer.render_rate_section(page_data, is_details=True))
        
        # ③ CPI（詳細に折りたたみ）
        sections.append(SectionRenderer.render_cpi_section(page_data, is_details=True))
        
        # ④ EPS + PER（詳細に折りたたみ）
        sections.append(SectionRenderer.render_eps_per_section(page_data, is_details=True))
        
        # コンテンツ結合
        content = header + "\n".join(sections)
        
        # ベースHTML生成
        title = f"{market_name} - {timeframe_name}市場レポート"
        html = Layout.get_base_html(title, content)
        
        return html
    
    @staticmethod
    def generate_index_html() -> str:
        """
        インデックスページを生成（CSP準拠）
        
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
            f'<li><a href="logs/{filename}" class="report-link">{name}</a></li>'
            for filename, name in links
        ])
        
        content = f"""<header>
            <h1>v2 Market Report</h1>
            <p class="subtitle">実データに基づく市場分析レポート</p>
        </header>
        <div class="section">
            <h2 class="section-title">レポート一覧</h2>
            <ul class="report-list">
                {link_items}
            </ul>
        </div>"""
        
        # インデックスページはルートなので、パスを調整
        html = Layout.get_base_html("v2 Market Report - インデックス", content)
        # インデックスページ用にパスを修正
        html = html.replace('../assets/', 'assets/')
        return html


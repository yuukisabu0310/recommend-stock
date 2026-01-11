"""
HTML生成
"""
from typing import Dict, Any
from datetime import datetime
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
        
        # セクション（すべて常時表示）
        sections = []
        
        # ① 株価指数チャート
        sections.append(SectionRenderer.render_price_section(page_data))
        
        # ② 政策金利 + 長期金利
        sections.append(SectionRenderer.render_rate_section(page_data))
        
        # ③ CPI
        sections.append(SectionRenderer.render_cpi_section(page_data))
        
        # ④ EPS + PER
        sections.append(SectionRenderer.render_eps_per_section(page_data))
        
        # コンテンツ結合（ダッシュボード型レイアウト）
        sections_html = "\n".join(sections)
        content = header + f'<div class="dashboard">\n{sections_html}\n</div>'
        
        # FactデータをJSON形式で埋め込み（ヒートマップ用）
        import json
        import pandas as pd
        
        heatmap_data = []
        facts = page_data.get("facts", {})
        
        # 株価データからヒートマップ用データを生成
        price_fact = facts.get("price")
        if price_fact and price_fact.get("is_valid"):
            price_data = price_fact.get("data")
            symbol = price_fact.get("symbol", "")
            if price_data is not None and not price_data.empty and "Close" in price_data.columns:
                close_values = price_data["Close"].dropna()
                if len(close_values) >= 2:
                    current = float(close_values.iloc[-1])
                    previous = float(close_values.iloc[-2])
                    change_pct = ((current - previous) / previous) * 100 if previous != 0 else 0
                    
                    # 変化率の絶対値で弱/中/強を判定
                    abs_change = abs(change_pct)
                    if abs_change < 1.0:
                        strength = "weak"
                    elif abs_change < 3.0:
                        strength = "mid"
                    else:
                        strength = "strong"
                    
                    direction = "up" if change_pct > 0 else "down" if change_pct < 0 else "flat"
                    
                    heatmap_data.append({
                        "symbol": symbol,
                        "direction": direction,
                        "strength": strength,
                        "change_pct": round(change_pct, 2)
                    })
        
        # JSONデータをスクリプトタグに埋め込み
        heatmap_json = json.dumps(heatmap_data, ensure_ascii=False)
        heatmap_script = f'<script>window.heatmapData = {heatmap_json};</script>'
        
        # 憲法準拠：複数期間チャートデータをJSON形式で埋め込み
        multi_period_chart_data = page_data.get("chart_data", {})
        chart_data_json = json.dumps(multi_period_chart_data, ensure_ascii=False, default=str)
        chart_data_script = f'<script>window.multiPeriodChartData = {chart_data_json};</script>'
        
        # 憲法準拠：初期表示用のPlotly.newPlot()スクリプトを生成
        init_chart_script = '<script>'
        init_chart_script += 'if (typeof Plotly !== "undefined" && window.multiPeriodChartData) {'
        init_chart_script += '  const chartTypes = ["price", "rate", "cpi", "eps_per"];'
        init_chart_script += '  const chartIds = {"price": "price-chart", "rate": "rate-chart", "cpi": "cpi-chart", "eps_per": "eps-per-chart"};'
        init_chart_script += '  chartTypes.forEach(function(chartType) {'
        init_chart_script += '    const chartData = window.multiPeriodChartData[chartType];'
        init_chart_script += '    if (chartData) {'
        init_chart_script += '      const periods = Object.keys(chartData).map(Number).sort((a, b) => a - b);'
        init_chart_script += '      if (periods.length > 0) {'
        init_chart_script += '        const firstPeriod = periods[0];'
        init_chart_script += '        const periodData = chartData[firstPeriod];'
        init_chart_script += '        const chartId = chartIds[chartType];'
        init_chart_script += '        const chartDiv = document.getElementById(chartId);'
        init_chart_script += '        if (chartDiv && periodData && periodData.traces && periodData.layout) {'
        init_chart_script += '          Plotly.newPlot(chartId, periodData.traces, periodData.layout, {responsive: true});'
        init_chart_script += '        }'
        init_chart_script += '      }'
        init_chart_script += '    }'
        init_chart_script += '  });'
        init_chart_script += '}'
        init_chart_script += '</script>'
        
        # ベースHTML生成
        title = f"{market_name} - {timeframe_name}市場レポート"
        html = Layout.get_base_html(title, content)
        
        # 生成日時を取得して置換
        generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        html = html.replace(
            "<!--REPORT_TIMESTAMP-->",
            f'<div class="report-generated">Generated at: {generated_at}</div>'
        )
        
        # スクリプトタグをbodyの最後に追加
        html = html.replace('</body>', f'{heatmap_script}\n{chart_data_script}\n{init_chart_script}</body>')
        
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
        # Skeleton UIを含まないベースHTMLを生成
        html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.plot.ly; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self' https://api.github.com;">
    <title>v2 Market Report - インデックス</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+JP:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="assets/css/main.css">
</head>
<body>
    <div class="container">
        {content}
    </div>
    <script src="assets/js/main.js"></script>
</body>
</html>"""
        return html


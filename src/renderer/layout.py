"""
HTMLレイアウト
"""
from typing import Dict, Any


class Layout:
    """HTMLレイアウトクラス"""
    
    @staticmethod
    def get_base_html(title: str, content: str) -> str:
        """
        ベースHTMLを生成（CSP準拠：外部CSS/JSファイルを使用）
        
        Args:
            title: ページタイトル
            content: コンテンツ
        
        Returns:
            str: HTML文字列
        """
        return f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.plot.ly; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self' https://api.github.com;">
    <title>{title}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+JP:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="../assets/css/main.css">
</head>
<body>
    <div class="container">
        <!-- Skeleton UI -->
        <div id="skeleton" class="skeleton hidden">
            <div class="skel-card"></div>
            <div class="skel-card"></div>
            <div class="skel-card"></div>
        </div>
        {content}
    </div>
    <script src="../assets/js/main.js"></script>
</body>
</html>"""
    
    @staticmethod
    def get_header(market_name: str, timeframe_name: str, market_code: str, timeframe_code: str) -> str:
        """
        ヘッダーを生成（市場・期間選択UIを含む）
        
        Args:
            market_name: 市場名
            timeframe_name: 期間名
            market_code: 市場コード（"US" or "JP"）
            timeframe_code: 期間コード（"short", "medium", "long"）
        
        Returns:
            str: HTML文字列
        """
        market_selector = Layout.get_market_selector(market_code)
        timeframe_selector = Layout.get_timeframe_selector(timeframe_code)
        
        return f"""<header>
            <h1>{market_name} - {timeframe_name}市場レポート</h1>
            <p class="subtitle">実データに基づく市場分析（判断材料の提供のみ）</p>
            {market_selector}
            {timeframe_selector}
        </header>"""
    
    @staticmethod
    def get_section(title: str, chart_html: str, interpretation: str, 
                   period_selector: str = "", is_details: bool = False) -> str:
        """
        セクションを生成（詳細は折りたたみ可能）
        
        Args:
            title: セクションタイトル
            chart_html: チャートHTML
            interpretation: 解釈文章
            period_selector: 期間選択UI（オプション）
            is_details: 詳細セクションかどうか（折りたたみ対象）
        
        Returns:
            str: HTML文字列
        """
        if is_details:
            return f"""<div class="section">
                <button class="details-toggle">詳細を見る</button>
                <div class="details-content">
                    <h2 class="section-title">{title}</h2>
                    {period_selector}
                    <div class="chart-container">
                        {chart_html}
                    </div>
                    <div class="interpretation">
                        {interpretation}
                    </div>
                </div>
            </div>"""
        else:
            return f"""<div class="section">
                <h2 class="section-title">{title}</h2>
                {period_selector}
                <div class="chart-container">
                    {chart_html}
                </div>
                <div class="interpretation">
                    {interpretation}
                </div>
            </div>"""
    
    @staticmethod
    def get_period_selector(years: int, switchable_years: list, chart_id: str) -> str:
        """
        期間選択UIを生成（CSP準拠：data属性のみ使用）
        
        Args:
            years: 現在の年数
            switchable_years: 切替可能な年数のリスト
            chart_id: チャートID
        
        Returns:
            str: HTML文字列
        """
        if not switchable_years:
            return ""
        
        buttons = []
        all_years = sorted(set([years] + switchable_years))
        
        for y in all_years:
            active_class = "active" if y == years else ""
            buttons.append(
                f'<button class="period-btn {active_class}" data-years="{y}" data-chart-id="{chart_id}">{y}年</button>'
            )
        
        return f'<div class="period-selector">{"".join(buttons)}</div>'
    
    @staticmethod
    def get_market_selector(current_market: str) -> str:
        """
        市場選択UIを生成
        
        Args:
            current_market: 現在の市場（"US" or "JP"）
        
        Returns:
            str: HTML文字列
        """
        markets = [
            ("US", "米国"),
            ("JP", "日本")
        ]
        
        buttons = []
        for market_code, market_name in markets:
            active_class = "active" if market_code == current_market else ""
            buttons.append(
                f'<button class="market-btn {active_class}" data-market="{market_code}">{market_name}</button>'
            )
        
        return f'<div class="market-selector">{"".join(buttons)}</div>'
    
    @staticmethod
    def get_timeframe_selector(current_timeframe: str) -> str:
        """
        期間選択UIを生成
        
        Args:
            current_timeframe: 現在の期間（"short", "medium", "long"）
        
        Returns:
            str: HTML文字列
        """
        timeframes = [
            ("short", "短期"),
            ("medium", "中期"),
            ("long", "長期")
        ]
        
        buttons = []
        for timeframe_code, timeframe_name in timeframes:
            active_class = "active" if timeframe_code == current_timeframe else ""
            buttons.append(
                f'<button class="timeframe-btn {active_class}" data-timeframe="{timeframe_code}">{timeframe_name}</button>'
            )
        
        return f'<div class="timeframe-selector">{"".join(buttons)}</div>'
    
    @staticmethod
    def get_rank_cards(rank_data: list) -> str:
        """
        ランクカードUIを生成
        
        Args:
            rank_data: ランクデータのリスト [{"rank": "A", "symbol": "AAPL"}, ...]
        
        Returns:
            str: HTML文字列
        """
        if not rank_data:
            return '<div class="empty-card">該当銘柄なし</div>'
        
        cards = []
        for item in rank_data:
            rank = item.get("rank", "C").upper()
            symbol = item.get("symbol", "")
            cards.append(
                f'<div class="rank-card rank-{rank}">'
                f'<div class="rank-letter">{rank}</div>'
                f'<div class="symbol">{symbol}</div>'
                f'</div>'
            )
        
        return f'<div class="rank-cards-container">{"".join(cards)}</div>'


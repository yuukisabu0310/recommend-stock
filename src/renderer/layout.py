"""
HTMLレイアウト
"""
from typing import Dict, Any


class Layout:
    """HTMLレイアウトクラス"""
    
    @staticmethod
    def get_base_html(title: str, content: str) -> str:
        """
        ベースHTMLを生成
        
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
    <title>{title}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+JP:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', 'Noto Sans JP', sans-serif;
            background: #f8fafc;
            color: #1e293b;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem 1rem;
        }}
        
        header {{
            background: white;
            padding: 2rem;
            border-radius: 1rem;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            margin-bottom: 2rem;
        }}
        
        h1 {{
            font-size: 2rem;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 0.5rem;
        }}
        
        .subtitle {{
            color: #64748b;
            font-size: 1rem;
        }}
        
        .section {{
            background: white;
            padding: 2rem;
            border-radius: 1rem;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            margin-bottom: 2rem;
        }}
        
        .section-title {{
            font-size: 1.5rem;
            font-weight: 600;
            color: #1e293b;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #e2e8f0;
        }}
        
        .chart-container {{
            margin: 1.5rem 0;
        }}
        
        .interpretation {{
            background: #f1f5f9;
            padding: 1.5rem;
            border-radius: 0.75rem;
            margin-top: 1rem;
            color: #475569;
            line-height: 1.8;
        }}
        
        .period-selector {{
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1rem;
            flex-wrap: wrap;
        }}
        
        .period-btn {{
            padding: 0.5rem 1rem;
            border: 1px solid #cbd5e1;
            background: white;
            border-radius: 0.5rem;
            cursor: pointer;
            font-size: 0.875rem;
            transition: all 0.2s;
        }}
        
        .period-btn:hover {{
            background: #f1f5f9;
            border-color: #2563eb;
        }}
        
        .period-btn.active {{
            background: #2563eb;
            color: white;
            border-color: #2563eb;
        }}
        
        @media (max-width: 768px) {{
            .container {{
                padding: 1rem 0.5rem;
            }}
            
            header {{
                padding: 1.5rem;
            }}
            
            h1 {{
                font-size: 1.5rem;
            }}
            
            .section {{
                padding: 1.5rem;
            }}
            
            .section-title {{
                font-size: 1.25rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        {content}
    </div>
</body>
</html>"""
    
    @staticmethod
    def get_header(market_name: str, timeframe_name: str) -> str:
        """
        ヘッダーを生成
        
        Args:
            market_name: 市場名
            timeframe_name: 期間名
        
        Returns:
            str: HTML文字列
        """
        return f"""<header>
            <h1>{market_name} - {timeframe_name}市場レポート</h1>
            <p class="subtitle">実データに基づく市場分析（判断材料の提供のみ）</p>
        </header>"""
    
    @staticmethod
    def get_section(title: str, chart_html: str, interpretation: str, 
                   period_selector: str = "") -> str:
        """
        セクションを生成
        
        Args:
            title: セクションタイトル
            chart_html: チャートHTML
            interpretation: 解釈文章
            period_selector: 期間選択UI（オプション）
        
        Returns:
            str: HTML文字列
        """
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
        期間選択UIを生成
        
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


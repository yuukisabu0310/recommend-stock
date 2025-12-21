"""
HTML生成モジュール
分析結果をモダンなHTML形式で出力する
"""

import yaml
import json
from typing import Dict, List
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class HTMLGenerator:
    """HTML生成クラス"""
    
    def __init__(self, config_path: str = "config/config.yml"):
        """初期化"""
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.output_dir = Path(self.config['output']['pages_directory'])
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.score_labels = self.config['score_labels']
        self.score_colors = {
            "2": {"bg": "bg-green-100", "text": "text-green-800", "border": "border-green-300"},
            "1": {"bg": "bg-green-50", "text": "text-green-700", "border": "border-green-200"},
            "0": {"bg": "bg-gray-100", "text": "text-gray-800", "border": "border-gray-300"},
            "-1": {"bg": "bg-red-50", "text": "text-red-700", "border": "border-red-200"},
            "-2": {"bg": "bg-red-100", "text": "text-red-800", "border": "border-red-300"},
        }
    
    def _get_score_style(self, score: int) -> Dict[str, str]:
        """スコアに応じたスタイルを取得"""
        score_str = str(score)
        return self.score_colors.get(score_str, self.score_colors["0"])
    
    def _get_market_stance(self, score: int) -> str:
        """スコアから市場スタンス（🟢🟡🔴）を取得"""
        if score >= 1:
            return "🟢"  # 強気
        elif score <= -1:
            return "🔴"  # 弱気
        else:
            return "🟡"  # 中立
    
    def _generate_conclusion_block(self, country_name: str, timeframe_name: str, direction_label: str, summary) -> str:
        """
        結論ブロックを生成（2行固定）
        
        Args:
            country_name: 国名
            timeframe_name: 期間名
            direction_label: 方向ラベル
            summary: LLM生成のsummary（2文形式、結論ブロック専用。文字列またはリスト）
        
        Returns:
            結論ブロックのHTML
        """
        # summaryがリストの場合は文字列に変換
        if isinstance(summary, list):
            summary = ' '.join(str(s) for s in summary if s)
        elif summary is None:
            summary = ""
        else:
            summary = str(summary)
        
        # summaryから2文を抽出（改行または句点で分割）
        # summaryは「【結論】◯◯市場は（期間）で（方向ラベル）」と「主要因を1つだけ短文で補足」の2文形式を想定
        summary_lines = summary.replace('\n', '。').split('。')
        summary_lines = [s.strip() for s in summary_lines if s.strip()]
        
        # 1行目：【結論】◯◯市場は（期間）で（方向ラベル）
        # summaryの1文目に「【結論】」が含まれている場合はそれを使用、なければ生成
        if summary_lines and len(summary_lines) > 0 and '【結論】' in summary_lines[0]:
            line1 = summary_lines[0]
            # 「【結論】」が含まれていない場合は追加
            if not line1.startswith('【結論】'):
                line1 = f"【結論】{line1}"
        else:
            line1 = f"【結論】{country_name}市場は{timeframe_name}で{direction_label}"
        
        # 2行目：主要因を1つだけ短文で補足（summaryの2文目、または1文目から抽出）
        if summary_lines and len(summary_lines) > 1:
            # 2文目を使用
            line2 = summary_lines[1]
        elif summary_lines and len(summary_lines) > 0:
            # 1文目から抽出（「【結論】」部分を除く）
            line2 = summary_lines[0].replace('【結論】', '').strip()
            if country_name in line2 and timeframe_name in line2 and direction_label in line2:
                # 1文目が結論形式の場合は、主要因として簡潔な説明を生成
                line2 = "データに基づく判断材料を提示しています。"
        else:
            line2 = "データに基づく判断材料を提示しています。"
        
        # 長すぎる場合は短縮（50文字以内）
        if len(line2) > 50:
            line2 = line2[:47] + "..."
        
        return f"""
            <!-- 結論ブロック -->
            <div class="bg-blue-50 border-l-4 border-blue-500 p-6 mb-6 rounded-lg shadow-md">
                <p class="text-lg font-bold text-blue-900 mb-2">{line1}</p>
                <p class="text-sm text-blue-800">{line2}</p>
            </div>
"""
    
    def _generate_header(self, title: str = "株式市場分析レポート", include_charts: bool = False) -> str:
        """
        HTMLヘッダーを生成
        
        Args:
            title: ページタイトル
            include_charts: Chart.jsを読み込むかどうか（logsページのみTrue）
        """
        date_str = datetime.now().strftime("%Y年%m月%d日 %H:%M")
        chart_js = '<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>' if include_charts else ''
        return f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    {chart_js}
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+JP:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body {{
            font-family: 'Inter', 'Noto Sans JP', sans-serif;
        }}
        .card {{
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
        }}
    </style>
</head>
<body class="bg-gray-50">
    <div class="min-h-screen">
        <!-- ヘッダー -->
        <header class="bg-white shadow-md">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                <h1 class="text-3xl font-bold text-gray-900">{title}</h1>
                <p class="mt-2 text-sm text-gray-600">更新日時: {date_str}</p>
            </div>
        </header>
        
        <!-- メインコンテンツ -->
        <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
"""
    
    def _generate_footer(self) -> str:
        """HTMLフッターを生成"""
        return """        </main>
        
        <!-- フッター -->
        <footer class="bg-white border-t mt-12">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                <div class="space-y-4">
                    <div class="bg-yellow-50 border-l-4 border-yellow-400 p-4 rounded-lg">
                        <p class="text-sm text-yellow-800">
                            <strong>免責事項</strong>: 本レポートは研究用途であり、投資助言や売買指示を目的としたものではありません。投資判断は自己責任で行ってください。過去の実績は将来を保証するものではありません。
                        </p>
                    </div>
                    <div class="text-sm text-gray-600 space-y-2">
                        <p><strong>データ取得元:</strong> Yahoo Finance (yfinance), FRED API, e-Stat API</p>
                        <p><strong>更新頻度:</strong> 毎日（GitHub Actions自動実行）</p>
                        <p><strong>指標計算方法:</strong></p>
                        <ul class="list-disc list-inside ml-4 space-y-1">
                            <li>移動平均: 単純移動平均（20日、75日、200日）</li>
                            <li>ボラティリティ: 過去30日の日次リターンの標準偏差を年率換算</li>
                            <li>出来高比率: 最新出来高 / 過去30日の平均出来高</li>
                            <li>トレンド判定: 価格と移動平均の順序関係から判定</li>
                        </ul>
                    </div>
                </div>
            </div>
        </footer>
    </div>
</body>
</html>"""
    
    def generate_overview_cards(self, analysis_result: Dict) -> str:
        """
        Overviewカードを生成（クリック可能、logsページへリンク）
        
        市場判断の文章は表示せず、方向感・要因タグ・超短文要約のみを表示
        """
        countries = self.config['countries']
        timeframes = self.config['timeframes']
        overview = analysis_result.get("overview", {})
        countries_data = analysis_result.get("countries", {})
        
        html = """
        <!-- Market Direction Overview -->
        <section class="mb-12">
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
"""
        
        for country_config in countries:
            country_code = country_config['code']
            country_name = country_config['name']
            directions = overview.get(country_code, {})
            country_result = countries_data.get(country_code, {})
            
            html += f"""
                <div class="bg-white rounded-2xl shadow-md overflow-hidden card">
                    <div class="p-6">
                        <h3 class="text-xl font-semibold text-gray-900 mb-4">{country_name}</h3>
                        <div class="space-y-3">
"""
            
            for timeframe in timeframes:
                timeframe_code = timeframe['code']
                timeframe_name = timeframe['name']
                
                direction = directions.get(timeframe_code, {})
                score = direction.get("score", 0)
                has_risk = direction.get("has_risk", False)
                label = self.score_labels.get(str(score), "→ 中立")
                
                # 詳細データから要因タグと要約を取得
                direction_data = country_result.get("directions", {}).get(timeframe_code, {})
                rule_components = direction_data.get("rule_based_components", {})
                summary = direction_data.get("summary", "")
                
                # 要因タグを取得（既存分類から）
                factor_tags = []
                if rule_components:
                    factor_map = {
                        "macro": "マクロ",
                        "financial": "金融",
                        "technical": "テクニカル",
                        "structural": "構造"
                    }
                    # スコアの絶対値が大きい順に最大2つ
                    factor_scores = {}
                    for factor, data in rule_components.items():
                        if isinstance(data, dict):
                            factor_scores[factor] = abs(data.get("score", 0))
                        else:
                            factor_scores[factor] = abs(data) if isinstance(data, (int, float)) else 0
                    
                    sorted_factors = sorted(factor_scores.items(), key=lambda x: x[1], reverse=True)
                    factor_tags = [factor_map.get(f, f) for f, _ in sorted_factors[:2] if _ > 0]
                
                # 一文理由を生成（20文字前後、意味を変えない）
                short_summary = ""
                if summary:
                    # summaryから最初の文を取得し、20文字前後に短縮
                    summary_lines = str(summary).replace('\n', '。').split('。')
                    if summary_lines and summary_lines[0]:
                        first_line = summary_lines[0].strip()
                        # 意味を変えない範囲で短縮（20文字前後）
                        if len(first_line) > 25:
                            # 句点や読点で区切って短縮
                            if '、' in first_line:
                                parts = first_line.split('、')
                                short_summary = parts[0][:22] if len(parts[0]) <= 22 else parts[0][:20] + "..."
                            elif '。' in first_line:
                                parts = first_line.split('。')
                                short_summary = parts[0][:22] if len(parts[0]) <= 22 else parts[0][:20] + "..."
                            else:
                                short_summary = first_line[:20] + "..."
                        else:
                            short_summary = first_line
                else:
                    # 要因タグから簡易要約を生成
                    if factor_tags:
                        short_summary = f"{factor_tags[0]}要因が主因"
                    else:
                        short_summary = "データに基づく判断"
                
                style = self._get_score_style(score)
                stance = self._get_market_stance(score)
                risk_icon = "⚠️" if has_risk else ""
                
                # カード全体をクリック可能にする
                html += f"""
                            <a href="./logs/{country_code}-{timeframe_code}.html" 
                               class="block border-l-4 {style['border']} pl-3 py-3 rounded-r-lg hover:bg-gray-50 transition cursor-pointer">
                                <div class="flex items-center justify-between mb-2">
                                    <span class="text-sm font-medium text-gray-700">{timeframe_name}</span>
                                    <span class="inline-flex items-center px-3 py-1 rounded-lg {style['bg']} {style['text']} text-sm font-medium">
                                        {stance} {label} {risk_icon}
                                    </span>
                                </div>
"""
                
                # 要因タグを表示
                if factor_tags:
                    html += f"""
                                <div class="flex flex-wrap gap-1 mb-2">
"""
                    for tag in factor_tags:
                        html += f"""
                                    <span class="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded">{tag}</span>
"""
                    html += """
                                </div>
"""
                
                # 一文理由を表示
                if short_summary:
                    html += f"""
                                <p class="text-xs text-gray-600 mb-2">{short_summary}</p>
"""
                
                # 詳細リンク
                html += f"""
                                <a href="./logs/{country_code}-{timeframe_code}.html" 
                                   class="text-xs text-blue-600 hover:text-blue-800 underline">
                                    詳細を見る →
                                </a>
                            </a>
"""
            
            html += """
                        </div>
                    </div>
                </div>
"""
        
        html += """
            </div>
        </section>
"""
        return html
    
    def generate_summary_section(self, analysis_result: Dict) -> str:
        """全体サマリーセクションを生成"""
        date_str = datetime.now().strftime("%Y年%m月%d日")
        overview = analysis_result.get("overview", {})
        
        html = f"""
        <!-- 全体サマリー -->
        <section class="mb-12">
            <h2 class="text-2xl font-bold text-gray-900 mb-6">全体サマリー</h2>
            <div class="bg-white rounded-2xl shadow-md p-6">
                <p class="text-gray-700 mb-4">{date_str}の市場環境を要約します。</p>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
"""
        
        for country_code, directions in overview.items():
            country_result = analysis_result["countries"].get(country_code, {})
            country_name = country_result.get("name", country_code)
            
            medium_score = directions.get("medium", {}).get("score", 0)
            label = self.score_labels.get(str(medium_score), "中立")
            style = self._get_score_style(medium_score)
            
            html += f"""
                    <div class="flex items-center space-x-3 p-3 rounded-lg {style['bg']}">
                        <span class="font-semibold {style['text']}">{country_name}</span>
                        <span class="text-sm {style['text']}">{label}</span>
                    </div>
"""
        
        html += """
                </div>
            </div>
        </section>
"""
        return html
    
    def generate_country_analysis(self, country_result: Dict, analysis_result: Dict) -> str:
        """国別分析セクションを生成"""
        country_name = country_result["name"]
        country_code = country_result["code"]
        directions = country_result["directions"]
        
        html = f"""
        <!-- {country_name} 市場判断 -->
        <section class="mb-12">
            <h2 class="text-2xl font-bold text-gray-900 mb-6">{country_name} 市場判断</h2>
"""
        
        for timeframe in self.config['timeframes']:
            timeframe_code = timeframe['code']
            timeframe_name = timeframe['name']
            
            direction = directions.get(timeframe_code, {})
            score = direction.get("score", 0)
            label = direction.get("direction_label", direction.get("label", "中立"))
            has_risk = direction.get("has_risk", False)
            
            style = self._get_score_style(score)
            stance = self._get_market_stance(score)
            risk_badge = '<span class="ml-2 text-red-600">⚠️ リスクあり</span>' if has_risk else ''
            
            analysis_text = country_result.get("analysis", {}).get(timeframe_code, {})
            
            html += f"""
            <div class="bg-white rounded-2xl shadow-md p-6 mb-6 card">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-xl font-semibold text-gray-900">{timeframe_name}</h3>
                    <span class="inline-flex items-center px-4 py-2 rounded-lg {style['bg']} {style['text']} font-medium">
                        {stance} {label}{risk_badge}
                    </span>
                </div>
"""
            
            # LLM分析結果を表示
            direction_data = directions.get(timeframe_code, {})
            
            # 前提条件を表示（必須）
            premise = direction_data.get("premise", "")
            if premise:
                html += f"""
                <div class="mb-4 p-4 bg-green-50 rounded-lg border-l-4 border-green-300">
                    <h4 class="text-lg font-semibold text-green-800 mb-2">前提条件</h4>
                    <p class="text-green-700 leading-relaxed">{premise}</p>
                </div>
"""
            
            if direction_data.get("summary"):
                html += f"""
                <div class="mb-4">
                    <h4 class="text-lg font-semibold text-gray-800 mb-2">市場環境サマリー</h4>
                    <p class="text-gray-700 leading-relaxed">{direction_data['summary']}</p>
                </div>
"""
            
            if direction_data.get("key_factors"):
                html += f"""
                <div class="mb-4">
                    <h4 class="text-lg font-semibold text-gray-800 mb-2">主要要因</h4>
                    <ul class="list-disc list-inside text-gray-700 space-y-1">
"""
                for factor in direction_data["key_factors"]:
                    html += f"""
                        <li>{factor}</li>
"""
                html += """
                    </ul>
                </div>
"""
            
            # リスクを表示（必須）
            risks = direction_data.get("risks", [])
            if risks:
                html += f"""
                <div class="mb-4 p-4 bg-red-50 rounded-lg border-l-4 border-red-300">
                    <h4 class="text-lg font-semibold text-red-800 mb-2">想定リスク</h4>
                    <ul class="list-disc list-inside text-red-700 space-y-1">
"""
                for risk in risks:
                    html += f"""
                        <li>{risk}</li>
"""
                html += """
                    </ul>
                </div>
"""
            
            # 転換シグナルを表示（必須）
            turning_points = direction_data.get("turning_points", [])
            if turning_points:
                html += f"""
                <div class="mb-4 p-4 bg-blue-50 rounded-lg border-l-4 border-blue-300">
                    <h4 class="text-lg font-semibold text-blue-800 mb-2">転換シグナル</h4>
                    <ul class="list-disc list-inside text-blue-700 space-y-1">
"""
                for point in turning_points:
                    html += f"""
                        <li>{point}</li>
"""
                html += """
                    </ul>
                </div>
"""
            
            html += f"""
                <a href="./logs/{country_code}-{timeframe_code}.html" 
                   class="inline-flex items-center text-sm text-blue-600 hover:text-blue-800 font-medium">
                    思考ログを見る →
                </a>
            </div>
"""
        
        html += """
        </section>
"""
        return html
    
    def generate_sector_analysis(self, sectors: List[Dict]) -> str:
        """セクター分析セクションを生成"""
        if not sectors:
            return ""
        
        html = """
        <!-- 注目セクター -->
        <section class="mb-12">
            <h2 class="text-2xl font-bold text-gray-900 mb-6">注目セクター</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
"""
        
        for i, sector in enumerate(sectors[:3], 1):
            html += f"""
                <div class="bg-white rounded-2xl shadow-md p-6 card">
                    <div class="flex items-center mb-4">
                        <span class="flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 text-blue-600 font-bold mr-3">
                            {i}
                        </span>
                        <h3 class="text-lg font-semibold text-gray-900">{sector.get('name', 'セクター')}</h3>
                    </div>
"""
            
            if sector.get('reason'):
                html += f"""
                    <div class="mb-3">
                        <p class="text-sm font-medium text-gray-600 mb-1">注目される理由</p>
                        <p class="text-gray-700 text-sm">{sector['reason']}</p>
                    </div>
"""
            
            if sector.get('related_fields'):
                fields = sector['related_fields']
                if isinstance(fields, str):
                    fields = [fields]
                html += f"""
                    <div class="mb-3">
                        <p class="text-sm font-medium text-gray-600 mb-1">波及する分野</p>
                        <div class="flex flex-wrap gap-2">
"""
                for field in fields:
                    html += f"""
                            <span class="px-2 py-1 bg-orange-100 text-orange-700 text-xs rounded-lg">{field}</span>
"""
                html += """
                        </div>
                    </div>
"""
            
            if sector.get('timeframe'):
                html += f"""
                    <div>
                        <span class="inline-flex items-center px-3 py-1 bg-gray-100 text-gray-700 text-xs rounded-lg">
                            期間: {sector['timeframe']}
                        </span>
                    </div>
"""
            
            html += """
                </div>
"""
        
        html += """
            </div>
        </section>
"""
        return html
    
    def generate_stock_recommendations(self, recommendations: Dict) -> str:
        """銘柄評価セクションを生成（推奨ではなく、判断材料の提示）"""
        if not recommendations:
            return ""
        
        html = """
        <!-- 参考銘柄情報 -->
        <section class="mb-12">
            <div class="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6 rounded-lg">
                <p class="text-sm text-yellow-800">
                    <strong>重要:</strong> 以下は参考情報であり、投資助言や売買指示ではありません。投資判断は自己責任で行ってください。
                </p>
            </div>
            <h2 class="text-2xl font-bold text-gray-900 mb-6">参考銘柄情報</h2>
"""
        
        # 日本株
        jp_stocks = recommendations.get("JP", [])
        if jp_stocks:
            html += """
            <div class="mb-8">
                <h3 class="text-xl font-semibold text-gray-900 mb-4">日本株</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
"""
            for stock in jp_stocks:
                stock_id = f"stock-{stock.get('ticker', '').replace('.', '-')}"
                fundamental = stock.get('fundamental_evaluation', {})
                technical = stock.get('technical_evaluation', {})
                overall = stock.get('overall_evaluation', '△')
                
                # 評価アイコンの色
                eval_colors = {
                    "◯": "text-green-600",
                    "△": "text-yellow-600",
                    "×": "text-red-600"
                }
                eval_color = eval_colors.get(overall, "text-gray-600")
                
                html += f"""
                    <div class="bg-white rounded-2xl shadow-md p-6 card cursor-pointer" onclick="showStockDetail('{stock_id}')">
                        <div class="flex items-center justify-between mb-3">
                            <h4 class="text-lg font-semibold text-gray-900">
                                {stock.get('rank', '')}位: {stock.get('name', '')}
                            </h4>
                            <span class="px-3 py-1 bg-blue-100 text-blue-700 text-sm font-medium rounded-lg">
                                {stock.get('ticker', '')}
                            </span>
                        </div>
                        <div class="space-y-2 text-sm">
                            <div>
                                <span class="font-medium text-gray-600">セクター:</span>
                                <span class="text-gray-700 ml-2">{stock.get('sector', '')}</span>
                            </div>
                            <div>
                                <span class="font-medium text-gray-600">事業概要:</span>
                                <p class="text-gray-700 mt-1 text-xs">{stock.get('business_summary', '')[:100]}...</p>
                            </div>
                            <div class="pt-2 border-t">
                                <span class="font-medium text-gray-600">総合評価:</span>
                                <span class="ml-2 text-lg font-bold {eval_color}">{overall}</span>
                            </div>
                            <div class="flex items-center space-x-4 text-xs">
                                <div>
                                    <span class="text-gray-600">売上成長:</span>
                                    <span class="ml-1 {eval_colors.get(fundamental.get('revenue_growth', '△'), 'text-gray-600')}">{fundamental.get('revenue_growth', '△')}</span>
                                </div>
                                <div>
                                    <span class="text-gray-600">営業利益率:</span>
                                    <span class="ml-1 {eval_colors.get(fundamental.get('operating_margin', '△'), 'text-gray-600')}">{fundamental.get('operating_margin', '△')}</span>
                                </div>
                                <div>
                                    <span class="text-gray-600">ROE:</span>
                                    <span class="ml-1 {eval_colors.get(fundamental.get('roe', '△'), 'text-gray-600')}">{fundamental.get('roe', '△')}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- 詳細パネル（モーダル） -->
                    <div id="{stock_id}" class="hidden fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
                        <div class="bg-white rounded-2xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6">
                            <div class="flex items-center justify-between mb-4">
                                <h3 class="text-2xl font-bold text-gray-900">{stock.get('name', '')} ({stock.get('ticker', '')})</h3>
                                <button onclick="hideStockDetail('{stock_id}')" class="text-gray-500 hover:text-gray-700 text-2xl">&times;</button>
                            </div>
                            
                            <div class="space-y-4">
                                <div>
                                    <h4 class="font-semibold text-gray-800 mb-2">セクター</h4>
                                    <p class="text-gray-700">{stock.get('sector', '')}</p>
                                </div>
                                
                                <div>
                                    <h4 class="font-semibold text-gray-800 mb-2">事業概要</h4>
                                    <p class="text-gray-700">{stock.get('business_summary', '')}</p>
                                </div>
                                
                                <div>
                                    <h4 class="font-semibold text-gray-800 mb-2">ファンダメンタル評価</h4>
                                    <div class="grid grid-cols-2 gap-2 text-sm">
                                        <div class="flex justify-between">
                                            <span class="text-gray-600">売上成長率:</span>
                                            <span class="{eval_colors.get(fundamental.get('revenue_growth', '△'), 'text-gray-600')} font-bold">{fundamental.get('revenue_growth', '△')}</span>
                                        </div>
                                        <div class="flex justify-between">
                                            <span class="text-gray-600">営業利益率:</span>
                                            <span class="{eval_colors.get(fundamental.get('operating_margin', '△'), 'text-gray-600')} font-bold">{fundamental.get('operating_margin', '△')}</span>
                                        </div>
                                        <div class="flex justify-between">
                                            <span class="text-gray-600">ROE:</span>
                                            <span class="{eval_colors.get(fundamental.get('roe', '△'), 'text-gray-600')} font-bold">{fundamental.get('roe', '△')}</span>
                                        </div>
                                        <div class="flex justify-between">
                                            <span class="text-gray-600">時価総額区分:</span>
                                            <span class="text-gray-700">{fundamental.get('market_cap_category', '')}</span>
                                        </div>
                                    </div>
                                </div>
                                
                                <div>
                                    <h4 class="font-semibold text-gray-800 mb-2">テクニカル評価</h4>
                                    <div class="grid grid-cols-2 gap-2 text-sm">
                                        <div class="flex justify-between">
                                            <span class="text-gray-600">トレンド:</span>
                                            <span class="{eval_colors.get(technical.get('trend', '△'), 'text-gray-600')} font-bold">{technical.get('trend', '△')}</span>
                                        </div>
                                        <div class="flex justify-between">
                                            <span class="text-gray-600">出来高:</span>
                                            <span class="{eval_colors.get(technical.get('volume', '△'), 'text-gray-600')} font-bold">{technical.get('volume', '△')}</span>
                                        </div>
                                    </div>
                                </div>
                                
                                <div>
                                    <h4 class="font-semibold text-gray-800 mb-2">市場環境との相性</h4>
                                    <p class="text-gray-700">{stock.get('market_compatibility', '')}</p>
                                </div>
                                
                                <div class="p-4 bg-green-50 rounded-lg border-l-4 border-green-300">
                                    <h4 class="font-semibold text-green-800 mb-2">前提条件</h4>
                                    <p class="text-green-700">{stock.get('premise', '')}</p>
                                </div>
                                
                                <div class="p-4 bg-red-50 rounded-lg border-l-4 border-red-300">
                                    <h4 class="font-semibold text-red-800 mb-2">リスク</h4>
                                    <ul class="list-disc list-inside text-red-700 space-y-1">
"""
                for risk in stock.get('risks', []):
                    html += f"""
                                        <li>{risk}</li>
"""
                html += """
                                    </ul>
                                </div>
                                
                                <div class="p-4 bg-blue-50 rounded-lg border-l-4 border-blue-300">
                                    <h4 class="font-semibold text-blue-800 mb-2">転換シグナル</h4>
                                    <ul class="list-disc list-inside text-blue-700 space-y-1">
"""
                for point in stock.get('turning_points', []):
                    html += f"""
                                        <li>{point}</li>
"""
                html += """
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>
"""
            html += """
                </div>
            </div>
"""
        
        # 米国株
        us_stocks = recommendations.get("US", [])
        if us_stocks:
            html += """
            <div>
                <h3 class="text-xl font-semibold text-gray-900 mb-4">米国株</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
"""
            for stock in us_stocks:
                stock_id = f"stock-{stock.get('ticker', '').replace('.', '-')}"
                fundamental = stock.get('fundamental_evaluation', {})
                technical = stock.get('technical_evaluation', {})
                overall = stock.get('overall_evaluation', '△')
                
                # 評価アイコンの色
                eval_colors = {
                    "◯": "text-green-600",
                    "△": "text-yellow-600",
                    "×": "text-red-600"
                }
                eval_color = eval_colors.get(overall, "text-gray-600")
                
                html += f"""
                    <div class="bg-white rounded-2xl shadow-md p-6 card cursor-pointer" onclick="showStockDetail('{stock_id}')">
                        <div class="flex items-center justify-between mb-3">
                            <h4 class="text-lg font-semibold text-gray-900">
                                {stock.get('rank', '')}位: {stock.get('name', '')}
                            </h4>
                            <span class="px-3 py-1 bg-blue-100 text-blue-700 text-sm font-medium rounded-lg">
                                {stock.get('ticker', '')}
                            </span>
                        </div>
                        <div class="space-y-2 text-sm">
                            <div>
                                <span class="font-medium text-gray-600">セクター:</span>
                                <span class="text-gray-700 ml-2">{stock.get('sector', '')}</span>
                            </div>
                            <div>
                                <span class="font-medium text-gray-600">事業概要:</span>
                                <p class="text-gray-700 mt-1 text-xs">{stock.get('business_summary', '')[:100]}...</p>
                            </div>
                            <div class="pt-2 border-t">
                                <span class="font-medium text-gray-600">総合評価:</span>
                                <span class="ml-2 text-lg font-bold {eval_color}">{overall}</span>
                            </div>
                            <div class="flex items-center space-x-4 text-xs">
                                <div>
                                    <span class="text-gray-600">売上成長:</span>
                                    <span class="ml-1 {eval_colors.get(fundamental.get('revenue_growth', '△'), 'text-gray-600')}">{fundamental.get('revenue_growth', '△')}</span>
                                </div>
                                <div>
                                    <span class="text-gray-600">営業利益率:</span>
                                    <span class="ml-1 {eval_colors.get(fundamental.get('operating_margin', '△'), 'text-gray-600')}">{fundamental.get('operating_margin', '△')}</span>
                                </div>
                                <div>
                                    <span class="text-gray-600">ROE:</span>
                                    <span class="ml-1 {eval_colors.get(fundamental.get('roe', '△'), 'text-gray-600')}">{fundamental.get('roe', '△')}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- 詳細パネル（モーダル） -->
                    <div id="{stock_id}" class="hidden fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
                        <div class="bg-white rounded-2xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6">
                            <div class="flex items-center justify-between mb-4">
                                <h3 class="text-2xl font-bold text-gray-900">{stock.get('name', '')} ({stock.get('ticker', '')})</h3>
                                <button onclick="hideStockDetail('{stock_id}')" class="text-gray-500 hover:text-gray-700 text-2xl">&times;</button>
                            </div>
                            
                            <div class="space-y-4">
                                <div>
                                    <h4 class="font-semibold text-gray-800 mb-2">セクター</h4>
                                    <p class="text-gray-700">{stock.get('sector', '')}</p>
                                </div>
                                
                                <div>
                                    <h4 class="font-semibold text-gray-800 mb-2">事業概要</h4>
                                    <p class="text-gray-700">{stock.get('business_summary', '')}</p>
                                </div>
                                
                                <div>
                                    <h4 class="font-semibold text-gray-800 mb-2">ファンダメンタル評価</h4>
                                    <div class="grid grid-cols-2 gap-2 text-sm">
                                        <div class="flex justify-between">
                                            <span class="text-gray-600">売上成長率:</span>
                                            <span class="{eval_colors.get(fundamental.get('revenue_growth', '△'), 'text-gray-600')} font-bold">{fundamental.get('revenue_growth', '△')}</span>
                                        </div>
                                        <div class="flex justify-between">
                                            <span class="text-gray-600">営業利益率:</span>
                                            <span class="{eval_colors.get(fundamental.get('operating_margin', '△'), 'text-gray-600')} font-bold">{fundamental.get('operating_margin', '△')}</span>
                                        </div>
                                        <div class="flex justify-between">
                                            <span class="text-gray-600">ROE:</span>
                                            <span class="{eval_colors.get(fundamental.get('roe', '△'), 'text-gray-600')} font-bold">{fundamental.get('roe', '△')}</span>
                                        </div>
                                        <div class="flex justify-between">
                                            <span class="text-gray-600">時価総額区分:</span>
                                            <span class="text-gray-700">{fundamental.get('market_cap_category', '')}</span>
                                        </div>
                                    </div>
                                </div>
                                
                                <div>
                                    <h4 class="font-semibold text-gray-800 mb-2">テクニカル評価</h4>
                                    <div class="grid grid-cols-2 gap-2 text-sm">
                                        <div class="flex justify-between">
                                            <span class="text-gray-600">トレンド:</span>
                                            <span class="{eval_colors.get(technical.get('trend', '△'), 'text-gray-600')} font-bold">{technical.get('trend', '△')}</span>
                                        </div>
                                        <div class="flex justify-between">
                                            <span class="text-gray-600">出来高:</span>
                                            <span class="{eval_colors.get(technical.get('volume', '△'), 'text-gray-600')} font-bold">{technical.get('volume', '△')}</span>
                                        </div>
                                    </div>
                                </div>
                                
                                <div>
                                    <h4 class="font-semibold text-gray-800 mb-2">市場環境との相性</h4>
                                    <p class="text-gray-700">{stock.get('market_compatibility', '')}</p>
                                </div>
                                
                                <div class="p-4 bg-green-50 rounded-lg border-l-4 border-green-300">
                                    <h4 class="font-semibold text-green-800 mb-2">前提条件</h4>
                                    <p class="text-green-700">{stock.get('premise', '')}</p>
                                </div>
                                
                                <div class="p-4 bg-red-50 rounded-lg border-l-4 border-red-300">
                                    <h4 class="font-semibold text-red-800 mb-2">リスク</h4>
                                    <ul class="list-disc list-inside text-red-700 space-y-1">
"""
                for risk in stock.get('risks', []):
                    html += f"""
                                        <li>{risk}</li>
"""
                html += """
                                    </ul>
                                </div>
                                
                                <div class="p-4 bg-blue-50 rounded-lg border-l-4 border-blue-300">
                                    <h4 class="font-semibold text-blue-800 mb-2">転換シグナル</h4>
                                    <ul class="list-disc list-inside text-blue-700 space-y-1">
"""
                for point in stock.get('turning_points', []):
                    html += f"""
                                        <li>{point}</li>
"""
                html += """
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>
"""
            html += """
                </div>
            </div>
"""
        
        html += """
        </section>
        
        <script>
        function showStockDetail(stockId) {
            document.getElementById(stockId).classList.remove('hidden');
        }
        function hideStockDetail(stockId) {
            document.getElementById(stockId).classList.add('hidden');
        }
        </script>
"""
        return html
    
    def generate_full_page(self, analysis_result: Dict, sectors: List[Dict], recommendations: Dict) -> str:
        """
        フルページを生成（index.html：方向感のナビゲーション専用）
        
        市場判断の文章は表示せず、方向感の分布を俯瞰するナビゲーションページとして機能
        """
        html = self._generate_header()
        
        # 説明文
        html += """
            <div class="mb-8 bg-blue-50 border-l-4 border-blue-500 p-6 rounded-lg">
                <h2 class="text-xl font-bold text-blue-900 mb-2">Market Direction Overview</h2>
                <p class="text-sm text-blue-800">
                    国別・期間別の市場方向感を一目で把握できます。各カードをクリックすると、詳細な判断根拠（チャート・数値・思考ログ）を確認できます。
                </p>
            </div>
"""
        
        # Overviewカード（クリック可能、logsページへリンク）
        html += self.generate_overview_cards(analysis_result)
        
        html += self._generate_footer()
        
        return html
    
    def save_html(self, content: str, filename: str = "index.html"):
        """HTMLファイルを保存"""
        filepath = self.output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"HTMLファイルを保存しました: {filepath}")
    
    def generate_detail_page(self, country_result: Dict, timeframe_code: str, analysis_text: Dict) -> str:
        """詳細ページを生成"""
        country_name = country_result["name"]
        timeframe_name = next(
            (tf['name'] for tf in self.config['timeframes'] if tf['code'] == timeframe_code),
            timeframe_code
        )
        
        html = self._generate_header(f"{country_name} 市場分析 - {timeframe_name}")
        
        html += f"""
            <div class="mb-6">
                <a href="../index.html" class="inline-flex items-center text-blue-600 hover:text-blue-800 font-medium">
                    ← トップページに戻る
                </a>
            </div>
"""
        
        # 前提条件を表示（必須）
        premise = analysis_text.get("premise", analysis_text.get("前提", ""))
        if premise:
            html += f"""
            <section class="bg-green-50 rounded-2xl shadow-md p-6 mb-6 border-l-4 border-green-300">
                <h2 class="text-2xl font-bold text-green-800 mb-4">前提条件</h2>
                <p class="text-green-700 leading-relaxed">{premise}</p>
            </section>
"""
        
        # 新しい形式（LLM結果）を優先表示
        if analysis_text.get("summary") or analysis_text.get("結論"):
            summary = analysis_text.get("summary", analysis_text.get("結論", ""))
            html += f"""
            <section class="bg-white rounded-2xl shadow-md p-6 mb-6">
                <h2 class="text-2xl font-bold text-gray-900 mb-4">市場環境サマリー</h2>
                <p class="text-gray-700 leading-relaxed">{summary}</p>
            </section>
"""
        
        # 主要要因
        key_factors = analysis_text.get("key_factors", [])
        if not key_factors and analysis_text.get("前提") and not premise:
            # 後方互換性：旧形式の前提を主要要因として表示（前提条件として既に表示されていない場合）
            key_factors = [analysis_text["前提"]]
        
        if key_factors:
            html += f"""
            <section class="bg-white rounded-2xl shadow-md p-6 mb-6">
                <h2 class="text-2xl font-bold text-gray-900 mb-4">主要要因</h2>
                <ul class="list-disc list-inside text-gray-700 space-y-2">
"""
            for factor in key_factors:
                html += f"""
                    <li>{factor}</li>
"""
            html += """
                </ul>
            </section>
"""
        
        # リスク
        risks = analysis_text.get("risks", [])
        if not risks and analysis_text.get("最大リスク"):
            risks = [analysis_text["最大リスク"]]
        
        if risks:
            html += f"""
            <section class="bg-red-50 rounded-2xl shadow-md p-6 mb-6 border-l-4 border-red-300">
                <h2 class="text-2xl font-bold text-red-800 mb-4">想定リスク</h2>
                <ul class="list-disc list-inside text-red-700 space-y-2">
"""
            for risk in risks:
                html += f"""
                    <li>{risk}</li>
"""
            html += """
                </ul>
            </section>
"""
        
        # 転換ポイント
        turning_points = analysis_text.get("turning_points", [])
        if not turning_points and analysis_text.get("転換シグナル"):
            turning_points = [analysis_text["転換シグナル"]]
        
        if turning_points:
            html += f"""
            <section class="bg-blue-50 rounded-2xl shadow-md p-6 mb-6 border-l-4 border-blue-300">
                <h2 class="text-2xl font-bold text-blue-800 mb-4">転換ポイント</h2>
                <ul class="list-disc list-inside text-blue-700 space-y-2">
"""
            for point in turning_points:
                html += f"""
                    <li>{point}</li>
"""
            html += """
                </ul>
            </section>
"""
        
        html += self._generate_footer()
        
        return html
    
    def save_detail_page(self, content: str, country_code: str, timeframe_code: str):
        """詳細ページを保存"""
        detail_dir = self.output_dir / "details"
        detail_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"{country_code}-{timeframe_code}.html"
        filepath = detail_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"詳細ページを保存しました: {filepath}")
    
    def _extract_facts(self, data: Dict, analysis: Dict) -> List[Dict]:
        """
        観測事実を抽出（影響度順、数値・状態のみ、主観的表現は禁止）
        
        Returns:
            観測事実のリスト（各要素は{'text': str, 'priority': int, 'source': str, 'release_date': str}）
        """
        facts = []
        
        # 優先順位: 1=金融政策・金利・インフレ, 2=景気指標, 3=株価トレンド, 4=補足的データ
        
        # 1. 金融政策・金利・インフレ関連（最優先）
        financial = data.get("financial", {})
        if financial.get("policy_rate") is not None:
            facts.append({
                'text': f"政策金利は{financial['policy_rate']:.2f}%です",
                'priority': 1,
                'source': self._get_data_source("政策金利"),
                'release_date': self._get_latest_release_date("政策金利")
            })
        if financial.get("long_term_rate") is not None:
            facts.append({
                'text': f"長期金利（10年債）は{financial['long_term_rate']:.2f}%です",
                'priority': 1,
                'source': self._get_data_source("長期金利"),
                'release_date': self._get_latest_release_date("長期金利")
            })
        
        macro = data.get("macro", {})
        if macro.get("CPI") is not None:
            cpi_change = macro.get("CPI_change", 0)
            prev_cpi = macro['CPI'] - cpi_change if cpi_change else None
            if prev_cpi:
                facts.append({
                    'text': f"CPI前年同月比は{macro['CPI']:.2f}%です（前回: {prev_cpi:.2f}%）",
                    'priority': 1,
                    'source': self._get_data_source("CPI"),
                    'release_date': self._get_latest_release_date("CPI")
                })
            else:
                facts.append({
                    'text': f"CPI前年同月比は{macro['CPI']:.2f}%です",
                    'priority': 1,
                    'source': self._get_data_source("CPI"),
                    'release_date': self._get_latest_release_date("CPI")
                })
        
        # 2. 景気指標
        if macro.get("PMI") is not None:
            facts.append({
                'text': f"PMIは{macro['PMI']:.1f}です",
                'priority': 2,
                'source': self._get_data_source("PMI"),
                'release_date': self._get_latest_release_date("PMI")
            })
        if macro.get("employment_rate") is not None:
            facts.append({
                'text': f"雇用率は{macro['employment_rate']:.2f}%です",
                'priority': 2,
                'source': self._get_data_source("雇用"),
                'release_date': self._get_latest_release_date("雇用")
            })
        
        # 3. 株価トレンド・需給・ボラティリティ
        indices = data.get("indices", {})
        if indices:
            for index_code, index_data in indices.items():
                latest_price = index_data.get("latest_price")
                ma20 = index_data.get("ma20")
                ma75 = index_data.get("ma75")
                ma200 = index_data.get("ma200")
                price_vs_ma200 = index_data.get("price_vs_ma200", 0)
                volume_ratio = index_data.get("volume_ratio", 1.0)
                volatility = index_data.get("volatility", 0)
                
                if latest_price and ma200:
                    facts.append({
                        'text': f"{index_code}の最新終値は{latest_price:.2f}です（MA200との乖離: {price_vs_ma200:+.2f}%）",
                        'priority': 3,
                        'source': self._get_data_source(index_code),
                        'release_date': self._get_latest_release_date("株価")
                    })
                
                # 移動平均の順序関係
                if ma20 and ma75 and ma200:
                    if ma20 > ma75 > ma200:
                        facts.append({
                            'text': f"{index_code}の移動平均は20日 > 75日 > 200日の順序です",
                            'priority': 3,
                            'source': self._get_data_source(index_code),
                            'release_date': self._get_latest_release_date("株価")
                        })
                    elif ma20 < ma75 < ma200:
                        facts.append({
                            'text': f"{index_code}の移動平均は20日 < 75日 < 200日の順序です",
                            'priority': 3,
                            'source': self._get_data_source(index_code),
                            'release_date': self._get_latest_release_date("株価")
                        })
                
                # 出来高
                if volume_ratio:
                    facts.append({
                        'text': f"{index_code}の最新出来高は直近30日平均の{volume_ratio:.2f}倍です",
                        'priority': 4,
                        'source': self._get_data_source(index_code),
                        'release_date': self._get_latest_release_date("株価")
                    })
                
                # ボラティリティ
                if volatility:
                    facts.append({
                        'text': f"{index_code}の過去30日のボラティリティ（年率換算）は{volatility:.2f}%です",
                        'priority': 4,
                        'source': self._get_data_source(index_code),
                        'release_date': self._get_latest_release_date("株価")
                    })
        
        # 優先順位でソート
        facts.sort(key=lambda x: x['priority'])
        
        return facts
    
    def _get_latest_release_date(self, indicator: str) -> str:
        """
        指標の最新発表日を取得（簡易版）
        
        Args:
            indicator: 指標名
        
        Returns:
            最新発表日（わかる範囲で）
        """
        # 実際の実装では、データソースから最新発表日を取得する必要がある
        # ここでは簡易的に「最新データ反映」を返す
        if 'CPI' in indicator or 'PMI' in indicator:
            return "最新データ反映"
        elif '金利' in indicator or 'rate' in indicator.lower():
            return "最新データ反映"
        elif '株価' in indicator or 'SPX' in indicator or 'NDX' in indicator or 'N225' in indicator:
            return "最新データ反映"
        else:
            return "最新データ反映"
    
    def _generate_charts_section(self, data: Dict, analysis: Dict, country_code: str, timeframe_code: str) -> str:
        """
        チャートセクションを生成（方向感の根拠）
        
        Args:
            data: 国別データ
            analysis: 分析結果
            country_code: 国コード
            timeframe_code: 期間コード
        
        Returns:
            チャートセクションのHTML
        """
        html = """
            <!-- ② 方向感の根拠（チャート） -->
            <section class="bg-white rounded-2xl shadow-md p-6 mb-6">
                <h2 class="text-2xl font-bold text-gray-900 mb-6">方向感の根拠（チャート）</h2>
                <p class="text-sm text-gray-600 mb-6">以下のチャートは判断の証拠として表示しています。新たな判断を生まない補助情報です。</p>
                
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
"""
        
        # ① 価格トレンドチャート（必須）
        indices = data.get("indices", {})
        if indices:
            first_index = list(indices.values())[0]
            index_code = list(indices.keys())[0]
            index_name = {"SPX": "S&P500", "NDX": "NASDAQ100", "N225": "日経225", "TPX": "TOPIX"}.get(index_code, index_code)
            
            latest_price = first_index.get("latest_price", 0)
            ma20 = first_index.get("ma20", 0)
            ma75 = first_index.get("ma75", 0)
            ma200 = first_index.get("ma200", 0)
            
            # キャプション生成（ルールベース）
            caption = ""
            if latest_price > ma200:
                caption = f"価格は200日移動平均（{ma200:.2f}）を上回って推移しています。"
            elif latest_price < ma200:
                caption = f"価格は200日移動平均（{ma200:.2f}）を下回って推移しています。"
            else:
                caption = f"価格は200日移動平均（{ma200:.2f}）付近で推移しています。"
            
            chart_id = f"priceChart_{country_code}_{timeframe_code}"
            html += f"""
                    <!-- 価格トレンドチャート -->
                    <div class="bg-gray-50 p-4 rounded-lg">
                        <h3 class="text-lg font-semibold text-gray-900 mb-2">{index_name} 価格トレンド</h3>
                        <canvas id="{chart_id}"></canvas>
                        <p class="text-xs text-gray-600 mt-2">{caption}</p>
                    </div>
"""
        
        # ② マクロ指標チャート（期間に応じて）
        macro = data.get("macro", {})
        financial = data.get("financial", {})
        
        if timeframe_code == "short":
            # 短期：金利、CPI
            if financial.get("long_term_rate") is not None:
                rate = financial.get("long_term_rate")
                chart_id = f"rateChart_{country_code}_{timeframe_code}"
                html += f"""
                    <div class="bg-gray-50 p-4 rounded-lg">
                        <h3 class="text-lg font-semibold text-gray-900 mb-2">長期金利（10年債）</h3>
                        <canvas id="{chart_id}"></canvas>
                        <p class="text-xs text-gray-600 mt-2">現在の長期金利は{rate:.2f}%です。</p>
                    </div>
"""
            
            if macro.get("CPI") is not None:
                cpi = macro.get("CPI")
                chart_id = f"cpiChart_{country_code}_{timeframe_code}"
                html += f"""
                    <div class="bg-gray-50 p-4 rounded-lg">
                        <h3 class="text-lg font-semibold text-gray-900 mb-2">CPI（消費者物価指数）</h3>
                        <canvas id="{chart_id}"></canvas>
                        <p class="text-xs text-gray-600 mt-2">CPI前年同月比は{cpi:.2f}%です。</p>
                    </div>
"""
        
        elif timeframe_code == "medium":
            # 中期：PMI、CPI（YoY）
            if macro.get("PMI") is not None:
                pmi = macro.get("PMI")
                caption = "PMIは50を上回っており、景気拡大を示しています。" if pmi > 50 else "PMIは50を下回っており、景気後退を示しています。"
                chart_id = f"pmiChart_{country_code}_{timeframe_code}"
                html += f"""
                    <div class="bg-gray-50 p-4 rounded-lg">
                        <h3 class="text-lg font-semibold text-gray-900 mb-2">PMI（購買担当者景気指数）</h3>
                        <canvas id="{chart_id}"></canvas>
                        <p class="text-xs text-gray-600 mt-2">{caption}</p>
                    </div>
"""
        
        # ③ 構造リスク可視化（簡易）
        if indices:
            first_index = list(indices.values())[0]
            concentration = first_index.get("top_stocks_concentration", 0)
            if concentration > 0:
                chart_id = f"concentrationChart_{country_code}_{timeframe_code}"
                html += f"""
                    <div class="bg-gray-50 p-4 rounded-lg">
                        <h3 class="text-lg font-semibold text-gray-900 mb-2">トップ銘柄集中度</h3>
                        <canvas id="{chart_id}"></canvas>
                        <p class="text-xs text-gray-600 mt-2">上位銘柄の集中度は{concentration*100:.1f}%です。</p>
                    </div>
"""
        
        html += """
                </div>
            </section>
"""
        
        # Chart.jsスクリプトを追加
        html += self._generate_chart_scripts(data, analysis, country_code, timeframe_code)
        
        return html
    
    def _generate_chart_scripts(self, data: Dict, analysis: Dict, country_code: str, timeframe_code: str) -> str:
        """
        チャート用JavaScriptを生成
        
        Args:
            data: 国別データ
            analysis: 分析結果
            country_code: 国コード
            timeframe_code: 期間コード
        
        Returns:
            Chart.jsスクリプトのHTML
        """
        scripts = """
            <script>
                // Chart.jsの設定
                Chart.defaults.font.family = "'Inter', 'Noto Sans JP', sans-serif";
                Chart.defaults.font.size = 12;
"""
        
        # 価格トレンドチャート
        indices = data.get("indices", {})
        if indices:
            first_index = list(indices.values())[0]
            latest_price = first_index.get("latest_price", 0)
            ma20 = first_index.get("ma20", 0)
            ma75 = first_index.get("ma75", 0)
            ma200 = first_index.get("ma200", 0)
            
            chart_id = f"priceChart_{country_code}_{timeframe_code}"
            scripts += f"""
                // 価格トレンドチャート
                const ctx_{chart_id.replace('-', '_')} = document.getElementById('{chart_id}');
                if (ctx_{chart_id.replace('-', '_')}) {{
                    new Chart(ctx_{chart_id.replace('-', '_')}, {{
                        type: 'line',
                        data: {{
                            labels: ['現在'],
                            datasets: [
                                {{
                                    label: '終値',
                                    data: [{latest_price}],
                                    borderColor: 'rgb(59, 130, 246)',
                                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                                    tension: 0.1
                                }},
                                {{
                                    label: 'MA20',
                                    data: [{ma20}],
                                    borderColor: 'rgb(34, 197, 94)',
                                    borderDash: [5, 5],
                                    tension: 0.1
                                }},
                                {{
                                    label: 'MA75',
                                    data: [{ma75}],
                                    borderColor: 'rgb(251, 191, 36)',
                                    borderDash: [5, 5],
                                    tension: 0.1
                                }},
                                {{
                                    label: 'MA200',
                                    data: [{ma200}],
                                    borderColor: 'rgb(239, 68, 68)',
                                    borderDash: [5, 5],
                                    tension: 0.1
                                }}
                            ]
                        }},
                        options: {{
                            responsive: true,
                            maintainAspectRatio: true,
                            plugins: {{
                                legend: {{
                                    display: true,
                                    position: 'top'
                                }}
                            }},
                            scales: {{
                                y: {{
                                    beginAtZero: false
                                }}
                            }}
                        }}
                    }});
                }}
"""
        
        scripts += """
            </script>
"""
        return scripts
    
    def _generate_key_numbers_section(self, data: Dict, analysis: Dict) -> str:
        """
        判断に使った数値セクションを生成
        
        Args:
            data: 国別データ
            analysis: 分析結果
        
        Returns:
            数値セクションのHTML
        """
        html = """
            <!-- ③ 判断に使った数値 -->
            <section class="bg-white rounded-2xl shadow-md p-6 mb-6">
                <h2 class="text-2xl font-bold text-gray-900 mb-6">判断に使った数値</h2>
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
"""
        
        # インデックスデータ
        indices = data.get("indices", {})
        if indices:
            first_index = list(indices.values())[0]
            latest_price = first_index.get("latest_price")
            ma200 = first_index.get("ma200")
            if latest_price and ma200:
                deviation = ((latest_price - ma200) / ma200) * 100
                comment = "上回り" if deviation > 0 else "下回り"
                html += f"""
                    <div class="bg-gray-50 p-3 rounded-lg border-l-4 border-gray-300">
                        <p class="text-xs text-gray-600 mb-1">MA200乖離</p>
                        <p class="text-lg font-bold text-gray-900">{deviation:+.2f}%</p>
                        <p class="text-xs text-gray-500 mt-1">価格がMA200を{comment}ています</p>
                    </div>
"""
        
        # マクロ指標
        macro = data.get("macro", {})
        if macro.get("CPI") is not None:
            cpi = macro.get("CPI")
            cpi_change = macro.get("CPI_change", 0)
            prev_cpi = cpi - cpi_change if cpi_change else None
            comment = "前回比で上昇" if cpi_change > 0 else ("前回比で低下" if cpi_change < 0 else "前回と同水準")
            html += f"""
                    <div class="bg-gray-50 p-3 rounded-lg border-l-4 border-gray-300">
                        <p class="text-xs text-gray-600 mb-1">CPI</p>
                        <p class="text-lg font-bold text-gray-900">{cpi:.2f}%</p>
                        <p class="text-xs text-gray-500 mt-1">{comment if prev_cpi else '前年同月比'}</p>
                    </div>
"""
        
        if macro.get("PMI") is not None:
            pmi = macro.get("PMI")
            comment = "景気拡大を示す" if pmi > 50 else "景気後退を示す"
            html += f"""
                    <div class="bg-gray-50 p-3 rounded-lg border-l-4 border-gray-300">
                        <p class="text-xs text-gray-600 mb-1">PMI</p>
                        <p class="text-lg font-bold text-gray-900">{pmi:.1f}</p>
                        <p class="text-xs text-gray-500 mt-1">{comment}</p>
                    </div>
"""
        
        # 金融指標
        financial = data.get("financial", {})
        if financial.get("long_term_rate") is not None:
            rate = financial.get("long_term_rate")
            comment = "高水準" if rate > 4.0 else ("低水準" if rate < 2.0 else "中程度")
            html += f"""
                    <div class="bg-gray-50 p-3 rounded-lg border-l-4 border-gray-300">
                        <p class="text-xs text-gray-600 mb-1">10年金利</p>
                        <p class="text-lg font-bold text-gray-900">{rate:.2f}%</p>
                        <p class="text-xs text-gray-500 mt-1">{comment}の水準</p>
                    </div>
"""
        
        if financial.get("policy_rate") is not None:
            policy_rate = financial.get("policy_rate")
            comment = "高水準" if policy_rate > 3.0 else ("低水準" if policy_rate < 1.0 else "中程度")
            html += f"""
                    <div class="bg-gray-50 p-3 rounded-lg border-l-4 border-gray-300">
                        <p class="text-xs text-gray-600 mb-1">政策金利</p>
                        <p class="text-lg font-bold text-gray-900">{policy_rate:.2f}%</p>
                        <p class="text-xs text-gray-500 mt-1">{comment}の水準</p>
                    </div>
"""
        
        html += """
                </div>
            </section>
"""
        return html
    
    def _generate_policy_background_section(self, data: Dict, country_code: str) -> str:
        """
        政策・構造的背景セクションを生成（要約）
        
        Args:
            data: 国別データ
            country_code: 国コード
        
        Returns:
            政策・構造的背景セクションのHTML
        """
        html = """
            <!-- ①-2 現在の政策・構造的論点（要約） -->
            <section class="bg-white rounded-2xl shadow-md p-6 mb-6">
                <h2 class="text-2xl font-bold text-gray-900 mb-4">現在の政策・構造的論点（要約）</h2>
                <p class="text-sm text-gray-600 mb-4">市場判断の前提となる大きな論点を要約します。</p>
                <div class="bg-purple-50 p-4 rounded-lg border-l-4 border-purple-400">
"""
        
        # 国別の背景情報を生成（最大3点・短文）
        background_points = self._get_policy_background_points(data, country_code)
        
        if background_points:
            html += """
                    <ul class="list-disc list-inside text-gray-800 space-y-2">
"""
            for point in background_points:
                html += f"""
                        <li>{point}</li>
"""
            html += """
                    </ul>
"""
        else:
            html += """
                    <p class="text-gray-800">データに基づく判断材料を提示しています。</p>
"""
        
        html += """
                </div>
            </section>
"""
        return html
    
    def _get_policy_background_points(self, data: Dict, country_code: str) -> List[str]:
        """
        政策・構造的背景のポイントを取得（最大3点・短文）
        
        Args:
            data: 国別データ
            country_code: 国コード
        
        Returns:
            背景ポイントのリスト
        """
        points = []
        
        # 国別の背景情報（現状整理のみ、評価は禁止）
        if country_code == "US":
            macro = data.get("macro", {})
            financial = data.get("financial", {})
            cpi = macro.get("CPI")
            policy_rate = financial.get("policy_rate")
            
            # 課題
            if cpi is not None:
                points.append("課題：インフレ沈静化と景気減速の両立")
            
            # 政策スタンス
            if policy_rate is not None:
                points.append("政策スタンス：FRBはデータ次第で慎重姿勢を維持")
            
            # 注目指標
            points.append("注目指標：CPI、雇用統計、政策金利見通し")
        
        elif country_code == "JP":
            macro = data.get("macro", {})
            financial = data.get("financial", {})
            cpi = macro.get("CPI")
            policy_rate = financial.get("policy_rate")
            
            # 課題
            if cpi is not None:
                points.append("課題：物価上昇率の持続可能性と金融政策の正常化")
            
            # 政策スタンス
            if policy_rate is not None:
                points.append("政策スタンス：日銀は金融緩和の出口戦略を検討")
            
            # 注目指標
            points.append("注目指標：CPI、賃金動向、金融政策決定会合")
        
        else:
            # その他の国
            points.append("課題：インフレ・景気・金融政策のバランス")
            points.append("政策スタンス：中央銀行はデータに基づく判断を継続")
            points.append("注目指標：主要経済指標と金融政策動向")
        
        return points[:3]  # 最大3点
    
    def _generate_why_section(self, analysis: Dict, data: Dict) -> str:
        """
        この見方が成り立つ理由（Why）セクションを生成（具体化）
        
        Args:
            analysis: 分析結果
            data: 国別データ
        
        Returns:
            WhyセクションのHTML
        """
        html = """
            <!-- ② この見方が成り立つ理由（Why） -->
            <section class="bg-white rounded-2xl shadow-md p-6 mb-6">
                <h2 class="text-2xl font-bold text-gray-900 mb-4">この見方が成り立つ理由</h2>
                <p class="text-sm text-gray-600 mb-4">なぜこの方向なのか、具体的な指標・事象とともに説明します。</p>
                <div class="bg-blue-50 p-4 rounded-lg border-l-4 border-blue-400">
                    <ul class="list-disc list-inside text-gray-800 space-y-3">
"""
        
        # key_factorsから理由を抽出し、具体化
        key_factors = analysis.get('key_factors', [])
        rule_components = analysis.get('rule_based_components', {})
        
        # 各要因を具体化
        if key_factors:
            for factor in key_factors[:3]:
                # 既存の要因を具体化（分類＋具体指標・事象＋状態）
                concrete_reason = self._concretize_reason(factor, data, rule_components)
                html += f"""
                        <li class="mb-2">{concrete_reason}</li>
"""
        else:
            # データから理由を生成
            concrete_reasons = self._generate_concrete_reasons_from_data(data, rule_components)
            for reason in concrete_reasons[:3]:
                html += f"""
                        <li class="mb-2">{reason}</li>
"""
        
        html += """
                    </ul>
                </div>
            </section>
"""
        return html
    
    def _concretize_reason(self, factor: str, data: Dict, rule_components: Dict) -> str:
        """
        理由を具体化（分類＋具体指標・事象＋状態）
        
        Args:
            factor: 要因（抽象的な表現）
            data: 国別データ
            rule_components: ルールベース指標
        
        Returns:
            具体化された理由
        """
        # 既存の要因を具体化（新しい評価は追加しない）
        factor_lower = factor.lower()
        
        # テクニカル関連
        if 'テクニカル' in factor or 'トレンド' in factor or '移動平均' in factor:
            indices = data.get("indices", {})
            if indices:
                first_index = list(indices.values())[0]
                latest_price = first_index.get("latest_price")
                ma20 = first_index.get("ma20")
                ma75 = first_index.get("ma75")
                index_name = {"SPX": "S&P500", "NDX": "NASDAQ100", "N225": "日経225", "TPX": "TOPIX"}.get(
                    list(indices.keys())[0], list(indices.keys())[0]
                )
                if latest_price and ma20 and ma75:
                    if latest_price > ma20 and latest_price > ma75:
                        return f"テクニカル：{index_name}が20日・75日移動平均を上回って推移しており、短期的なトレンドが維持されている"
                    elif latest_price < ma20 and latest_price < ma75:
                        return f"テクニカル：{index_name}が20日・75日移動平均を下回って推移しており、短期的なトレンドが弱い"
            return f"テクニカル：{factor}"
        
        # マクロ関連
        elif 'マクロ' in factor or 'インフレ' in factor or 'CPI' in factor:
            macro = data.get("macro", {})
            cpi = macro.get("CPI")
            cpi_change = macro.get("CPI_change", 0)
            if cpi is not None:
                if cpi_change < 0:
                    return f"マクロ：CPIの低下ペースが続いており、インフレ沈静化が進んでいる"
                elif cpi_change > 0:
                    return f"マクロ：CPIの低下ペースが鈍化しており、インフレ沈静化が一服している兆しが見られる"
                else:
                    return f"マクロ：CPI前年同月比は{cpi:.2f}%で推移しており、インフレ動向が注視されている"
            return f"マクロ：{factor}"
        
        # 金融政策関連
        elif '金融' in factor or '金利' in factor or '政策' in factor:
            financial = data.get("financial", {})
            policy_rate = financial.get("policy_rate")
            long_term_rate = financial.get("long_term_rate")
            country_code = data.get("code", "")
            central_bank = {"US": "FRB", "JP": "日銀"}.get(country_code, "中央銀行")
            
            if policy_rate is not None or long_term_rate is not None:
                rate_text = ""
                if policy_rate is not None:
                    rate_text += f"政策金利{policy_rate:.2f}%"
                if long_term_rate is not None:
                    if rate_text:
                        rate_text += f"、長期金利{long_term_rate:.2f}%"
                    else:
                        rate_text = f"長期金利{long_term_rate:.2f}%"
                
                return f"金融政策：{central_bank}が{rate_text}の水準を維持しており、金融緩和期待が後退している"
            return f"金融政策：{factor}"
        
        # その他は既存の表現をそのまま使用
        return factor
    
    def _generate_concrete_reasons_from_data(self, data: Dict, rule_components: Dict) -> List[str]:
        """
        データから具体的な理由を生成
        
        Args:
            data: 国別データ
            rule_components: ルールベース指標
        
        Returns:
            具体化された理由のリスト
        """
        reasons = []
        
        # テクニカル
        indices = data.get("indices", {})
        if indices:
            first_index = list(indices.values())[0]
            latest_price = first_index.get("latest_price")
            ma20 = first_index.get("ma20")
            ma75 = first_index.get("ma75")
            index_name = {"SPX": "S&P500", "NDX": "NASDAQ100", "N225": "日経225", "TPX": "TOPIX"}.get(
                list(indices.keys())[0], list(indices.keys())[0]
            )
            if latest_price and ma20 and ma75:
                if latest_price > ma20 and latest_price > ma75:
                    reasons.append(f"テクニカル：{index_name}が20日・75日移動平均を上回って推移しており、短期的なトレンドが維持されている")
                elif latest_price < ma20 and latest_price < ma75:
                    reasons.append(f"テクニカル：{index_name}が20日・75日移動平均を下回って推移しており、短期的なトレンドが弱い")
        
        # マクロ
        macro = data.get("macro", {})
        cpi = macro.get("CPI")
        if cpi is not None:
            reasons.append(f"マクロ：CPI前年同月比は{cpi:.2f}%で推移しており、インフレ動向が注視されている")
        
        # 金融政策
        financial = data.get("financial", {})
        policy_rate = financial.get("policy_rate")
        country_code = data.get("code", "")
        central_bank = {"US": "FRB", "JP": "日銀"}.get(country_code, "中央銀行")
        if policy_rate is not None:
            reasons.append(f"金融政策：{central_bank}が政策金利{policy_rate:.2f}%の水準を維持しており、金融政策の方向性が注視されている")
        
        return reasons
    
    def _generate_facts_with_interpretation_section(self, data: Dict, analysis: Dict) -> str:
        """
        観測事実 × 解釈（セット表示、折りたたみ可能）セクションを生成
        
        Args:
            data: 国別データ
            analysis: 分析結果
        
        Returns:
            観測事実×解釈セクションのHTML
        """
        html = """
            <!-- ③ 観測事実 × 解釈（セット表示） -->
            <section class="bg-white rounded-2xl shadow-md p-6 mb-6">
                <h2 class="text-2xl font-bold text-gray-900 mb-4">観測事実と解釈</h2>
                <p class="text-sm text-gray-600 mb-4">観測事実とその解釈をセットで表示します。クリックで詳細を展開できます。</p>
                <div class="space-y-4">
"""
        
        # 観測事実を抽出（影響度順）
        facts = self._extract_facts(data, analysis)
        
        # 主要な観測事実を優先表示（上位3件）、その他は折りたたみ
        important_facts = facts[:3] if len(facts) > 3 else facts
        other_facts = facts[3:] if len(facts) > 3 else []
        
        # 主要な観測事実をカード化
        for fact_data in important_facts:
            fact_text = fact_data['text']
            fact_source = fact_data.get('source', '')
            fact_release_date = fact_data.get('release_date', '')
            # 解釈を取得（key_factorsから関連するものを抽出）
            interpretation = self._get_interpretation_for_fact(fact_text, analysis)
            
            html += f"""
                    <div class="bg-gray-50 rounded-lg border-l-4 border-gray-300 p-4">
                        <div class="flex items-start justify-between">
                            <div class="flex-1">
                                <h3 class="text-sm font-semibold text-gray-700 mb-2">観測事実</h3>
                                <p class="text-sm text-gray-800 mb-2">{fact_text}</p>
                                <div class="flex items-center gap-3 text-xs text-gray-500">
                                    <span>データ取得元: {fact_source}</span>
                                    {f'<span>最新発表日: {fact_release_date}</span>' if fact_release_date else ''}
                                </div>
"""
            
            if interpretation:
                html += f"""
                                <div class="mt-3 pt-3 border-t border-gray-200">
                                    <h4 class="text-sm font-semibold text-blue-700 mb-1">解釈</h4>
                                    <p class="text-sm text-blue-800">{interpretation}</p>
                                </div>
"""
            
            html += """
                            </div>
                        </div>
                    </div>
"""
        
        # その他の観測事実を折りたたみ
        if other_facts:
            html += f"""
                    <details class="bg-gray-50 rounded-lg border-l-4 border-gray-200 p-4">
                        <summary class="cursor-pointer text-sm font-semibold text-gray-700 mb-2">
                            その他の観測事実（{len(other_facts)}件）を表示
                        </summary>
                        <div class="mt-3 space-y-3">
"""
            for fact_data in other_facts:
                fact_text = fact_data['text']
                fact_source = fact_data.get('source', '')
                fact_release_date = fact_data.get('release_date', '')
                interpretation = self._get_interpretation_for_fact(fact_text, analysis)
                html += f"""
                            <div class="bg-white p-3 rounded border-l-2 border-gray-300">
                                <p class="text-sm text-gray-800 mb-1">{fact_text}</p>
                                <div class="flex items-center gap-3 text-xs text-gray-500 mb-2">
                                    <span>データ取得元: {fact_source}</span>
                                    {f'<span>最新発表日: {fact_release_date}</span>' if fact_release_date else ''}
                                </div>
"""
                if interpretation:
                    html += f"""
                                <p class="text-xs text-blue-700 mt-2">解釈: {interpretation}</p>
"""
                html += """
                            </div>
"""
            html += """
                        </div>
                    </details>
"""
        
        html += """
                </div>
            </section>
"""
        return html
    
    def _get_interpretation_for_fact(self, fact: str, analysis: Dict) -> str:
        """
        観測事実に対する解釈を取得
        
        Args:
            fact: 観測事実
            analysis: 分析結果
        
        Returns:
            解釈文（なければ空文字列）
        """
        # key_factorsから関連する解釈を抽出
        key_factors = analysis.get('key_factors', [])
        summary = analysis.get('summary', '')
        
        # 簡易的なマッチング（実際の実装ではより詳細なロジックが必要）
        if 'CPI' in fact or 'インフレ' in fact:
            for factor in key_factors:
                if 'インフレ' in factor or 'CPI' in factor:
                    return factor
        elif '金利' in fact or 'rate' in fact.lower() or '政策' in fact:
            for factor in key_factors:
                if '金利' in factor or '金融' in factor or '政策' in factor:
                    return factor
        elif '移動平均' in fact or 'MA' in fact or 'SPX' in fact or 'NDX' in fact or 'N225' in fact:
            for factor in key_factors:
                if 'テクニカル' in factor or 'トレンド' in factor:
                    return factor
        elif 'PMI' in fact:
            for factor in key_factors:
                if 'PMI' in factor or '景気' in factor:
                    return factor
        
        # マッチしない場合はsummaryから抽出
        if summary and len(summary) < 100:
            return summary
        
        return ""
    
    def _get_data_source(self, fact: str) -> str:
        """
        観測事実のデータ取得元を取得
        
        Args:
            fact: 観測事実
        
        Returns:
            データ取得元名
        """
        if 'CPI' in fact or 'PMI' in fact:
            return "FRED / 各国統計機関"
        elif '金利' in fact or 'rate' in fact.lower():
            return "FRED / 各国中央銀行"
        elif '移動平均' in fact or 'MA' in fact or 'SPX' in fact or 'NDX' in fact or 'N225' in fact or 'TPX' in fact:
            return "Yahoo Finance"
        elif '雇用' in fact or 'employment' in fact.lower():
            return "各国統計機関"
        else:
            return "各種データソース"
    
    def _generate_turning_points_by_direction(self, data: Dict, analysis: Dict) -> str:
        """
        見方が変わる条件を上方向/下方向に分けて表示
        
        Args:
            data: 国別データ
            analysis: 分析結果
        
        Returns:
            転換条件セクションのHTML
        """
        html = """
            <!-- ④ 見方が変わる条件（方向明示） -->
            <section class="bg-white rounded-2xl shadow-md p-6 mb-6">
                <h2 class="text-2xl font-bold text-gray-900 mb-4">見方が変わる条件</h2>
                <p class="text-sm text-gray-600 mb-4">判断が変わる可能性のある条件を、上方向と下方向に分けて示します。</p>
"""
        
        # 現在のスコアを取得
        score = analysis.get('score', 0)
        
        # 転換条件を分類
        turning_points = analysis.get('turning_points', [])
        upward_conditions = []  # 上方向への転換条件
        downward_conditions = []  # 下方向への転換条件
        
        # turning_pointsを上方向/下方向に分類
        for point in turning_points:
            point_text = str(point)
            # 簡易的な分類（実際の実装ではより詳細なロジックが必要）
            if '上回' in point_text or '上昇' in point_text or '緩和' in point_text or '鈍化' in point_text:
                upward_conditions.append({
                    'text': point_text,
                    'indicator': self._extract_indicator_name(point_text),
                    'next_release': self._get_next_release_date(point_text)
                })
            elif '下回' in point_text or '下降' in point_text or '引き締め' in point_text or '加速' in point_text or '急騰' in point_text:
                downward_conditions.append({
                    'text': point_text,
                    'indicator': self._extract_indicator_name(point_text),
                    'next_release': self._get_next_release_date(point_text)
                })
            else:
                # 分類できない場合は、スコアに基づいて分類
                if score < 0:
                    upward_conditions.append({
                        'text': point_text,
                        'indicator': self._extract_indicator_name(point_text),
                        'next_release': self._get_next_release_date(point_text)
                    })
                else:
                    downward_conditions.append({
                        'text': point_text,
                        'indicator': self._extract_indicator_name(point_text),
                        'next_release': self._get_next_release_date(point_text)
                    })
        
        # turning_pointsがない場合は、データから生成
        if not turning_points:
            upward_conditions = self._generate_upward_conditions(data, analysis)
            downward_conditions = self._generate_downward_conditions(data, analysis)
        
        # 下方向リスク
        html += """
                <div class="mb-6">
                    <h3 class="text-lg font-semibold text-red-800 mb-3 flex items-center">
                        <span class="mr-2">📉</span>
                        下方向への転換条件
                    </h3>
                    <div class="space-y-2">
"""
        if downward_conditions:
            for condition in downward_conditions:
                html += f"""
                        <div class="flex items-start p-3 bg-red-50 border-l-4 border-red-200 rounded-r-lg">
                            <span class="mr-2 text-lg">🚩</span>
                            <div class="flex-1">
                                <p class="text-sm text-gray-800 font-medium mb-1">{condition['text']}</p>
"""
                # なぜ重要か
                importance = self._get_importance_reason(condition['text'], condition.get('indicator', ''))
                if importance:
                    html += f"""
                                <p class="text-xs text-gray-600 mb-1">→ {importance}</p>
"""
                # 対象指標と次回発表日（必ず記載）
                indicator = condition.get('indicator', self._extract_indicator_name(condition['text']))
                next_release = condition.get('next_release') or self._get_next_release_date(condition['text'])
                html += f"""
                                <p class="text-xs text-gray-500 mt-1">
                                    対象指標: {indicator} | 次回発表予定: {next_release}
                                </p>
"""
                html += """
                            </div>
                        </div>
"""
        else:
            html += """
                        <p class="text-sm text-gray-600">現在、下方向への転換条件は特に見当たりません。</p>
"""
        html += """
                    </div>
                </div>
"""
        
        # 上方向シナリオ
        html += """
                <div class="mb-6">
                    <h3 class="text-lg font-semibold text-green-800 mb-3 flex items-center">
                        <span class="mr-2">📈</span>
                        上方向への転換条件
                    </h3>
                    <div class="space-y-2">
"""
        if upward_conditions:
            for condition in upward_conditions:
                html += f"""
                        <div class="flex items-start p-3 bg-green-50 border-l-4 border-green-200 rounded-r-lg">
                            <span class="mr-2 text-lg">🚩</span>
                            <div class="flex-1">
                                <p class="text-sm text-gray-800 font-medium mb-1">{condition['text']}</p>
"""
                # なぜ重要か
                importance = self._get_importance_reason(condition['text'], condition.get('indicator', ''))
                if importance:
                    html += f"""
                                <p class="text-xs text-gray-600 mb-1">→ {importance}</p>
"""
                # 対象指標と次回発表日（必ず記載）
                indicator = condition.get('indicator', self._extract_indicator_name(condition['text']))
                next_release = condition.get('next_release') or self._get_next_release_date(condition['text'])
                html += f"""
                                <p class="text-xs text-gray-500 mt-1">
                                    対象指標: {indicator} | 次回発表予定: {next_release}
                                </p>
"""
                html += """
                            </div>
                        </div>
"""
        else:
            html += """
                        <p class="text-sm text-gray-600">現在、上方向への転換条件は特に見当たりません。</p>
"""
        html += """
                    </div>
                </div>
            </section>
"""
        return html
    
    def _generate_upward_conditions(self, data: Dict, analysis: Dict) -> List[Dict]:
        """
        上方向への転換条件を生成
        
        Args:
            data: 国別データ
            analysis: 分析結果
        
        Returns:
            上方向転換条件のリスト
        """
        conditions = []
        indices = data.get("indices", {})
        macro = data.get("macro", {})
        
        if indices:
            first_index = list(indices.values())[0]
            ma200 = first_index.get("ma200")
            latest_price = first_index.get("latest_price")
            
            if ma200 and latest_price and latest_price < ma200:
                conditions.append({
                    'text': f'終値ベースで200日移動平均（{ma200:.2f}）を3日連続で上回った場合、方向転換の可能性があります',
                    'indicator': '価格指数',
                    'next_release': None
                })
        
        if macro.get("CPI") is not None:
            conditions.append({
                'text': 'インフレ再鈍化の確認があった場合、金融緩和期待の再点火の可能性があります',
                'indicator': 'CPI',
                'next_release': '次回発表予定日を確認'
            })
        
        return conditions
    
    def _generate_downward_conditions(self, data: Dict, analysis: Dict) -> List[Dict]:
        """
        下方向への転換条件を生成
        
        Args:
            data: 国別データ
            analysis: 分析結果
        
        Returns:
            下方向転換条件のリスト
        """
        conditions = []
        indices = data.get("indices", {})
        macro = data.get("macro", {})
        financial = data.get("financial", {})
        
        if indices:
            first_index = list(indices.values())[0]
            ma200 = first_index.get("ma200")
            latest_price = first_index.get("latest_price")
            
            if ma200 and latest_price and latest_price > ma200:
                conditions.append({
                    'text': f'終値ベースで200日移動平均（{ma200:.2f}）を3日連続で下回った場合、方向転換の可能性があります',
                    'indicator': '価格指数',
                    'next_release': '常時更新（市場データ）'
                })
        
        if macro.get("CPI") is not None:
            conditions.append({
                'text': 'CPI前年比が再加速した場合、金融引き締め期待が高まる可能性があります',
                'indicator': 'CPI',
                'next_release': '次回：今月下旬予定（米国CPI）'
            })
        
        if financial.get("long_term_rate") is not None:
            conditions.append({
                'text': '長期金利が急騰した場合、株式市場への圧力が高まる可能性があります',
                'indicator': '長期金利',
                'next_release': '常時更新（市場データ）'
            })
        
        return conditions
    
    def _extract_indicator_name(self, text: str) -> str:
        """
        転換条件から指標名を抽出
        
        Args:
            text: 転換条件のテキスト
        
        Returns:
            指標名
        """
        if 'CPI' in text or 'インフレ' in text:
            return 'CPI'
        elif 'PMI' in text:
            return 'PMI'
        elif '金利' in text or 'rate' in text.lower():
            return '長期金利'
        elif '移動平均' in text or 'MA' in text:
            return '価格指数'
        else:
            return '各種指標'
    
    def _get_importance_reason(self, text: str, indicator: str) -> str:
        """
        転換条件の重要性理由を取得
        
        Args:
            text: 転換条件のテキスト
            indicator: 指標名
        
        Returns:
            重要性理由
        """
        if 'CPI' in text or 'インフレ' in text:
            return "インフレ沈静化前提が崩れるため"
        elif '金利' in text or '政策金利' in text:
            return "金融政策の方向性が変わるため"
        elif '長期金利' in text or '10年債' in text:
            return "株式市場への圧力が高まるため"
        elif '移動平均' in text or 'MA' in text or '株価' in text:
            return "トレンド転換のシグナルとなるため"
        elif 'PMI' in text:
            return "景気動向の先行指標となるため"
        else:
            return "市場判断の前提が変わるため"
    
    def _get_next_release_date(self, text: str) -> str:
        """
        転換条件から次回発表予定日を取得（必ず記載）
        
        Args:
            text: 転換条件のテキスト
        
        Returns:
            次回発表予定日（わかる範囲で、必ず記載）
        """
        # 指標ごとに次回発表予定日を返す（概算表記でも可）
        if 'CPI' in text or 'インフレ' in text:
            # CPIは通常月次で発表（米国は中旬、日本は下旬）
            return '次回：今月下旬予定（米国CPI）'
        elif 'PMI' in text:
            # PMIは通常月初に発表
            return '次回：来月初旬予定（PMI）'
        elif '金利' in text or '政策金利' in text:
            # 政策金利はFOMC・日銀金融政策決定会合で決定
            return '次回：FOMC・日銀会合日程を確認'
        elif '長期金利' in text or '10年債' in text:
            # 長期金利は常時更新
            return '常時更新（市場データ）'
        elif '移動平均' in text or 'MA' in text or '株価' in text:
            # 株価は常時更新
            return '常時更新（市場データ）'
        else:
            # 不明な場合は概算表記
            return '次回発表予定日を確認'
    
    def generate_thought_log(self, country_code: str, timeframe_code: str, data: Dict, analysis: Dict) -> str:
        """思考ログを生成（4ブロック構成：観測事実・解釈・前提・転換シグナル）"""
        date_str = datetime.now().strftime("%Y年%m月%d日 %H:%M")
        
        country_name = data.get("name", country_code)
        timeframe_name = next(
            (tf['name'] for tf in self.config['timeframes'] if tf['code'] == timeframe_code),
            timeframe_code
        )
        
        html = self._generate_header(f"思考ログ: {country_name} - {timeframe_name}", include_charts=True)
        
        html += f"""
            <div class="mb-6">
                <a href="../index.html" class="inline-flex items-center text-blue-600 hover:text-blue-800 font-medium">
                    ← トップページに戻る
                </a>
            </div>
"""
        
        # ① 結論（Market View）
        direction_label = analysis.get("direction_label", analysis.get("label", "中立"))
        summary = analysis.get("summary", "")
        html += self._generate_conclusion_block(country_name, timeframe_name, direction_label, summary)
        
        # ①-2 政策・構造的背景（要約）
        html += self._generate_policy_background_section(data, country_code)
        
        # ② この見方が成り立つ理由（Why）
        html += self._generate_why_section(analysis, data)
        
        # ③ 観測事実 × 解釈（セット表示、折りたたみ可能）
        html += self._generate_facts_with_interpretation_section(data, analysis)
        
        # ④ 見方が変わる条件（方向明示）
        html += self._generate_turning_points_by_direction(data, analysis)
        
        # チャートセクション（補助として）
        html += self._generate_charts_section(data, analysis, country_code, timeframe_code)
        
        # 参考情報
        html += """
                <!-- 参考情報 -->
                <div class="mt-8 pt-6 border-t border-gray-200">
                    <h3 class="text-lg font-semibold text-gray-800 mb-4">参考情報</h3>
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
"""
        
        # ルールベース指標を参考情報として表示
        rule_components = analysis.get('rule_based_components', {})
        if rule_components:
            # スコアを取得（新しい形式: {"score": float, "state": str} または 古い形式: float）
            def get_score(component):
                if isinstance(component, dict):
                    return component.get('score', 0)
                return component if isinstance(component, (int, float)) else 0
            
            macro_score = get_score(rule_components.get('macro', 0))
            financial_score = get_score(rule_components.get('financial', 0))
            technical_score = get_score(rule_components.get('technical', 0))
            structural_score = get_score(rule_components.get('structural', 0))
            
            html += f"""
                        <div class="bg-gray-50 p-3 rounded-lg">
                            <p class="text-xs text-gray-600 mb-1">マクロ指標スコア</p>
                            <p class="text-lg font-bold text-gray-900">{macro_score:.2f}</p>
                        </div>
                        <div class="bg-gray-50 p-3 rounded-lg">
                            <p class="text-xs text-gray-600 mb-1">金融指標スコア</p>
                            <p class="text-lg font-bold text-gray-900">{financial_score:.2f}</p>
                        </div>
                        <div class="bg-gray-50 p-3 rounded-lg">
                            <p class="text-xs text-gray-600 mb-1">テクニカル指標スコア</p>
                            <p class="text-lg font-bold text-gray-900">{technical_score:.2f}</p>
                        </div>
                        <div class="bg-gray-50 p-3 rounded-lg">
                            <p class="text-xs text-gray-600 mb-1">構造的指標スコア</p>
                            <p class="text-lg font-bold text-gray-900">{structural_score:.2f}</p>
                        </div>
"""
        
        direction_label = analysis.get('direction_label', analysis.get('label', '中立'))
        score = analysis.get('score', 0)
        html += f"""
                    </div>
                    <div class="mt-4 p-4 bg-blue-50 rounded-lg">
                        <p class="text-sm text-blue-600 mb-1">総合スコア（参考）</p>
                        <p class="text-2xl font-bold text-blue-800">{score} ({direction_label})</p>
                        <p class="text-xs text-blue-600 mt-2">※このスコアは判断材料の一つであり、投資判断ではありません。</p>
                    </div>
                </div>
            </section>
"""
        
        html += self._generate_footer()
        
        return html
    
    def save_thought_log(self, content: str, country_code: str, timeframe_code: str):
        """思考ログを保存"""
        log_dir = self.output_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"{country_code}-{timeframe_code}.html"
        filepath = log_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"思考ログを保存しました: {filepath}")


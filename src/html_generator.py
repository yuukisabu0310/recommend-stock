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
    
    def _generate_header(self, title: str = "株式市場分析レポート") -> str:
        """HTMLヘッダーを生成"""
        date_str = datetime.now().strftime("%Y年%m月%d日 %H:%M")
        return f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
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
                <p class="text-sm text-gray-600">
                    <strong>免責事項</strong>: 本レポートは研究用途であり、投資助言や売買指示を目的としたものではありません。投資判断は自己責任で行ってください。
                </p>
            </div>
        </footer>
    </div>
</body>
</html>"""
    
    def generate_overview_cards(self, analysis_result: Dict) -> str:
        """Overviewカードを生成"""
        countries = self.config['countries']
        timeframes = self.config['timeframes']
        overview = analysis_result.get("overview", {})
        
        html = """
        <!-- Market Direction Overview -->
        <section class="mb-12">
            <h2 class="text-2xl font-bold text-gray-900 mb-6">Market Direction Overview</h2>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
"""
        
        for country_config in countries:
            country_code = country_config['code']
            country_name = country_config['name']
            directions = overview.get(country_code, {})
            
            html += f"""
                <div class="bg-white rounded-2xl shadow-md p-6 card">
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
                
                style = self._get_score_style(score)
                risk_icon = "⚠️" if has_risk else ""
                
                html += f"""
                        <div class="border-l-4 {style['border']} pl-3 py-2">
                            <div class="flex items-center justify-between">
                                <span class="text-sm font-medium text-gray-600">{timeframe_name}</span>
                                <a href="./details/{country_code}-{timeframe_code}.html" 
                                   class="inline-flex items-center px-3 py-1 rounded-lg {style['bg']} {style['text']} text-sm font-medium hover:opacity-80 transition">
                                    {label} {risk_icon}
                                </a>
                            </div>
                        </div>
"""
            
            html += """
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
            label = direction.get("label", "中立")
            has_risk = direction.get("has_risk", False)
            
            style = self._get_score_style(score)
            risk_badge = '<span class="ml-2 text-red-600">⚠️ リスクあり</span>' if has_risk else ''
            
            analysis_text = country_result.get("analysis", {}).get(timeframe_code, {})
            
            html += f"""
            <div class="bg-white rounded-2xl shadow-md p-6 mb-6 card">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-xl font-semibold text-gray-900">{timeframe_name}</h3>
                    <span class="inline-flex items-center px-4 py-2 rounded-lg {style['bg']} {style['text']} font-medium">
                        {label}{risk_badge}
                    </span>
                </div>
"""
            
            if analysis_text.get("結論"):
                html += f"""
                <div class="mb-4">
                    <h4 class="text-lg font-semibold text-gray-800 mb-2">結論</h4>
                    <p class="text-gray-700 leading-relaxed">{analysis_text['結論']}</p>
                </div>
"""
            
            if analysis_text.get("前提"):
                html += f"""
                <div class="mb-4">
                    <h4 class="text-lg font-semibold text-gray-800 mb-2">前提</h4>
                    <p class="text-gray-700 leading-relaxed">{analysis_text['前提']}</p>
                </div>
"""
            
            if analysis_text.get("最大リスク"):
                html += f"""
                <div class="mb-4 p-4 bg-red-50 rounded-lg border-l-4 border-red-300">
                    <h4 class="text-lg font-semibold text-red-800 mb-2">最大リスク</h4>
                    <p class="text-red-700 leading-relaxed">{analysis_text['最大リスク']}</p>
                </div>
"""
            
            if analysis_text.get("転換シグナル"):
                html += f"""
                <div class="mb-4 p-4 bg-blue-50 rounded-lg border-l-4 border-blue-300">
                    <h4 class="text-lg font-semibold text-blue-800 mb-2">転換シグナル</h4>
                    <p class="text-blue-700 leading-relaxed">{analysis_text['転換シグナル']}</p>
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
        """銘柄推奨セクションを生成"""
        if not recommendations:
            return ""
        
        html = """
        <!-- おすすめ銘柄 -->
        <section class="mb-12">
            <h2 class="text-2xl font-bold text-gray-900 mb-6">おすすめ銘柄</h2>
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
                html += f"""
                    <div class="bg-white rounded-2xl shadow-md p-6 card">
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
                                <span class="font-medium text-gray-600">投資期間:</span>
                                <span class="text-gray-700 ml-2">{stock.get('timeframe', '中期')}</span>
                            </div>
                            <div>
                                <span class="font-medium text-gray-600">割安度:</span>
                                <span class="text-gray-700 ml-2">{stock.get('value_rating', '評価なし')}</span>
                            </div>
                            <div class="pt-2 border-t">
                                <span class="font-medium text-gray-600">注目理由:</span>
                                <p class="text-gray-700 mt-1">{stock.get('reason', '')}</p>
                            </div>
                            <div>
                                <span class="font-medium text-gray-600">前提条件:</span>
                                <p class="text-gray-700 mt-1">{stock.get('precondition', '')}</p>
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
                html += f"""
                    <div class="bg-white rounded-2xl shadow-md p-6 card">
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
                                <span class="font-medium text-gray-600">投資期間:</span>
                                <span class="text-gray-700 ml-2">{stock.get('timeframe', '中期')}</span>
                            </div>
                            <div>
                                <span class="font-medium text-gray-600">割安度:</span>
                                <span class="text-gray-700 ml-2">{stock.get('value_rating', '評価なし')}</span>
                            </div>
                            <div class="pt-2 border-t">
                                <span class="font-medium text-gray-600">注目理由:</span>
                                <p class="text-gray-700 mt-1">{stock.get('reason', '')}</p>
                            </div>
                            <div>
                                <span class="font-medium text-gray-600">前提条件:</span>
                                <p class="text-gray-700 mt-1">{stock.get('precondition', '')}</p>
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
"""
        return html
    
    def generate_full_page(self, analysis_result: Dict, sectors: List[Dict], recommendations: Dict) -> str:
        """フルページを生成"""
        html = self._generate_header()
        
        # Overview
        html += self.generate_overview_cards(analysis_result)
        
        # サマリー
        html += self.generate_summary_section(analysis_result)
        
        # 国別分析
        for country_code, country_result in analysis_result["countries"].items():
            html += self.generate_country_analysis(country_result, analysis_result)
        
        # セクター分析
        if sectors:
            html += self.generate_sector_analysis(sectors)
        
        # 銘柄推奨
        if recommendations:
            html += self.generate_stock_recommendations(recommendations)
        
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
        
        if analysis_text.get("結論"):
            html += f"""
            <section class="bg-white rounded-2xl shadow-md p-6 mb-6">
                <h2 class="text-2xl font-bold text-gray-900 mb-4">結論</h2>
                <p class="text-gray-700 leading-relaxed">{analysis_text['結論']}</p>
            </section>
"""
        
        if analysis_text.get("前提"):
            html += f"""
            <section class="bg-white rounded-2xl shadow-md p-6 mb-6">
                <h2 class="text-2xl font-bold text-gray-900 mb-4">前提</h2>
                <p class="text-gray-700 leading-relaxed">{analysis_text['前提']}</p>
            </section>
"""
        
        if analysis_text.get("最大リスク"):
            html += f"""
            <section class="bg-red-50 rounded-2xl shadow-md p-6 mb-6 border-l-4 border-red-300">
                <h2 class="text-2xl font-bold text-red-800 mb-4">最大リスク</h2>
                <p class="text-red-700 leading-relaxed">{analysis_text['最大リスク']}</p>
            </section>
"""
        
        if analysis_text.get("転換シグナル"):
            html += f"""
            <section class="bg-blue-50 rounded-2xl shadow-md p-6 mb-6 border-l-4 border-blue-300">
                <h2 class="text-2xl font-bold text-blue-800 mb-4">転換シグナル</h2>
                <p class="text-blue-700 leading-relaxed">{analysis_text['転換シグナル']}</p>
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
    
    def generate_thought_log(self, country_code: str, timeframe_code: str, data: Dict, analysis: Dict) -> str:
        """思考ログを生成"""
        date_str = datetime.now().strftime("%Y年%m月%d日 %H:%M")
        
        html = self._generate_header(f"思考ログ: {country_code} - {timeframe_code}")
        
        html += f"""
            <div class="mb-6">
                <a href="../index.html" class="inline-flex items-center text-blue-600 hover:text-blue-800 font-medium">
                    ← トップページに戻る
                </a>
            </div>
            
            <section class="bg-white rounded-2xl shadow-md p-6 mb-6">
                <h2 class="text-2xl font-bold text-gray-900 mb-4">判断に至ったプロセス</h2>
                
                <div class="mb-6">
                    <h3 class="text-lg font-semibold text-gray-800 mb-3">使用データ</h3>
                    <pre class="bg-gray-50 p-4 rounded-lg overflow-x-auto text-sm"><code>{json.dumps(data, ensure_ascii=False, indent=2, default=str)}</code></pre>
                </div>
                
                <div class="mb-6">
                    <h3 class="text-lg font-semibold text-gray-800 mb-3">分析結果</h3>
                    <pre class="bg-gray-50 p-4 rounded-lg overflow-x-auto text-sm"><code>{json.dumps(analysis, ensure_ascii=False, indent=2, default=str)}</code></pre>
                </div>
                
                <div class="bg-blue-50 p-4 rounded-lg border-l-4 border-blue-300">
                    <h3 class="text-lg font-semibold text-blue-800 mb-3">判断理由</h3>
                    <p class="text-blue-700 mb-3">上記のデータと分析結果に基づき、以下の判断を行いました：</p>
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div class="bg-white p-3 rounded-lg">
                            <p class="text-xs text-gray-600 mb-1">マクロ指標</p>
                            <p class="text-lg font-bold text-gray-900">{analysis.get('components', {}).get('macro', 0):.2f}</p>
                        </div>
                        <div class="bg-white p-3 rounded-lg">
                            <p class="text-xs text-gray-600 mb-1">金融指標</p>
                            <p class="text-lg font-bold text-gray-900">{analysis.get('components', {}).get('financial', 0):.2f}</p>
                        </div>
                        <div class="bg-white p-3 rounded-lg">
                            <p class="text-xs text-gray-600 mb-1">テクニカル指標</p>
                            <p class="text-lg font-bold text-gray-900">{analysis.get('components', {}).get('technical', 0):.2f}</p>
                        </div>
                        <div class="bg-white p-3 rounded-lg">
                            <p class="text-xs text-gray-600 mb-1">構造的指標</p>
                            <p class="text-lg font-bold text-gray-900">{analysis.get('components', {}).get('structural', 0):.2f}</p>
                        </div>
                    </div>
                    <div class="mt-4 pt-4 border-t border-blue-200">
                        <p class="text-sm text-blue-600 mb-1">最終スコア</p>
                        <p class="text-2xl font-bold text-blue-800">{analysis.get('score', 0)} ({analysis.get('label', '中立')})</p>
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


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
    
    def _generate_header(self, title: str = "株式市場分析レポート") -> str:
        """HTMLヘッダーを生成（初心者向けUI）"""
        date_str = datetime.now().strftime("%Y年%m月%d日 %H:%M")
        return f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdn.tailwindcss.com"></script>
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
        .accordion-content {{
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease-out;
        }}
        .accordion-content.open {{
            max-height: 2000px;
            transition: max-height 0.3s ease-in;
        }}
    </style>
</head>
<body class="bg-gray-50">
    <div class="min-h-screen">
        <!-- ヘッダー（シンプル） -->
        <header class="bg-white shadow-sm">
            <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                <h1 class="text-2xl sm:text-3xl font-bold text-gray-900">{title}</h1>
                <p class="mt-1 text-xs sm:text-sm text-gray-500">最終更新: {date_str}</p>
            </div>
        </header>
        
        <!-- メインコンテンツ -->
        <main class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
"""
    
    def _generate_footer(self) -> str:
        """HTMLフッターを生成"""
        return """        </main>
        
        <!-- フッター -->
        <footer class="bg-white border-t mt-8">
            <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                <div class="space-y-4">
                    <!-- 免責事項（短縮版） -->
                    <div class="bg-yellow-50 border-l-4 border-yellow-400 p-4 rounded-lg">
                        <p class="text-sm text-yellow-800 mb-2">
                            <strong>免責事項</strong>: この情報は参考としてお使いください。投資判断は自己責任で行ってください。
                        </p>
                        <button onclick="toggleDetail('disclaimer-detail')" class="text-xs text-yellow-700 hover:text-yellow-900 underline">
                            詳細を見る <span id="disclaimer-detail-icon">▼</span>
                        </button>
                        <div id="disclaimer-detail" class="accordion-content mt-2">
                            <div class="text-xs text-yellow-800 space-y-1">
                                <p>・投資判断は、必ずご自身で行ってください</p>
                                <p>・過去の実績は、将来を保証するものではありません</p>
                                <p>・この情報は、あくまで参考としてお使いください</p>
                                <p class="mt-2">投資にはリスクが伴います。ご自身の判断で、慎重に検討してください。</p>
                            </div>
                        </div>
                    </div>
                    
                    <!-- データ取得元（簡潔） -->
                    <div class="text-xs sm:text-sm text-gray-600 space-y-1">
                        <p><strong>データ取得元:</strong> Yahoo Finance, FRED API, e-Stat API</p>
                        <p><strong>更新頻度:</strong> 毎日、日本時間の18時に自動更新</p>
                        <button onclick="toggleDetail('data-detail')" class="text-gray-600 hover:text-gray-800 underline">
                            データの詳細を見る <span id="data-detail-icon">▼</span>
                        </button>
                        <div id="data-detail" class="accordion-content mt-2">
                            <div class="text-xs sm:text-sm text-gray-600 space-y-1">
                                <p><strong>指標計算方法:</strong></p>
                                <ul class="list-disc list-inside ml-4 space-y-1">
                                    <li>移動平均: 過去の株価の平均値（20日、75日、200日）</li>
                                    <li>ボラティリティ: 株価の変動の大きさ（過去30日）</li>
                                    <li>出来高比率: 最新の取引量と平均の比較</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </footer>
    </div>
    
    <script>
    // アコーディオン展開/折りたたみ
    function toggleDetail(id) {{
        const content = document.getElementById(id);
        const icon = document.getElementById(id + '-icon');
        if (content && icon) {{
            content.classList.toggle('open');
            icon.textContent = content.classList.contains('open') ? '▲' : '▼';
        }}
    }}
    
    // 銘柄詳細モーダル
    function showStockDetail(stockId) {{
        const modal = document.getElementById(stockId);
        if (modal) {{
            modal.classList.remove('hidden');
            document.body.style.overflow = 'hidden';
        }}
    }}
    
    function hideStockDetail(stockId) {{
        const modal = document.getElementById(stockId);
        if (modal) {{
            modal.classList.add('hidden');
            document.body.style.overflow = 'auto';
        }}
    }}
    
    // モーダル外側クリックで閉じる
    document.addEventListener('click', function(e) {{
        if (e.target.classList.contains('bg-black')) {{
            e.target.classList.add('hidden');
            document.body.style.overflow = 'auto';
        }}
    }});
    </script>
</body>
</html>"""
    
    def generate_first_view_card(self, analysis_result: Dict) -> str:
        """ファーストビュー：市場の今の状態メインカード（初心者向け）"""
        # 最新の分析結果から主要な情報を取得（日本株の中期をデフォルト）
        countries = self.config['countries']
        overview = analysis_result.get("overview", {})
        
        # 日本株の中期データを取得（なければ最初の国・期間）
        main_country_code = "JP"
        main_timeframe_code = "medium"
        
        if main_country_code not in overview or main_timeframe_code not in overview[main_country_code]:
            # フォールバック：最初の利用可能なデータ
            if overview:
                main_country_code = list(overview.keys())[0]
                if overview[main_country_code]:
                    main_timeframe_code = list(overview[main_country_code].keys())[0]
        
        main_direction = overview.get(main_country_code, {}).get(main_timeframe_code, {})
        score = main_direction.get("score", 0)
        has_risk = main_direction.get("has_risk", False)
        
        # 国別データから詳細情報を取得
        country_result = analysis_result.get("countries", {}).get(main_country_code, {})
        direction_data = country_result.get("directions", {}).get(main_timeframe_code, {})
        
        summary = direction_data.get("summary", "データを分析中です。")
        stance = self._get_market_stance(score)
        stance_label = direction_data.get("direction_label", self.score_labels.get(str(score), "中立"))
        
        # リスクレベルの判定
        risk_level = "中"
        risk_icon = "⚠️"
        if has_risk:
            risk_level = "高"
            risk_icon = "🚨"
        elif score == 0 and not has_risk:
            risk_level = "低"
            risk_icon = "✅"
        
        # 色の設定
        if score >= 1:
            bg_color = "bg-green-50"
            text_color = "text-green-800"
            border_color = "border-green-300"
        elif score <= -1:
            bg_color = "bg-red-50"
            text_color = "text-red-800"
            border_color = "border-red-300"
        else:
            bg_color = "bg-gray-50"
            text_color = "text-gray-800"
            border_color = "border-gray-300"
        
        html = f"""
        <!-- ファーストビュー：市場の今の状態 -->
        <section class="mb-8">
            <div class="bg-white rounded-2xl shadow-lg p-6 sm:p-8 mb-4">
                <h2 class="text-xl sm:text-2xl font-bold text-gray-900 mb-6 flex items-center">
                    <span class="text-2xl sm:text-3xl mr-2">📊</span>
                    市場の今の状態
                </h2>
                
                <div class="{bg_color} rounded-xl p-6 sm:p-8 border-l-4 {border_color}">
                    <div class="text-center mb-6">
                        <div class="text-4xl sm:text-5xl mb-3">{stance}</div>
                        <div class="text-2xl sm:text-3xl font-bold {text_color} mb-4">{stance_label}</div>
                        <div class="flex items-center justify-center space-x-2 text-sm sm:text-base">
                            <span>リスクレベル:</span>
                            <span class="text-xl">{risk_icon}</span>
                            <span class="font-semibold">{risk_level}</span>
                        </div>
                    </div>
                    
                    <div class="border-t {border_color} pt-6 mt-6">
                        <p class="text-base sm:text-lg {text_color} leading-relaxed text-center">
                            {summary}
                        </p>
                    </div>
                    
                    <div class="mt-6 text-center">
                        <button onclick="toggleDetail('main-detail')" class="inline-flex items-center px-4 py-2 bg-white {text_color} border-2 {border_color} rounded-lg font-medium hover:bg-opacity-90 transition">
                            <span>詳しく見る</span>
                            <span id="main-detail-icon" class="ml-2">▼</span>
                        </button>
                    </div>
                </div>
            </div>
            
            <!-- 詳細情報（アコーディオン） -->
            <div id="main-detail" class="accordion-content">
                <div class="bg-white rounded-2xl shadow-md p-6 space-y-6">
"""
        
        # なぜそう判断したか
        key_factors = direction_data.get("key_factors", [])
        premise = direction_data.get("premise", "")
        
        html += f"""
                    <!-- なぜそう判断したか -->
                    <div class="border-l-4 border-blue-400 pl-4">
                        <h3 class="text-lg font-semibold text-gray-900 mb-3">なぜそう判断したか</h3>
                        <div class="space-y-3 text-sm sm:text-base text-gray-700">
"""
        
        if premise:
            html += f"""
                            <p class="mb-3">{premise}</p>
"""
        
        if key_factors:
            html += """
                            <p class="mb-2">以下の観点から判断しています：</p>
                            <ol class="list-decimal list-inside space-y-2 ml-2">
"""
            for i, factor in enumerate(key_factors[:3], 1):
                html += f"""
                                <li>{factor}</li>
"""
            html += """
                            </ol>
"""
        else:
            html += """
                            <p>データを分析した結果、現在の市場環境を判断しています。</p>
"""
        
        html += """
                        </div>
                    </div>
"""
        
        # 注意しておきたい点
        risks = direction_data.get("risks", [])
        if risks:
            html += f"""
                    <!-- 注意しておきたい点 -->
                    <div class="bg-yellow-50 border-l-4 border-yellow-400 p-4 rounded-lg">
                        <h3 class="text-lg font-semibold text-yellow-900 mb-3 flex items-center">
                            <span class="mr-2">⚠️</span>
                            注意しておきたい点
                        </h3>
                        <ul class="list-disc list-inside space-y-2 text-sm sm:text-base text-yellow-800">
"""
            for risk in risks:
                html += f"""
                            <li>{risk}</li>
"""
            html += """
                        </ul>
                    </div>
"""
        
        # 判断を見直すタイミング
        turning_points = direction_data.get("turning_points", [])
        if turning_points:
            html += f"""
                    <!-- 判断を見直すタイミング -->
                    <div class="border-l-4 border-blue-400 pl-4">
                        <h3 class="text-lg font-semibold text-gray-900 mb-3">判断を見直すタイミング</h3>
                        <p class="text-sm sm:text-base text-gray-700 mb-3">
                            以下のような変化が見られたら、市場の状態が変わり始めている可能性があります：
                        </p>
                        <ul class="list-disc list-inside space-y-2 text-sm sm:text-base text-gray-700 ml-2">
"""
            for point in turning_points:
                html += f"""
                            <li>{point}</li>
"""
            html += """
                        </ul>
                        <p class="text-xs sm:text-sm text-gray-600 mt-3 italic">
                            ※ これらの条件は「目安」です。必ずしもこの通りになるとは限りませんが、参考として知っておくと役立ちます。
                        </p>
                    </div>
"""
        
        html += """
                </div>
            </div>
        </section>
"""
        
        return html
    
    def generate_overview_cards(self, analysis_result: Dict) -> str:
        """国別・期間別の状態カード（コンパクト、クリックで展開）"""
        countries = self.config['countries']
        timeframes = self.config['timeframes']
        overview = analysis_result.get("overview", {})
        
        html = """
        <!-- 国別・期間別の状態 -->
        <section class="mb-8">
            <h2 class="text-xl sm:text-2xl font-bold text-gray-900 mb-4">国別・期間別の状態</h2>
            <div class="space-y-4">
"""
        
        for country_config in countries:
            country_code = country_config['code']
            country_name = country_config['name']
            directions = overview.get(country_code, {})
            country_result = analysis_result.get("countries", {}).get(country_code, {})
            
            html += f"""
                <div class="bg-white rounded-xl shadow-md overflow-hidden">
                    <button onclick="toggleDetail('{country_code}-detail')" class="w-full p-4 sm:p-6 text-left flex items-center justify-between hover:bg-gray-50 transition">
                        <h3 class="text-lg sm:text-xl font-semibold text-gray-900">{country_name}</h3>
                        <span id="{country_code}-detail-icon" class="text-gray-400">▼</span>
                    </button>
                    
                    <div id="{country_code}-detail" class="accordion-content">
                        <div class="px-4 sm:px-6 pb-4 sm:pb-6 space-y-4">
"""
            
            for timeframe in timeframes:
                timeframe_code = timeframe['code']
                timeframe_name = timeframe['name']
                
                direction = directions.get(timeframe_code, {})
                score = direction.get("score", 0)
                has_risk = direction.get("has_risk", False)
                label = self.score_labels.get(str(score), "→ 中立")
                
                style = self._get_score_style(score)
                stance = self._get_market_stance(score)
                
                # リスクアイコン
                if has_risk:
                    risk_icon = "🚨"
                    risk_text = "高"
                elif score == 0:
                    risk_icon = "✅"
                    risk_text = "低"
                else:
                    risk_icon = "⚠️"
                    risk_text = "中"
                
                direction_data = country_result.get("directions", {}).get(timeframe_code, {})
                summary = direction_data.get("summary", "")
                
                html += f"""
                            <div class="border-l-4 {style['border']} pl-4 py-3 bg-gray-50 rounded-r-lg">
                                <div class="flex items-center justify-between mb-2">
                                    <span class="text-sm sm:text-base font-medium text-gray-700">{timeframe_name}</span>
                                    <div class="flex items-center space-x-2">
                                        <span class="text-xl">{stance}</span>
                                        <span class="text-sm sm:text-base font-semibold {style['text']}">{label}</span>
                                        <span class="text-sm">{risk_icon}</span>
                                    </div>
                                </div>
                                <p class="text-xs sm:text-sm text-gray-600">{summary[:80]}{'...' if len(summary) > 80 else ''}</p>
                                <a href="./details/{country_code}-{timeframe_code}.html" class="text-xs sm:text-sm text-blue-600 hover:text-blue-800 mt-2 inline-block">
                                    詳細を見る →
                                </a>
                            </div>
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
        """全体サマリーセクションを生成（非表示：ファーストビューに統合）"""
        # 初心者向けUIでは、サマリーはファーストビューに統合されているため空を返す
        return ""
    
    def generate_country_analysis(self, country_result: Dict, analysis_result: Dict) -> str:
        """国別分析セクションを生成（非表示：詳細ページに移動）"""
        # 初心者向けUIでは、詳細分析は詳細ページに移動
        return ""
        
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
        """セクター分析セクションを生成（初心者向け）"""
        if not sectors:
            return ""
        
        html = """
                    <!-- 注目セクター -->
                    <div>
                        <h3 class="text-lg sm:text-xl font-bold text-gray-900 mb-4">注目セクター</h3>
                        <p class="text-sm text-gray-600 mb-4">現在、注目されている業界や分野の情報です。参考としてご覧ください。</p>
                        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
"""
        
        for i, sector in enumerate(sectors[:3], 1):
            html += f"""
                            <div class="bg-white rounded-xl shadow-sm p-4 border border-gray-200">
                                <div class="flex items-center mb-3">
                                    <span class="flex items-center justify-center w-6 h-6 rounded-full bg-blue-100 text-blue-600 font-bold text-sm mr-2">
                                        {i}
                                    </span>
                                    <h4 class="text-base font-semibold text-gray-900">{sector.get('name', 'セクター')}</h4>
                                </div>
"""
            
            if sector.get('reason'):
                html += f"""
                                <div class="mb-2">
                                    <p class="text-xs text-gray-600 mb-1">なぜ注目されているか</p>
                                    <p class="text-sm text-gray-700">{sector['reason']}</p>
                                </div>
"""
            
            if sector.get('related_fields'):
                fields = sector['related_fields']
                if isinstance(fields, str):
                    fields = [fields]
                html += f"""
                                <div class="mb-2">
                                    <p class="text-xs text-gray-600 mb-1">関連する分野</p>
                                    <div class="flex flex-wrap gap-1">
"""
                for field in fields[:3]:  # 最大3つまで
                    html += f"""
                                        <span class="px-2 py-0.5 bg-orange-50 text-orange-700 text-xs rounded">{field}</span>
"""
                html += """
                                    </div>
                                </div>
"""
            
            if sector.get('timeframe'):
                html += f"""
                                <div class="mt-2">
                                    <span class="text-xs text-gray-500">期間: {sector['timeframe']}</span>
                                </div>
"""
            
            html += """
                            </div>
"""
        
        html += """
                        </div>
                    </div>
"""
        return html
    
    def generate_stock_recommendations(self, recommendations: Dict) -> str:
        """銘柄評価セクションを生成（初心者向け、推奨ではなく参考情報）"""
        if not recommendations:
            return ""
        
        html = """
                    <!-- 参考銘柄情報 -->
                    <div class="mt-6">
                        <div class="bg-yellow-50 border-l-4 border-yellow-400 p-3 mb-4 rounded-lg">
                            <p class="text-xs sm:text-sm text-yellow-800">
                                <strong>重要:</strong> 以下は参考情報です。投資助言ではありません。投資判断は自己責任で行ってください。
                            </p>
                        </div>
                        <h3 class="text-lg sm:text-xl font-bold text-gray-900 mb-4">参考銘柄情報</h3>
                        <p class="text-sm text-gray-600 mb-4">現在の市場環境と照らし合わせて、参考になりそうな銘柄の情報です。</p>
"""
        
        # 日本株
        jp_stocks = recommendations.get("JP", [])
        if jp_stocks:
            html += """
                        <div class="mb-6">
                            <h4 class="text-base sm:text-lg font-semibold text-gray-900 mb-3">日本株</h4>
                            <div class="space-y-4">
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
                                <div class="bg-white rounded-xl shadow-sm p-4 border border-gray-200 cursor-pointer hover:shadow-md transition" onclick="showStockDetail('{stock_id}')">
                                    <div class="flex items-start justify-between mb-2">
                                        <div class="flex-1">
                                            <h5 class="text-base font-semibold text-gray-900 mb-1">
                                                {stock.get('name', '')}
                                            </h5>
                                            <span class="text-xs text-gray-500">{stock.get('ticker', '')}</span>
                                        </div>
                                        <span class="text-lg font-bold {eval_color} ml-2">{overall}</span>
                                    </div>
                                    <div class="text-xs text-gray-600 mb-2">
                                        <span>{stock.get('sector', '')}</span>
                                    </div>
                                    <p class="text-xs text-gray-600 line-clamp-2">{stock.get('business_summary', '')[:80]}...</p>
                                    <button class="text-xs text-blue-600 hover:text-blue-800 mt-2">
                                        詳細を見る →
                                    </button>
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
                        <div class="mt-6">
                            <h4 class="text-base sm:text-lg font-semibold text-gray-900 mb-3">米国株</h4>
                            <div class="space-y-4">
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
                                <div class="bg-white rounded-xl shadow-sm p-4 border border-gray-200 cursor-pointer hover:shadow-md transition" onclick="showStockDetail('{stock_id}')">
                                    <div class="flex items-start justify-between mb-2">
                                        <div class="flex-1">
                                            <h5 class="text-base font-semibold text-gray-900 mb-1">
                                                {stock.get('name', '')}
                                            </h5>
                                            <span class="text-xs text-gray-500">{stock.get('ticker', '')}</span>
                                        </div>
                                        <span class="text-lg font-bold {eval_color} ml-2">{overall}</span>
                                    </div>
                                    <div class="text-xs text-gray-600 mb-2">
                                        <span>{stock.get('sector', '')}</span>
                                    </div>
                                    <p class="text-xs text-gray-600 line-clamp-2">{stock.get('business_summary', '')[:80]}...</p>
                                    <button class="text-xs text-blue-600 hover:text-blue-800 mt-2">
                                        詳細を見る →
                                    </button>
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
                    </div>
"""
        return html
    
    def generate_full_page(self, analysis_result: Dict, sectors: List[Dict], recommendations: Dict) -> str:
        """フルページを生成（初心者向けUI）"""
        html = self._generate_header()
        
        # ファーストビュー：市場の今の状態
        html += self.generate_first_view_card(analysis_result)
        
        # 国別・期間別の状態（コンパクトカード、展開式）
        html += self.generate_overview_cards(analysis_result)
        
        # 参考情報（折りたたみ）
        if sectors or recommendations:
            html += """
        <!-- 参考情報（折りたたみ） -->
        <section class="mb-8">
            <button onclick="toggleDetail('reference-info')" class="w-full p-4 bg-white rounded-xl shadow-md text-left flex items-center justify-between hover:bg-gray-50 transition">
                <h2 class="text-xl sm:text-2xl font-bold text-gray-900">参考情報</h2>
                <span id="reference-info-icon" class="text-gray-400">▼</span>
            </button>
            
            <div id="reference-info" class="accordion-content">
                <div class="mt-4 space-y-6">
"""
            
            # セクター分析
            if sectors:
                html += self.generate_sector_analysis(sectors)
            
            # 銘柄推奨
            if recommendations:
                html += self.generate_stock_recommendations(recommendations)
            
            html += """
                </div>
            </div>
        </section>
"""
        
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
    
    def _extract_facts(self, data: Dict, analysis: Dict) -> List[str]:
        """観測事実を抽出（数値・状態のみ、主観的表現は禁止）"""
        facts = []
        
        # インデックスデータから観測事実を抽出
        indices = data.get("indices", {})
        if indices:
            for index_code, index_data in indices.items():
                latest_price = index_data.get("latest_price")
                ma20 = index_data.get("ma20")
                ma75 = index_data.get("ma75")
                ma200 = index_data.get("ma200")
                price_vs_ma20 = index_data.get("price_vs_ma20", 0)
                price_vs_ma75 = index_data.get("price_vs_ma75", 0)
                price_vs_ma200 = index_data.get("price_vs_ma200", 0)
                volume_ratio = index_data.get("volume_ratio", 1.0)
                volatility = index_data.get("volatility", 0)
                
                if latest_price:
                    facts.append(f"{index_code}の最新終値は{latest_price:.2f}です")
                
                # 移動平均との関係（事実のみ）
                if ma20 and latest_price:
                    facts.append(f"{index_code}の20日移動平均は{ma20:.2f}です（最新価格との差: {price_vs_ma20:+.2f}%）")
                
                if ma75 and latest_price:
                    facts.append(f"{index_code}の75日移動平均は{ma75:.2f}です（最新価格との差: {price_vs_ma75:+.2f}%）")
                
                if ma200 and latest_price:
                    facts.append(f"{index_code}の200日移動平均は{ma200:.2f}です（最新価格との差: {price_vs_ma200:+.2f}%）")
                
                # 移動平均の順序関係（事実のみ）
                if ma20 and ma75 and ma200:
                    if ma20 > ma75 > ma200:
                        facts.append(f"{index_code}の移動平均は20日 > 75日 > 200日の順序です")
                    elif ma20 < ma75 < ma200:
                        facts.append(f"{index_code}の移動平均は20日 < 75日 < 200日の順序です")
                    else:
                        facts.append(f"{index_code}の移動平均は交差している状態です")
                
                # 出来高（事実のみ）
                if volume_ratio:
                    facts.append(f"{index_code}の最新出来高は直近30日平均の{volume_ratio:.2f}倍です")
                
                # ボラティリティ（事実のみ）
                if volatility:
                    facts.append(f"{index_code}の過去30日のボラティリティ（年率換算）は{volatility:.2f}%です")
        
        # マクロ指標から観測事実を抽出
        macro = data.get("macro", {})
        if macro.get("PMI") is not None:
            facts.append(f"PMIは{macro['PMI']:.1f}です")
        if macro.get("CPI") is not None:
            facts.append(f"CPI前年同月比は{macro['CPI']:.2f}%です")
        if macro.get("employment_rate") is not None:
            facts.append(f"雇用率は{macro['employment_rate']:.2f}%です")
        
        # 金融指標から観測事実を抽出
        financial = data.get("financial", {})
        if financial.get("policy_rate") is not None:
            facts.append(f"政策金利は{financial['policy_rate']:.2f}%です")
        if financial.get("long_term_rate") is not None:
            facts.append(f"長期金利（10年債）は{financial['long_term_rate']:.2f}%です")
        
        return facts
    
    def generate_thought_log(self, country_code: str, timeframe_code: str, data: Dict, analysis: Dict) -> str:
        """思考ログを生成（4ブロック構成：観測事実・解釈・前提・転換シグナル）"""
        date_str = datetime.now().strftime("%Y年%m月%d日 %H:%M")
        
        country_name = data.get("name", country_code)
        timeframe_name = next(
            (tf['name'] for tf in self.config['timeframes'] if tf['code'] == timeframe_code),
            timeframe_code
        )
        
        html = self._generate_header(f"思考ログ: {country_name} - {timeframe_name}")
        
        html += f"""
            <div class="mb-6">
                <a href="../index.html" class="inline-flex items-center text-blue-600 hover:text-blue-800 font-medium">
                    ← トップページに戻る
                </a>
            </div>
            
            <div class="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6 rounded-lg">
                <p class="text-sm text-yellow-800">
                    <strong>重要:</strong> この思考ログは「判断結果」ではなく、「判断材料」です。ユーザーが自分で判断できるための情報を提示しています。
                </p>
            </div>
            
            <section class="bg-white rounded-2xl shadow-md p-6 mb-6">
                <h2 class="text-2xl font-bold text-gray-900 mb-6">判断材料</h2>
                
                <!-- ① 観測事実（Fact） -->
                <div class="mb-8 p-6 bg-gray-50 rounded-lg border-l-4 border-gray-400">
                    <h3 class="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                        <span class="bg-gray-600 text-white rounded-full w-8 h-8 flex items-center justify-center mr-3 text-sm font-bold">①</span>
                        観測事実（Fact）
                    </h3>
                    <p class="text-sm text-gray-600 mb-4">実際に観測できる数値・状態のみを列挙しています。主観的表現は含まれていません。</p>
                    <ul class="list-disc list-inside text-gray-800 space-y-2">
"""
        
        # 観測事実を抽出
        facts = self._extract_facts(data, analysis)
        if not facts:
            facts = ["データが不足しているため、観測事実を抽出できませんでした。"]
        
        for fact in facts:
            html += f"""
                        <li>{fact}</li>
"""
        
        html += """
                    </ul>
                </div>
                
                <!-- ② 解釈（Interpretation） -->
                <div class="mb-8 p-6 bg-blue-50 rounded-lg border-l-4 border-blue-400">
                    <h3 class="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                        <span class="bg-blue-600 text-white rounded-full w-8 h-8 flex items-center justify-center mr-3 text-sm font-bold">②</span>
                        解釈（Interpretation）
                    </h3>
                    <p class="text-sm text-gray-600 mb-4">観測事実から考えられる見方を説明しています。断定表現は使用していません。</p>
                    <div class="bg-white p-4 rounded-lg">
"""
        
        # 解釈を表示（LLMのsummaryまたはkey_factorsから）
        summary = analysis.get('summary', '')
        key_factors = analysis.get('key_factors', [])
        
        if summary:
            html += f"""
                        <p class="text-gray-800 leading-relaxed mb-3">{summary}</p>
"""
        
        if key_factors:
            html += """
                        <ul class="list-disc list-inside text-gray-800 space-y-2">
"""
            for factor in key_factors:
                html += f"""
                            <li>{factor}</li>
"""
            html += """
                        </ul>
"""
        
        if not summary and not key_factors:
            html += """
                        <p class="text-gray-800">観測事実から、市場環境は中立的な状態と考えられます。</p>
"""
        
        html += """
                    </div>
                </div>
                
                <!-- ③ この見方が成り立つ前提（Assumption） -->
                <div class="mb-8 p-6 bg-green-50 rounded-lg border-l-4 border-green-400">
                    <h3 class="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                        <span class="bg-green-600 text-white rounded-full w-8 h-8 flex items-center justify-center mr-3 text-sm font-bold">③</span>
                        この見方が成り立つ前提（Assumption）
                    </h3>
                    <p class="text-sm text-gray-600 mb-4">解釈が有効であるための条件を明示しています。再現可能な条件です。</p>
                    <div class="bg-white p-4 rounded-lg">
"""
        
        # 前提条件を表示
        premise = analysis.get('premise', '')
        if premise:
            html += f"""
                        <p class="text-gray-800 leading-relaxed">{premise}</p>
"""
        else:
            # データから前提条件を生成
            indices = data.get("indices", {})
            if indices:
                first_index = list(indices.values())[0]
                ma200 = first_index.get("ma200")
                latest_price = first_index.get("latest_price")
                if ma200 and latest_price:
                    if latest_price > ma200:
                        html += f"""
                        <ul class="list-disc list-inside text-gray-800 space-y-2">
                            <li>価格が200日移動平均（{ma200:.2f}）を上回って推移すること</li>
                            <li>マクロ環境が現在の水準を維持すること</li>
                            <li>出来高が平均以上を維持すること</li>
                        </ul>
"""
                    else:
                        html += f"""
                        <ul class="list-disc list-inside text-gray-800 space-y-2">
                            <li>価格が200日移動平均（{ma200:.2f}）を下回って推移すること</li>
                            <li>マクロ環境が現在の水準を維持すること</li>
                            <li>出来高が平均以上を維持すること</li>
                        </ul>
"""
            else:
                html += """
                        <p class="text-gray-800">データに基づく判断材料を提示しています。テクニカル指標とマクロ環境の現状を反映しています。</p>
"""
        
        html += """
                    </div>
                </div>
                
                <!-- ④ 見方が変わる条件（転換シグナル） -->
                <div class="mb-8 p-6 bg-red-50 rounded-lg border-l-4 border-red-400">
                    <h3 class="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                        <span class="bg-red-600 text-white rounded-full w-8 h-8 flex items-center justify-center mr-3 text-sm font-bold">④</span>
                        見方が変わる条件（転換シグナル）
                    </h3>
                    <p class="text-sm text-gray-600 mb-4">判断が変わる具体的なトリガーを数値で示しています。曖昧な表現は使用していません。</p>
                    <div class="bg-white p-4 rounded-lg">
                        <ul class="list-disc list-inside text-gray-800 space-y-2">
"""
        
        # 転換シグナルを表示
        turning_points = analysis.get('turning_points', [])
        if turning_points:
            for point in turning_points:
                html += f"""
                            <li>{point}</li>
"""
        else:
            # データから転換シグナルを生成
            indices = data.get("indices", {})
            if indices:
                first_index = list(indices.values())[0]
                ma20 = first_index.get("ma20")
                ma75 = first_index.get("ma75")
                ma200 = first_index.get("ma200")
                latest_price = first_index.get("latest_price")
                
                if ma200 and latest_price:
                    if latest_price > ma200:
                        html += f"""
                            <li>終値ベースで200日移動平均（{ma200:.2f}）を3日連続で下回った場合</li>
"""
                    else:
                        html += f"""
                            <li>終値ベースで200日移動平均（{ma200:.2f}）を3日連続で上回った場合</li>
"""
                
                if ma75:
                    html += f"""
                            <li>出来高を伴って75日移動平均（{ma75:.2f}）を割り込んだ（または突破した）場合</li>
"""
                
                if ma20:
                    html += f"""
                            <li>20日移動平均（{ma20:.2f}）と75日移動平均（{ma75:.2f if ma75 else 'N/A'}）の順序が逆転した場合</li>
"""
            
            # マクロ指標の転換シグナル
            macro = data.get("macro", {})
            if macro.get("PMI"):
                html += f"""
                            <li>PMIが50を下回った（または上回った）場合</li>
"""
            if macro.get("CPI"):
                html += f"""
                            <li>CPI前年同月比が前回値から±1%ポイント以上変化した場合</li>
"""
        
        html += """
                        </ul>
                    </div>
                </div>
                
                <!-- 参考情報 -->
                <div class="mt-8 pt-6 border-t border-gray-200">
                    <h3 class="text-lg font-semibold text-gray-800 mb-4">参考情報</h3>
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
"""
        
        # ルールベース指標を参考情報として表示
        rule_components = analysis.get('rule_based_components', {})
        if rule_components:
            html += f"""
                        <div class="bg-gray-50 p-3 rounded-lg">
                            <p class="text-xs text-gray-600 mb-1">マクロ指標スコア</p>
                            <p class="text-lg font-bold text-gray-900">{rule_components.get('macro', 0):.2f}</p>
                        </div>
                        <div class="bg-gray-50 p-3 rounded-lg">
                            <p class="text-xs text-gray-600 mb-1">金融指標スコア</p>
                            <p class="text-lg font-bold text-gray-900">{rule_components.get('financial', 0):.2f}</p>
                        </div>
                        <div class="bg-gray-50 p-3 rounded-lg">
                            <p class="text-xs text-gray-600 mb-1">テクニカル指標スコア</p>
                            <p class="text-lg font-bold text-gray-900">{rule_components.get('technical', 0):.2f}</p>
                        </div>
                        <div class="bg-gray-50 p-3 rounded-lg">
                            <p class="text-xs text-gray-600 mb-1">構造的指標スコア</p>
                            <p class="text-lg font-bold text-gray-900">{rule_components.get('structural', 0):.2f}</p>
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


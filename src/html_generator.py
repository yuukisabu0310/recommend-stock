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
            background: linear-gradient(to bottom, #f8fafc 0%, #f1f5f9 100%);
        }}
        .card {{
            transition: transform 0.2s, box-shadow 0.2s;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
        }}
        .card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
        }}
        @keyframes fadeIn {{
            from {{
                opacity: 0;
                transform: translateY(10px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        .fade-in {{
            animation: fadeIn 0.5s ease-out;
        }}
        .arrow-up {{
            color: #059669;
            font-size: 1.5rem;
        }}
        .arrow-down {{
            color: #dc2626;
            font-size: 1.5rem;
        }}
        .arrow-neutral {{
            color: #6b7280;
            font-size: 1.5rem;
        }}
        .line-clamp-2 {{
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }}
    </style>
</head>
<body>
    <div class="min-h-screen">
        <!-- ヘッダー（コンパクト） -->
        <header class="bg-gradient-to-r from-blue-600 to-blue-700 shadow-md sticky top-0 z-20">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                <div class="flex items-center justify-between">
                    <div>
                        <h1 class="text-2xl font-bold text-white">{title}</h1>
                        <p class="text-blue-100 text-xs mt-1">更新: {date_str}</p>
                    </div>
                    <p class="text-blue-50 text-xs opacity-90 hidden md:block">市場環境の整理を目的としており、投資助言ではありません</p>
                </div>
            </div>
        </header>
        
        <!-- メインコンテンツ -->
        <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
"""
    
    def _generate_footer(self) -> str:
        """HTMLフッターを生成（改善版：データソース詳細化）"""
        return """        </main>
        
        <!-- フッター -->
        <footer class="bg-gradient-to-b from-gray-50 to-gray-100 border-t-2 border-gray-200 mt-16">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
                <div class="space-y-8">
                    <!-- 免責事項 -->
                    <div class="bg-yellow-50 border-l-4 border-yellow-400 p-5 rounded-lg shadow-sm">
                        <h3 class="font-bold text-yellow-900 mb-2 flex items-center">
                            <span class="mr-2">⚠️</span>
                            免責事項
                        </h3>
                        <p class="text-sm text-yellow-800 leading-relaxed">
                            本レポートは市場環境の整理を目的とした研究用途の資料であり、投資助言や売買指示を目的としたものではありません。
                            投資判断は自己責任で行ってください。過去の実績は将来を保証するものではありません。
                            本レポートの内容は「可能性」「傾向」を述べたものであり、断定表現は避けています。
                        </p>
                    </div>
                    
                    <!-- データソース・取得方法 -->
                    <div class="bg-white p-6 rounded-xl shadow-md border border-gray-200">
                        <h3 class="text-lg font-bold text-gray-900 mb-4 flex items-center">
                            <span class="mr-2">📊</span>
                            データソース・取得方法
                        </h3>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div>
                                <h4 class="font-semibold text-gray-800 mb-3">マクロ指標</h4>
                                <ul class="space-y-2 text-sm text-gray-700">
                                    <li class="flex items-start">
                                        <span class="font-medium mr-2">• PMI:</span>
                                        <span>S&P Global（実データ取得可能な場合はAPI経由、それ以外は推測値）</span>
                                    </li>
                                    <li class="flex items-start">
                                        <span class="font-medium mr-2">• CPI:</span>
                                        <span>FRED API（US Bureau of Labor Statistics / 各国統計機関）</span>
                                    </li>
                                    <li class="flex items-start">
                                        <span class="font-medium mr-2">• 雇用率:</span>
                                        <span>FRED API（US Bureau of Labor Statistics / 各国統計機関）</span>
                                    </li>
                                </ul>
                            </div>
                            <div>
                                <h4 class="font-semibold text-gray-800 mb-3">金融指標</h4>
                                <ul class="space-y-2 text-sm text-gray-700">
                                    <li class="flex items-start">
                                        <span class="font-medium mr-2">• 政策金利:</span>
                                        <span>FRED API（各国中央銀行データ）</span>
                                    </li>
                                    <li class="flex items-start">
                                        <span class="font-medium mr-2">• 長期金利:</span>
                                        <span>FRED API（10年物国債利回り）</span>
                                    </li>
                                </ul>
                            </div>
                            <div>
                                <h4 class="font-semibold text-gray-800 mb-3">株価指数</h4>
                                <ul class="space-y-2 text-sm text-gray-700">
                                    <li class="flex items-start">
                                        <span class="font-medium mr-2">• 価格・出来高:</span>
                                        <span>Yahoo Finance (yfinanceライブラリ)</span>
                                    </li>
                                    <li class="flex items-start">
                                        <span class="font-medium mr-2">• 更新頻度:</span>
                                        <span>日次（市場取引日）</span>
                                    </li>
                                </ul>
                            </div>
                            <div>
                                <h4 class="font-semibold text-gray-800 mb-3">指標計算方法</h4>
                                <ul class="space-y-2 text-sm text-gray-700">
                                    <li class="flex items-start">
                                        <span class="font-medium mr-2">• 移動平均:</span>
                                        <span>単純移動平均（SMA）- 20日、75日、200日</span>
                                    </li>
                                    <li class="flex items-start">
                                        <span class="font-medium mr-2">• ボラティリティ:</span>
                                        <span>過去30日の日次リターンの標準偏差を年率換算（√252倍）</span>
                                    </li>
                                    <li class="flex items-start">
                                        <span class="font-medium mr-2">• 出来高比率:</span>
                                        <span>最新出来高 ÷ 過去30日の平均出来高</span>
                                    </li>
                                    <li class="flex items-start">
                                        <span class="font-medium mr-2">• トレンド判定:</span>
                                        <span>価格と移動平均の順序関係から判定（上昇/下降/中立）</span>
                                    </li>
                                </ul>
                            </div>
                        </div>
                        
                        <div class="mt-6 pt-6 border-t border-gray-200">
                            <p class="text-sm text-gray-600">
                                <strong>更新頻度:</strong> 毎日自動実行（GitHub Actions経由、日本時間18:00頃）
                            </p>
                            <p class="text-sm text-gray-600 mt-2">
                                <strong>データ遅延:</strong> マクロ指標は通常1-2ヶ月の遅延があります。最新のデータは各データソースの公式サイトをご確認ください。
                            </p>
                        </div>
                    </div>
                    
                    <!-- 分析手法について -->
                    <div class="bg-blue-50 p-5 rounded-lg border-l-4 border-blue-400">
                        <h3 class="font-bold text-blue-900 mb-2">分析手法について</h3>
                        <p class="text-sm text-blue-800 leading-relaxed">
                            本レポートは、ルールベース分析とLLM（大規模言語モデル）による分析を組み合わせています。
                            各期間（短期・中期・長期）では異なる指標の重み付けを使用しており、期間が長くなるほど構造的・マクロ的な要因が重視されます。
                            詳細な判断ロジックは各ページの「思考ログ」セクションで確認できます。
                        </p>
                    </div>
                </div>
            </div>
        </footer>
    </div>
</body>
</html>"""
    
    def _get_arrow_icon(self, score: int) -> str:
        """スコアから矢印アイコンを取得"""
        if score >= 2:
            return '<span class="arrow-up">↗↗</span>'
        elif score == 1:
            return '<span class="arrow-up">↗</span>'
        elif score <= -2:
            return '<span class="arrow-down">↘↘</span>'
        elif score == -1:
            return '<span class="arrow-down">↘</span>'
        else:
            return '<span class="arrow-neutral">→</span>'
    
    def _get_one_line_summary(self, direction_data: Dict, timeframe_code: str) -> str:
        """1行要約を生成"""
        summary = direction_data.get("summary", "")
        if summary:
            # 最初の1文を抽出（最大50文字）
            sentences = summary.split('。')
            if sentences:
                first_sentence = sentences[0].strip()
                if len(first_sentence) > 50:
                    first_sentence = first_sentence[:47] + "..."
                return first_sentence
        return "データ分析中"
    
    def generate_overview_cards(self, analysis_result: Dict) -> str:
        """Overviewカードを生成（ダッシュボード型：ファーストビュー）"""
        countries = self.config['countries']
        timeframes = self.config['timeframes']
        overview = analysis_result.get("overview", {})
        
        html = """
        <!-- 市場方向ダッシュボード（ファーストビュー） -->
        <section class="mb-8 fade-in">
            <div class="sticky top-0 z-10 bg-white/95 backdrop-blur-sm border-b border-gray-200 py-4 mb-6">
                <h2 class="text-2xl font-bold text-gray-900 flex items-center">
                    <span class="mr-2">📊</span>
                    市場方向ダッシュボード
                </h2>
                <p class="text-xs text-gray-500 mt-1">各国・各期間の市場環境を一目で把握</p>
            </div>
            
            <!-- 国別カード（コンパクト） -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
"""
        
        for country_config in countries:
            country_code = country_config['code']
            country_name = country_config['name']
            directions = overview.get(country_code, {})
            country_result = analysis_result.get("countries", {}).get(country_code, {})
            
            html += f"""
                <div class="bg-white rounded-xl shadow-md border border-gray-200 overflow-hidden">
                    <div class="bg-gradient-to-r from-blue-50 to-indigo-50 px-4 py-3 border-b border-gray-200">
                        <h3 class="text-lg font-bold text-gray-900">{country_name}</h3>
                    </div>
                    <div class="p-4 space-y-3">
"""
            
            for timeframe in timeframes:
                timeframe_code = timeframe['code']
                timeframe_name = timeframe['name']
                
                direction = directions.get(timeframe_code, {})
                score = direction.get("score", 0)
                has_risk = direction.get("has_risk", False)
                label = self.score_labels.get(str(score), "→ 中立")
                
                # 1行要約を取得
                country_directions = country_result.get("directions", {})
                direction_data = country_directions.get(timeframe_code, {})
                one_line = self._get_one_line_summary(direction_data, timeframe_code)
                
                style = self._get_score_style(score)
                arrow_icon = self._get_arrow_icon(score)
                risk_badge = '<span class="ml-1 text-red-600">⚠️</span>' if has_risk else ''
                
                html += f"""
                        <div class="border-l-4 {style['border']} pl-3 py-2 bg-gray-50 rounded-r">
                            <div class="flex items-center justify-between mb-1">
                                <span class="text-xs font-medium text-gray-600">{timeframe_name}</span>
                                <span class="inline-flex items-center text-sm font-semibold {style['text']}">
                                    <span class="mr-1">{arrow_icon}</span>
                                    {label}
                                    {risk_badge}
                                </span>
                            </div>
                            <p class="text-xs text-gray-700 mt-1 line-clamp-2">{one_line}</p>
                            <a href="#country-{country_code}-{timeframe_code}" 
                               class="text-xs text-blue-600 hover:text-blue-800 mt-1 inline-block">
                                詳細を見る →
                            </a>
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
        """全体サマリーセクションを生成（ダッシュボード型：削除または最小化）"""
        # ダッシュボード型では、overview_cardsで既に表示しているため、このセクションは削除
        return ""
    
    def _format_number(self, value, decimals: int = 2, suffix: str = "") -> str:
        """数値をフォーマット"""
        if value is None:
            return "データなし"
        try:
            return f"{value:.{decimals}f}{suffix}"
        except (ValueError, TypeError):
            return str(value) if value else "データなし"
    
    def _generate_quantitative_data_section(self, country_data: Dict, country_code: str) -> str:
        """定量的データセクションを生成"""
        html = """
                <div class="mb-6 p-5 bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl border border-gray-200">
                    <h4 class="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                        <span class="mr-2">📈</span>
                        定量的補足データ
                    </h4>
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
"""
        
        # マクロ指標
        macro = country_data.get("macro", {})
        if macro.get("PMI") is not None:
            pmi = macro["PMI"]
            pmi_trend = "改善傾向" if pmi > 50 else "悪化傾向"
            pmi_class = "text-green-700" if pmi > 50 else "text-red-700"
            html += f"""
                        <div class="bg-white p-4 rounded-lg shadow-sm">
                            <p class="text-xs text-gray-600 mb-1">PMI（製造業）</p>
                            <p class="text-2xl font-bold {pmi_class}">{self._format_number(pmi, 1)}</p>
                            <p class="text-xs text-gray-500 mt-1">{pmi_trend}（50以上で拡大）</p>
                        </div>
"""
        
        if macro.get("CPI") is not None:
            cpi = macro["CPI"]
            cpi_trend = "適切" if 1.0 < cpi < 3.0 else ("高い" if cpi > 3.0 else "低い")
            cpi_class = "text-green-700" if 1.0 < cpi < 3.0 else ("text-red-700" if cpi > 5.0 else "text-yellow-700")
            html += f"""
                        <div class="bg-white p-4 rounded-lg shadow-sm">
                            <p class="text-xs text-gray-600 mb-1">CPI（前年同月比）</p>
                            <p class="text-2xl font-bold {cpi_class}">{self._format_number(cpi, 2, "%")}</p>
                            <p class="text-xs text-gray-500 mt-1">{cpi_trend}（目標: 1-3%）</p>
                        </div>
"""
        
        if macro.get("employment_rate") is not None:
            emp = macro["employment_rate"]
            html += f"""
                        <div class="bg-white p-4 rounded-lg shadow-sm">
                            <p class="text-xs text-gray-600 mb-1">雇用率</p>
                            <p class="text-2xl font-bold text-gray-800">{self._format_number(emp, 2, "%")}</p>
                            <p class="text-xs text-gray-500 mt-1">労働人口比</p>
                        </div>
"""
        
        # 金融指標
        financial = country_data.get("financial", {})
        if financial.get("policy_rate") is not None:
            rate = financial["policy_rate"]
            html += f"""
                        <div class="bg-white p-4 rounded-lg shadow-sm">
                            <p class="text-xs text-gray-600 mb-1">政策金利</p>
                            <p class="text-2xl font-bold text-gray-800">{self._format_number(rate, 2, "%")}</p>
                            <p class="text-xs text-gray-500 mt-1">中央銀行政策金利</p>
                        </div>
"""
        
        if financial.get("long_term_rate") is not None:
            ltr = financial["long_term_rate"]
            html += f"""
                        <div class="bg-white p-4 rounded-lg shadow-sm">
                            <p class="text-xs text-gray-600 mb-1">長期金利（10年債）</p>
                            <p class="text-2xl font-bold text-gray-800">{self._format_number(ltr, 2, "%")}</p>
                            <p class="text-xs text-gray-500 mt-1">10年物国債利回り</p>
                        </div>
"""
        
        # 指数データ
        indices = country_data.get("indices", {})
        if indices:
            first_index = list(indices.values())[0]
            index_code = list(indices.keys())[0]
            
            latest_price = first_index.get("latest_price")
            ma20 = first_index.get("ma20")
            ma200 = first_index.get("ma200")
            volatility = first_index.get("volatility")
            volume_ratio = first_index.get("volume_ratio")
            
            if latest_price:
                html += f"""
                        <div class="bg-white p-4 rounded-lg shadow-sm">
                            <p class="text-xs text-gray-600 mb-1">{index_code} 最新価格</p>
                            <p class="text-2xl font-bold text-gray-800">{self._format_number(latest_price, 2)}</p>
                            <p class="text-xs text-gray-500 mt-1">終値</p>
                        </div>
"""
            
            if ma200 and latest_price:
                price_vs_ma200 = ((latest_price - ma200) / ma200) * 100
                trend_class = "text-green-700" if price_vs_ma200 > 0 else "text-red-700"
                html += f"""
                        <div class="bg-white p-4 rounded-lg shadow-sm">
                            <p class="text-xs text-gray-600 mb-1">200日移動平均乖離率</p>
                            <p class="text-2xl font-bold {trend_class}">{self._format_number(price_vs_ma200, 2, "%")}</p>
                            <p class="text-xs text-gray-500 mt-1">長期トレンド指標</p>
                        </div>
"""
            
            if volatility:
                vol_class = "text-red-700" if volatility > 30 else ("text-yellow-700" if volatility > 20 else "text-green-700")
                html += f"""
                        <div class="bg-white p-4 rounded-lg shadow-sm">
                            <p class="text-xs text-gray-600 mb-1">ボラティリティ（年率）</p>
                            <p class="text-2xl font-bold {vol_class}">{self._format_number(volatility, 2, "%")}</p>
                            <p class="text-xs text-gray-500 mt-1">過去30日の標準偏差</p>
                        </div>
"""
            
            if volume_ratio:
                vol_ratio_class = "text-green-700" if volume_ratio > 1.2 else ("text-yellow-700" if volume_ratio > 0.8 else "text-gray-700")
                html += f"""
                        <div class="bg-white p-4 rounded-lg shadow-sm">
                            <p class="text-xs text-gray-600 mb-1">出来高比率</p>
                            <p class="text-2xl font-bold {vol_ratio_class}">{self._format_number(volume_ratio, 2, "倍")}</p>
                            <p class="text-xs text-gray-500 mt-1">30日平均との比較</p>
                        </div>
"""
        
        html += """
                    </div>
                </div>
"""
        
        # 株価指数の簡易グラフ（historical_pricesがある場合）
        if indices:
            first_index = list(indices.values())[0]
            index_code = list(indices.keys())[0]
            historical_prices = first_index.get("historical_prices", [])
            
            if historical_prices and len(historical_prices) > 0:
                # Chart.js用のデータを準備
                chart_id = f"chart_{country_code}_{index_code.replace('-', '_')}"
                chart_labels = [f"{i+1}日前" for i in range(len(historical_prices))][::-1]
                chart_data = historical_prices[::-1]  # 時系列順に並び替え
                
                html += f"""
                <div class="mt-4 p-4 bg-white rounded-lg border border-gray-200">
                    <h5 class="text-sm font-semibold text-gray-700 mb-3">{index_code} 価格推移（直近{len(historical_prices)}日）</h5>
                    <canvas id="{chart_id}" style="max-height: 200px;"></canvas>
                    <script>
                    (function() {{
                        const ctx = document.getElementById('{chart_id}');
                        if (ctx) {{
                            new Chart(ctx, {{
                                type: 'line',
                                data: {{
                                    labels: {json.dumps(chart_labels)},
                                    datasets: [{{
                                        label: '{index_code}',
                                        data: {json.dumps(chart_data)},
                                        borderColor: 'rgb(37, 99, 235)',
                                        backgroundColor: 'rgba(37, 99, 235, 0.1)',
                                        tension: 0.4,
                                        fill: true
                                    }}]
                                }},
                                options: {{
                                    responsive: true,
                                    maintainAspectRatio: true,
                                    plugins: {{
                                        legend: {{
                                            display: false
                                        }},
                                        tooltip: {{
                                            mode: 'index',
                                            intersect: false
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
                    }})();
                    </script>
                </div>
"""
        
        return html
    
    def _get_top_risks(self, risks: List[str], concrete_risks: List[str], max_count: int = 2) -> List[str]:
        """重要リスクを最大2つまで取得"""
        top_risks = []
        # LLM生成リスクを優先
        for risk in risks[:max_count]:
            if len(risk) <= 100:  # 短文のみ
                top_risks.append(risk)
        # 足りない場合は指標ベースリスクから追加
        if len(top_risks) < max_count:
            for risk in concrete_risks[:max_count - len(top_risks)]:
                if len(risk) <= 100:
                    top_risks.append(risk)
        return top_risks
    
    def generate_country_analysis(self, country_result: Dict, analysis_result: Dict) -> str:
        """国別分析セクションを生成（ダッシュボード型：コンパクト）"""
        country_name = country_result["name"]
        country_code = country_result["code"]
        directions = country_result["directions"]
        country_data = country_result.get("data", {})
        
        html = f"""
        <!-- {country_name} 市場判断（ダッシュボード型） -->
        <section class="mb-8 fade-in">
            <h2 class="text-2xl font-bold text-gray-900 mb-4 flex items-center">
                <span class="mr-2">🌍</span>
                {country_name}
            </h2>
"""
        
        for timeframe in self.config['timeframes']:
            timeframe_code = timeframe['code']
            timeframe_name = timeframe['name']
            accordion_id = f"accordion-{country_code}-{timeframe_code}"
            
            direction = directions.get(timeframe_code, {})
            score = direction.get("score", 0)
            label = direction.get("direction_label", direction.get("label", "中立"))
            has_risk = direction.get("has_risk", False)
            
            style = self._get_score_style(score)
            arrow_icon = self._get_arrow_icon(score)
            risk_badge = '<span class="ml-2 text-red-600">⚠️</span>' if has_risk else ''
            
            direction_data = directions.get(timeframe_code, {})
            
            # 1行要約
            one_line = self._get_one_line_summary(direction_data, timeframe_code)
            
            # 重要リスク（最大2つ）
            risks = direction_data.get("risks", [])
            concrete_risks = []
            
            # 簡易的なリスク抽出（詳細は折りたたみ内に）
            macro = country_data.get("macro", {})
            if macro.get("PMI") is not None and macro["PMI"] < 50:
                concrete_risks.append(f"PMI {macro['PMI']:.1f}（50未満）")
            if macro.get("CPI") is not None and macro["CPI"] > 5.0:
                concrete_risks.append(f"CPI {macro['CPI']:.1f}%（高水準）")
            
            top_risks = self._get_top_risks(risks, concrete_risks, max_count=2)
            
            html += f"""
            <div id="country-{country_code}-{timeframe_code}" class="bg-white rounded-xl shadow-md border border-gray-200 mb-4 overflow-hidden">
                <!-- レベル1：常時表示 -->
                <div class="p-4 border-b border-gray-100">
                    <div class="flex items-center justify-between mb-2">
                        <div class="flex items-center space-x-3">
                            <span class="text-sm font-medium text-gray-600">{timeframe_name}</span>
                            <span class="inline-flex items-center px-3 py-1 rounded-lg {style['bg']} {style['text']} text-sm font-semibold">
                                <span class="mr-1">{arrow_icon}</span>
                                {label}
                                {risk_badge}
                            </span>
                        </div>
                        <button onclick="toggleAccordion('{accordion_id}')" 
                                class="text-sm text-blue-600 hover:text-blue-800 font-medium">
                            <span id="{accordion_id}-icon">▼</span> 詳細
                        </button>
                    </div>
                    <p class="text-sm text-gray-700 mt-2 line-clamp-2">{one_line}</p>
"""
            
            # 重要リスク（最大2つ、常時表示）
            if top_risks:
                html += """
                    <div class="mt-3 flex flex-wrap gap-2">
"""
                for risk in top_risks:
                    html += f"""
                        <span class="inline-flex items-center px-2 py-1 bg-red-50 text-red-700 text-xs rounded border border-red-200">
                            ⚠️ {risk[:40]}{'...' if len(risk) > 40 else ''}
                        </span>
"""
                html += """
                    </div>
"""
            
            html += """
                </div>
                
                <!-- レベル2：クリックで展開 -->
                <div id="{accordion_id}" class="hidden">
                    <div class="p-4 bg-gray-50 space-y-4">
"""
            
            # 判断理由（箇条書き、最大5行）
            key_factors = direction_data.get("key_factors", [])
            if key_factors:
                html += """
                        <div>
                            <h4 class="text-sm font-semibold text-gray-800 mb-2">判断理由</h4>
                            <ul class="text-xs text-gray-700 space-y-1 list-disc list-inside">
"""
                for factor in key_factors[:5]:  # 最大5つ
                    # 1行に収まるように短縮
                    short_factor = factor[:80] + "..." if len(factor) > 80 else factor
                    html += f"""
                                <li>{short_factor}</li>
"""
                html += """
                            </ul>
                        </div>
"""
            
            # 要点（マクロ/金融/テクニカル/構造）
            html += """
                        <div class="grid grid-cols-2 gap-3">
"""
            
            # マクロ要点
            macro_summary = []
            if macro.get("PMI") is not None:
                macro_summary.append(f"PMI: {macro['PMI']:.1f}")
            if macro.get("CPI") is not None:
                macro_summary.append(f"CPI: {macro['CPI']:.1f}%")
            
            if macro_summary:
                html += f"""
                            <div class="bg-white p-3 rounded border border-gray-200">
                                <p class="text-xs font-semibold text-gray-600 mb-1">マクロ</p>
                                <p class="text-xs text-gray-700">{', '.join(macro_summary)}</p>
                            </div>
"""
            
            # 金融要点
            financial = country_data.get("financial", {})
            financial_summary = []
            if financial.get("policy_rate") is not None:
                financial_summary.append(f"政策金利: {financial['policy_rate']:.2f}%")
            if financial.get("long_term_rate") is not None:
                financial_summary.append(f"長期金利: {financial['long_term_rate']:.2f}%")
            
            if financial_summary:
                html += f"""
                            <div class="bg-white p-3 rounded border border-gray-200">
                                <p class="text-xs font-semibold text-gray-600 mb-1">金融</p>
                                <p class="text-xs text-gray-700">{', '.join(financial_summary)}</p>
                            </div>
"""
            
            # テクニカル要点
            indices = country_data.get("indices", {})
            if indices:
                first_index = list(indices.values())[0]
                technical_summary = []
                if first_index.get("price_vs_ma200"):
                    technical_summary.append(f"MA200乖離: {first_index['price_vs_ma200']:+.1f}%")
                if first_index.get("volatility"):
                    technical_summary.append(f"ボラ: {first_index['volatility']:.1f}%")
                
                if technical_summary:
                    html += f"""
                            <div class="bg-white p-3 rounded border border-gray-200">
                                <p class="text-xs font-semibold text-gray-600 mb-1">テクニカル</p>
                                <p class="text-xs text-gray-700">{', '.join(technical_summary)}</p>
                            </div>
"""
            
            html += """
                        </div>
                        
                        <!-- レベル3：別ページリンク -->
                        <div class="pt-3 border-t border-gray-200">
                            <a href="./logs/{country_code}-{timeframe_code}.html" 
                               class="inline-flex items-center text-xs text-blue-600 hover:text-blue-800 font-medium">
                                📝 詳細な思考ログを見る →
                            </a>
                        </div>
                    </div>
                </div>
            </div>
"""
        
        html += """
        </section>
        
        <script>
        function toggleAccordion(id) {
            const element = document.getElementById(id);
            const icon = document.getElementById(id + '-icon');
            if (element.classList.contains('hidden')) {
                element.classList.remove('hidden');
                icon.textContent = '▲';
            } else {
                element.classList.add('hidden');
                icon.textContent = '▼';
            }
        }
        </script>
"""
        return html
    
    def generate_sector_analysis(self, sectors: List[Dict]) -> str:
        """セクター分析セクションを生成（ダッシュボード型：コンパクト）"""
        if not sectors:
            return ""
        
        html = """
        <!-- 注目セクター（ダッシュボード型） -->
        <section class="mb-8 fade-in">
            <h2 class="text-2xl font-bold text-gray-900 mb-4 flex items-center">
                <span class="mr-2">📈</span>
                注目セクター
            </h2>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
"""
        
        for i, sector in enumerate(sectors[:3], 1):
            sector_id = f"sector-{i}"
            reason = sector.get('reason', '')
            short_reason = reason[:60] + "..." if len(reason) > 60 else reason
            
            html += f"""
                <div class="bg-white rounded-xl shadow-md border border-gray-200 overflow-hidden">
                    <div class="p-4">
                        <div class="flex items-center mb-2">
                            <span class="flex items-center justify-center w-6 h-6 rounded-full bg-blue-100 text-blue-600 font-bold text-sm mr-2">
                                {i}
                            </span>
                            <h3 class="text-base font-semibold text-gray-900">{sector.get('name', 'セクター')}</h3>
                        </div>
                        <p class="text-xs text-gray-700 line-clamp-2 mb-3">{short_reason}</p>
                        <button onclick="toggleSectorDetail('{sector_id}')" 
                                class="text-xs text-blue-600 hover:text-blue-800 font-medium">
                            <span id="{sector_id}-icon">▼</span> 詳細
                        </button>
                    </div>
                    <div id="{sector_id}" class="hidden p-4 bg-gray-50 border-t border-gray-200">
"""
            
            if sector.get('reason') and len(sector['reason']) > 60:
                html += f"""
                        <p class="text-xs text-gray-700 mb-3">{sector['reason']}</p>
"""
            
            if sector.get('related_fields'):
                fields = sector['related_fields']
                if isinstance(fields, str):
                    fields = [fields]
                html += """
                        <div class="mb-2">
                            <p class="text-xs font-medium text-gray-600 mb-1">波及分野</p>
                            <div class="flex flex-wrap gap-1">
"""
                for field in fields:
                    html += f"""
                                <span class="px-2 py-0.5 bg-orange-100 text-orange-700 text-xs rounded">{field}</span>
"""
                html += """
                            </div>
                        </div>
"""
            
            if sector.get('timeframe'):
                html += f"""
                        <p class="text-xs text-gray-600">
                            <span class="font-medium">期間:</span> {sector['timeframe']}
                        </p>
"""
            
            html += """
                    </div>
                </div>
"""
        
        html += """
            </div>
        </section>
        
        <script>
        function toggleSectorDetail(id) {
            const element = document.getElementById(id);
            const icon = document.getElementById(id + '-icon');
            if (element.classList.contains('hidden')) {
                element.classList.remove('hidden');
                icon.textContent = '▲';
            } else {
                element.classList.add('hidden');
                icon.textContent = '▼';
            }
        }
        </script>
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
        """フルページを生成（ダッシュボード型）"""
        html = self._generate_header()
        
        # レベル1：ファーストビュー（市場方向サマリー）
        html += self.generate_overview_cards(analysis_result)
        
        # レベル1：注目セクター（あれば）
        if sectors:
            html += self.generate_sector_analysis(sectors)
        
        # レベル2：国別分析（詳細は折りたたみ）
        for country_code, country_result in analysis_result["countries"].items():
            html += self.generate_country_analysis(country_result, analysis_result)
        
        # レベル3：銘柄情報（別セクション、必要に応じて）
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


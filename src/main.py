"""
メイン実行スクリプト
データ取得、分析、LLM生成、HTML出力を統合
"""

import sys
import os
import logging
import json
from pathlib import Path
from datetime import datetime

# パスを追加
sys.path.insert(0, str(Path(__file__).parent))

from data_fetcher import DataFetcher
from market_analyzer import MarketAnalyzer
from llm_generator import LLMGenerator
from html_generator import HTMLGenerator

# ロギング設定
Path("logs").mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/main.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def main():
    """メイン処理"""
    try:
        logger.info("=== 株式市場分析・銘柄選定アプリ開始 ===")
        
        # ログディレクトリ作成
        Path("logs").mkdir(parents=True, exist_ok=True)
        
        # 1. データ取得
        logger.info("ステップ1: 市場データ取得")
        fetcher = DataFetcher()
        market_data = fetcher.fetch_all_data()
        logger.info(f"データ取得完了: {len(market_data['countries'])}ヶ国")
        
        # データを保存（デバッグ用）
        output_dir = Path("outputs")
        output_dir.mkdir(parents=True, exist_ok=True)
        with open(output_dir / "market_data.json", 'w', encoding='utf-8') as f:
            json.dump(market_data, f, ensure_ascii=False, indent=2)
        
        # 2. 市場分析（ルールベース：補助的）
        logger.info("ステップ2: 市場分析（ルールベース）")
        analyzer = MarketAnalyzer()
        rule_based_result = analyzer.analyze_all_markets(market_data)
        logger.info("ルールベース分析完了")
        
        # 3. LLM生成（Groq API）
        logger.info("ステップ3: LLM市場方向感分析（Groq）")
        llm = LLMGenerator()
        
        # 分析結果の構造を初期化
        analysis_result = {
            "overview": {},
            "countries": {},
            "timestamp": rule_based_result["timestamp"]
        }
        
        # 各国×期間ごとにLLMで市場方向感を分析
        for country_code, country_data in market_data["countries"].items():
            country_result = {
                "name": country_data["name"],
                "code": country_code,
                "directions": {},
                "data": country_data,
                "analysis": {}
            }
            
            for timeframe in analyzer.config['timeframes']:
                timeframe_code = timeframe['code']
                timeframe_name = timeframe['name']
                
                logger.info(f"LLM分析中: {country_code} - {timeframe_code}")
                
                # Groq LLMで市場方向感を分析
                llm_direction = llm.generate_market_direction(
                    country_data,
                    timeframe_code,
                    timeframe_name
                )
                
                # ルールベース結果も保持（思考ログ用）
                rule_based_direction = rule_based_result["countries"].get(country_code, {}).get("directions", {}).get(timeframe_code, {})
                
                # LLM結果をメインとして使用
                direction_result = {
                    "score": llm_direction.get("score", 0),
                    "direction_label": llm_direction.get("direction_label", "中立"),
                    "summary": llm_direction.get("summary", ""),
                    "premise": llm_direction.get("premise", ""),  # 前提条件を追加
                    "key_factors": llm_direction.get("key_factors", []),
                    "risks": llm_direction.get("risks", []),
                    "turning_points": llm_direction.get("turning_points", []),
                    # 後方互換性のため
                    "label": llm_direction.get("direction_label", "中立"),
                    "has_risk": len(llm_direction.get("risks", [])) > 0,
                    # ルールベース結果も保持（思考ログ用）
                    "rule_based_components": rule_based_direction.get("components", {})
                }
                
                country_result["directions"][timeframe_code] = direction_result
                
                # 分析文章（後方互換性のため）
                country_result["analysis"][timeframe_code] = {
                    "結論": llm_direction.get("summary", ""),
                    "前提": llm_direction.get("premise", "") or "、".join(llm_direction.get("key_factors", [])),
                    "最大リスク": "、".join(llm_direction.get("risks", [])),
                    "転換シグナル": "、".join(llm_direction.get("turning_points", []))
                }
                
                # Overview用にスコアを記録
                if country_code not in analysis_result["overview"]:
                    analysis_result["overview"][country_code] = {}
                analysis_result["overview"][country_code][timeframe_code] = {
                    "score": direction_result["score"],
                    "has_risk": direction_result["has_risk"]
                }
                
                logger.info(f"LLM分析完了: {country_code} - {timeframe_code} (スコア: {direction_result['score']})")
            
            analysis_result["countries"][country_code] = country_result
        
        # セクター分析生成
        logger.info("セクター分析生成")
        sectors = llm.generate_sector_analysis(market_data)
        logger.info(f"セクター分析完了: {len(sectors)}件")
        
        # 4. 銘柄推奨生成
        logger.info("ステップ4: 銘柄推奨生成")
        recommendations = {}
        
        for country_config in analyzer.config['countries']:
            country_code = country_config['code']
            country_name = country_config['name']
            
            if country_code not in ["JP", "US"]:
                continue
            
            logger.info(f"銘柄データ取得: {country_name}")
            stocks_data = []
            
            # ユニバースから銘柄を取得
            for universe_name in country_config.get('universe', []):
                tickers = fetcher.get_stock_universe(universe_name, country_code)
                
                for ticker in tickers[:20]:  # 各ユニバースから最大20銘柄
                    stock_data = fetcher.get_stock_data(ticker)
                    if stock_data:
                        stocks_data.append(stock_data)
            
            # LLMで推奨を生成
            if stocks_data:
                stock_recommendations = llm.generate_stock_recommendations(stocks_data, country_code)
                recommendations[country_code] = stock_recommendations
                logger.info(f"銘柄推奨完了: {country_name} ({len(stock_recommendations)}件)")
        
        # 5. HTML生成
        logger.info("ステップ6: HTML生成")
        html_generator = HTMLGenerator()
        
        # メインページ
        main_html = html_generator.generate_full_page(analysis_result, sectors, recommendations)
        html_generator.save_html(main_html, "index.html")
        logger.info("HTMLメインページ生成完了")
        
        # 詳細ページ
        for country_code, country_result in analysis_result["countries"].items():
            directions = country_result["directions"]
            analysis_dict = country_result.get("analysis", {})
            
            for timeframe_code in directions.keys():
                analysis_text = analysis_dict.get(timeframe_code, {})
                detail_html = html_generator.generate_detail_page(
                    country_result,
                    timeframe_code,
                    analysis_text
                )
                html_generator.save_detail_page(detail_html, country_code, timeframe_code)
                
                # 思考ログ生成
                direction_data = directions[timeframe_code]
                thought_log_html = html_generator.generate_thought_log(
                    country_code,
                    timeframe_code,
                    country_result["data"],
                    direction_data
                )
                html_generator.save_thought_log(thought_log_html, country_code, timeframe_code)
        
        logger.info("HTML詳細ページ・思考ログ生成完了")
        
        # 結果を保存
        result = {
            "timestamp": datetime.now().isoformat(),
            "analysis_result": analysis_result,
            "sectors": sectors,
            "recommendations": recommendations
        }
        
        with open(output_dir / "analysis_result.json", 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info("=== 処理完了 ===")
        
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()


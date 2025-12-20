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
from state_mapper import StateMapper
from market_judgment import MarketJudgment
from sector_recommender import SectorRecommender

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
        
        # 2. 状態マッピング（生データ → 状態）
        logger.info("ステップ2: 状態マッピング（生データ → 状態）")
        state_mapper = StateMapper()
        market_judgment = MarketJudgment()
        sector_recommender = SectorRecommender()
        analyzer = MarketAnalyzer()
        llm = LLMGenerator()
        
        # 分析結果の構造を初期化
        analysis_result = {
            "overview": {},
            "countries": {},
            "timestamp": datetime.now().isoformat()
        }
        
        # 各国×期間ごとに分析
        for country_code, country_data in market_data["countries"].items():
            country_result = {
                "name": country_data["name"],
                "code": country_code,
                "directions": {},
                "data": country_data,
                "analysis": {}
            }
            
            # 状態をマッピング
            states = state_mapper.map_all_states(country_data)
            logger.info(f"状態マッピング完了: {country_code} - {states}")
            
            for timeframe in analyzer.config['timeframes']:
                timeframe_code = timeframe['code']
                timeframe_name = timeframe['name']
                
                logger.info(f"市場判断中: {country_code} - {timeframe_code}")
                
                # ルールベースで市場判断を決定
                judgment = market_judgment.judge_market_view(states, timeframe_code)
                market_view = judgment["view"]
                market_score = judgment["score"]
                reasoning = judgment["reasoning"]
                key_states = judgment["key_states"]
                
                logger.info(f"市場判断確定: {country_code} - {timeframe_code} (判断: {market_view}, スコア: {market_score})")
                
                # LLMで要約・言語化（判断は確定済み）
                llm_result = llm.generate_market_direction(
                    country_code=country_code,
                    country_name=country_data["name"],
                    timeframe_code=timeframe_code,
                    timeframe_name=timeframe_name,
                    states=states,
                    market_view=market_view,
                    market_score=market_score,
                    reasoning=reasoning,
                    key_states=key_states
                )
                
                # 判断結果を統合
                view_label_map = {
                    "strong_bullish": "超強気",
                    "bullish": "やや強気",
                    "neutral": "中立",
                    "bearish": "やや弱気",
                    "strong_bearish": "弱気"
                }
                direction_label = view_label_map.get(market_view, "中立")
                
                direction_result = {
                    "score": market_score,
                    "direction_label": direction_label,
                    "view": market_view,
                    "summary": llm_result.get("summary", ""),
                    "premise": llm_result.get("premise", ""),
                    "risks": llm_result.get("risks", []),
                    "turning_points": llm_result.get("turning_points", []),
                    "reasoning": reasoning,
                    "key_states": key_states,
                    # 後方互換性のため
                    "label": direction_label,
                    "has_risk": len(llm_result.get("risks", [])) > 0,
                    "key_factors": reasoning  # 判断理由をkey_factorsとして使用
                }
                
                country_result["directions"][timeframe_code] = direction_result
                
                # 分析文章（後方互換性のため）
                country_result["analysis"][timeframe_code] = {
                    "結論": llm_result.get("summary", ""),
                    "前提": llm_result.get("premise", ""),
                    "最大リスク": "、".join(llm_result.get("risks", [])),
                    "転換シグナル": "、".join(llm_result.get("turning_points", []))
                }
                
                # Overview用にスコアを記録
                if country_code not in analysis_result["overview"]:
                    analysis_result["overview"][country_code] = {}
                analysis_result["overview"][country_code][timeframe_code] = {
                    "score": market_score,
                    "has_risk": direction_result["has_risk"],
                    "view": market_view
                }
                
                logger.info(f"分析完了: {country_code} - {timeframe_code} (スコア: {market_score})")
            
            analysis_result["countries"][country_code] = country_result
        
        # セクター分析生成（テーマベース）
        logger.info("セクター分析生成（テーマベース）")
        sectors = []
        for country_code, country_data in market_data["countries"].items():
            states = state_mapper.map_all_states(country_data)
            for timeframe in analyzer.config['timeframes']:
                timeframe_code = timeframe['code']
                country_sectors = sector_recommender.recommend_sectors(states, timeframe_code)
                sectors.extend(country_sectors)
        
        # 重複を除去
        unique_sectors = {}
        for sector in sectors:
            name = sector["name"]
            if name not in unique_sectors:
                unique_sectors[name] = sector
        sectors = list(unique_sectors.values())[:3]  # 上位3つ
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


"""
バックテストスクリプト
過去のデータで分析機能を検証
"""

import sys
import os
from pathlib import Path

# パスを追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

import json
import logging
from datetime import datetime, timedelta

from data_fetcher import DataFetcher
from market_analyzer import MarketAnalyzer
from llm_generator import LLMGenerator
from markdown_generator import MarkdownGenerator
from html_generator import HTMLGenerator

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def run_backtest():
    """バックテストを実行"""
    try:
        logger.info("=== バックテスト開始 ===")
        
        # 必要なディレクトリを作成
        (project_root / "logs").mkdir(parents=True, exist_ok=True)
        (project_root / "outputs").mkdir(parents=True, exist_ok=True)
        (project_root / "docs").mkdir(parents=True, exist_ok=True)
        (project_root / "docs" / "details").mkdir(parents=True, exist_ok=True)
        (project_root / "docs" / "logs").mkdir(parents=True, exist_ok=True)
        
        # 1. データ取得テスト
        logger.info("テスト1: データ取得")
        fetcher = DataFetcher(str(project_root / "config" / "config.yml"))
        market_data = fetcher.fetch_all_data()
        
        assert "countries" in market_data, "市場データに'countries'キーがありません"
        assert len(market_data["countries"]) > 0, "国別データが取得できていません"
        logger.info(f"✓ データ取得成功: {len(market_data['countries'])}ヶ国")
        
        # データの構造を確認
        for country_code, country_data in market_data["countries"].items():
            assert "name" in country_data, f"{country_code}: 'name'キーがありません"
            assert "code" in country_data, f"{country_code}: 'code'キーがありません"
            assert "indices" in country_data, f"{country_code}: 'indices'キーがありません"
        logger.info("✓ データ構造検証完了")
        
        # 2. 市場分析テスト
        logger.info("テスト2: 市場分析")
        analyzer = MarketAnalyzer(str(project_root / "config" / "config.yml"))
        analysis_result = analyzer.analyze_all_markets(market_data)
        
        assert "overview" in analysis_result, "分析結果に'overview'キーがありません"
        assert "countries" in analysis_result, "分析結果に'countries'キーがありません"
        
        # Overviewテーブルの確認
        overview = analysis_result["overview"]
        for country_code in market_data["countries"].keys():
            assert country_code in overview, f"{country_code}: overviewに含まれていません"
            
            country_overview = overview[country_code]
            for timeframe in ["short", "medium", "long"]:
                assert timeframe in country_overview, f"{country_code}-{timeframe}: 期間データがありません"
                
                direction = country_overview[timeframe]
                assert "score" in direction, f"{country_code}-{timeframe}: スコアがありません"
                assert isinstance(direction["score"], int), f"{country_code}-{timeframe}: スコアが整数ではありません"
                assert -2 <= direction["score"] <= 2, f"{country_code}-{timeframe}: スコアが範囲外です"
        
        logger.info("✓ 市場分析成功")
        
        # 3. LLM文章生成テスト（フォールバック）
        logger.info("テスト3: 文章生成（フォールバック）")
        llm = LLMGenerator(str(project_root / "config" / "config.yml"))
        
        # 各国×期間ごとに分析文章を生成
        for country_code, country_result in analysis_result["countries"].items():
            country_data = country_result["data"]
            directions = country_result["directions"]
            
            country_result["analysis"] = {}
            
            for timeframe_code, direction_data in directions.items():
                timeframe_name = next(
                    (tf['name'] for tf in analyzer.config['timeframes'] if tf['code'] == timeframe_code),
                    timeframe_code
                )
                
                analysis_text = llm.generate_market_analysis(
                    country_data,
                    direction_data,
                    timeframe_name
                )
                
                # 分析結果の構造確認
                assert "結論" in analysis_text, f"{country_code}-{timeframe_code}: '結論'がありません"
                assert "前提" in analysis_text, f"{country_code}-{timeframe_code}: '前提'がありません"
                assert "最大リスク" in analysis_text, f"{country_code}-{timeframe_code}: '最大リスク'がありません"
                assert "転換シグナル" in analysis_text, f"{country_code}-{timeframe_code}: '転換シグナル'がありません"
                
                country_result["analysis"][timeframe_code] = analysis_text
        
        logger.info("✓ 文章生成成功")
        
        # 4. セクター分析テスト
        logger.info("テスト4: セクター分析")
        sectors = llm.generate_sector_analysis(market_data)
        assert isinstance(sectors, list), "セクター分析がリストではありません"
        assert len(sectors) > 0, "セクター分析が空です"
        logger.info(f"✓ セクター分析成功: {len(sectors)}件")
        
        # 5. 銘柄推奨テスト
        logger.info("テスト5: 銘柄推奨")
        recommendations = {}
        
        for country_config in analyzer.config['countries']:
            country_code = country_config['code']
            
            if country_code not in ["JP", "US"]:
                continue
            
            stocks_data = []
            for universe_name in country_config.get('universe', []):
                tickers = fetcher.get_stock_universe(universe_name, country_code)
                
                for ticker in tickers[:5]:  # テスト用に5銘柄に制限
                    stock_data = fetcher.get_stock_data(ticker)
                    if stock_data:
                        stocks_data.append(stock_data)
            
            if stocks_data:
                stock_recommendations = llm.generate_stock_recommendations(stocks_data, country_code)
                recommendations[country_code] = stock_recommendations
                
                assert len(stock_recommendations) > 0, f"{country_code}: 推奨銘柄が生成されていません"
                
                for rec in stock_recommendations:
                    assert "ticker" in rec, "銘柄推奨に'ticker'がありません"
                    assert "name" in rec, "銘柄推奨に'name'がありません"
        
        logger.info(f"✓ 銘柄推奨成功: {len(recommendations)}ヶ国")
        
        # 6. Markdown生成テスト
        logger.info("テスト6: Markdown生成")
        md_generator = MarkdownGenerator(str(project_root / "config" / "config.yml"))
        
        # メインページ生成
        main_content = md_generator.generate_full_page(analysis_result, sectors, recommendations)
        assert len(main_content) > 0, "メインページコンテンツが空です"
        assert "Market Direction Overview" in main_content, "Overviewテーブルが含まれていません"
        assert "全体サマリー" in main_content, "全体サマリーが含まれていません"
        
        md_generator.save_markdown(main_content, "test-index.md")
        test_file = project_root / "docs" / "test-index.md"
        assert test_file.exists(), "テストMarkdownファイルが生成されていません"
        
        logger.info("✓ Markdown生成成功")
        
        # 7. 詳細ページ生成テスト
        logger.info("テスト7: 詳細ページ生成")
        for country_code, country_result in analysis_result["countries"].items():
            directions = country_result["directions"]
            analysis_dict = country_result.get("analysis", {})
            
            for timeframe_code in list(directions.keys())[:1]:  # テスト用に1つだけ
                analysis_text = analysis_dict.get(timeframe_code, {})
                detail_content = md_generator.generate_detail_page(
                    country_result,
                    timeframe_code,
                    analysis_text
                )
                assert len(detail_content) > 0, f"{country_code}-{timeframe_code}: 詳細ページが空です"
                
                md_generator.save_detail_page(detail_content, country_code, timeframe_code)
        
        logger.info("✓ 詳細ページ生成成功")
        
        # 8. 思考ログ生成テスト
        logger.info("テスト8: 思考ログ生成")
        for country_code, country_result in list(analysis_result["countries"].items())[:1]:  # テスト用に1つだけ
            directions = country_result["directions"]
            
            for timeframe_code in list(directions.keys())[:1]:  # テスト用に1つだけ
                direction_data = directions[timeframe_code]
                thought_log_content = md_generator.generate_thought_log(
                    country_code,
                    timeframe_code,
                    country_result["data"],
                    direction_data
                )
                assert len(thought_log_content) > 0, f"{country_code}-{timeframe_code}: 思考ログが空です"
                
                md_generator.save_thought_log(thought_log_content, country_code, timeframe_code)
        
        logger.info("✓ 思考ログ生成成功")
        
        # 9. HTML生成テスト
        logger.info("テスト9: HTML生成")
        html_generator = HTMLGenerator(str(project_root / "config" / "config.yml"))
        
        # メインページ生成
        main_html = html_generator.generate_full_page(analysis_result, sectors, recommendations)
        assert len(main_html) > 0, "メインHTMLコンテンツが空です"
        assert "Market Direction Overview" in main_html, "Overviewセクションが含まれていません"
        assert "全体サマリー" in main_html, "全体サマリーが含まれていません"
        assert "<!DOCTYPE html>" in main_html, "HTMLドキュメントタイプが含まれていません"
        assert "tailwindcss.com" in main_html, "Tailwind CSSが含まれていません"
        
        html_generator.save_html(main_html, "test-index.html")
        test_html_file = project_root / "docs" / "test-index.html"
        assert test_html_file.exists(), "テストHTMLファイルが生成されていません"
        
        logger.info("✓ HTMLメインページ生成成功")
        
        # 詳細ページ生成テスト
        logger.info("テスト10: HTML詳細ページ生成")
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
                assert len(detail_html) > 0, f"{country_code}-{timeframe_code}: HTML詳細ページが空です"
                assert "<!DOCTYPE html>" in detail_html, "HTMLドキュメントタイプが含まれていません"
                
                html_generator.save_detail_page(detail_html, country_code, timeframe_code)
        
        logger.info("✓ HTML詳細ページ生成成功")
        
        # 思考ログ生成テスト
        logger.info("テスト11: HTML思考ログ生成")
        for country_code, country_result in analysis_result["countries"].items():
            directions = country_result["directions"]
            
            for timeframe_code in directions.keys():
                direction_data = directions[timeframe_code]
                thought_log_html = html_generator.generate_thought_log(
                    country_code,
                    timeframe_code,
                    country_result["data"],
                    direction_data
                )
                assert len(thought_log_html) > 0, f"{country_code}-{timeframe_code}: HTML思考ログが空です"
                assert "<!DOCTYPE html>" in thought_log_html, "HTMLドキュメントタイプが含まれていません"
                
                html_generator.save_thought_log(thought_log_html, country_code, timeframe_code)
        
        logger.info("✓ HTML思考ログ生成成功")
        
        # 結果サマリー
        logger.info("\n=== バックテスト結果 ===")
        logger.info("✓ 全テスト通過")
        logger.info(f"- 対象国: {len(market_data['countries'])}ヶ国")
        logger.info(f"- 分析期間: {len(analyzer.config['timeframes'])}期間")
        logger.info(f"- セクター分析: {len(sectors)}件")
        logger.info(f"- 銘柄推奨: {sum(len(v) for v in recommendations.values())}件")
        logger.info("========================\n")
        
        return True
        
    except AssertionError as e:
        logger.error(f"❌ テスト失敗: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ エラーが発生しました: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = run_backtest()
    sys.exit(0 if success else 1)


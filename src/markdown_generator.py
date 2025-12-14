"""
Markdown生成モジュール
分析結果をMarkdown形式で出力する
"""

import yaml
import json
from typing import Dict, List
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class MarkdownGenerator:
    """Markdown生成クラス"""
    
    def __init__(self, config_path: str = "config/config.yml"):
        """初期化"""
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.output_dir = Path(self.config['output']['pages_directory'])
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.score_labels = self.config['score_labels']
    
    def generate_overview_table(self, analysis_result: Dict) -> str:
        """
        Overview テーブルを生成
        
        Args:
            analysis_result: 分析結果
        
        Returns:
            Markdownテーブル
        """
        countries = self.config['countries']
        timeframes = self.config['timeframes']
        
        # テーブルヘッダー
        header = "| 国 | " + " | ".join([tf['name'] for tf in timeframes]) + " |\n"
        separator = "|" + "|".join(["---"] * (len(timeframes) + 1)) + "|\n"
        
        # テーブルボディ
        rows = []
        overview = analysis_result.get("overview", {})
        
        for country_config in countries:
            country_code = country_config['code']
            country_name = country_config['name']
            
            cells = [country_name]
            for timeframe in timeframes:
                timeframe_code = timeframe['code']
                
                direction = overview.get(country_code, {}).get(timeframe_code, {})
                score = direction.get("score", 0)
                has_risk = direction.get("has_risk", False)
                
                label = self.score_labels.get(str(score), "→ 中立")
                risk_icon = " ⚠" if has_risk else ""
                
                # リンク付きセル（詳細ページへ）
                detail_link = f"[{label}{risk_icon}](./details/{country_code}-{timeframe_code}.md)"
                cells.append(detail_link)
            
            rows.append("| " + " | ".join(cells) + " |\n")
        
        return "## Market Direction Overview\n\n" + header + separator + "".join(rows) + "\n"
    
    def generate_summary(self, analysis_result: Dict) -> str:
        """
        全体サマリーを生成
        
        Args:
            analysis_result: 分析結果
        
        Returns:
            Markdown形式のサマリー
        """
        # 簡易的なサマリー生成
        date_str = datetime.now().strftime("%Y年%m月%d日")
        
        summary = f"""## 全体サマリー

{date_str}の市場環境を要約します。

"""
        
        # 各国の主要なスコアを集計
        overview = analysis_result.get("overview", {})
        country_summaries = []
        
        for country_code, directions in overview.items():
            country_result = analysis_result["countries"].get(country_code, {})
            country_name = country_result.get("name", country_code)
            
            # 中期スコアを代表値として使用
            medium_score = directions.get("medium", {}).get("score", 0)
            label = self.score_labels.get(str(medium_score), "中立")
            
            country_summaries.append(f"- **{country_name}**: {label}")
        
        summary += "\n".join(country_summaries) + "\n\n"
        
        return summary
    
    def generate_country_analysis(self, country_result: Dict, analysis_result: Dict) -> str:
        """
        国別分析セクションを生成
        
        Args:
            country_result: 国別分析結果
            analysis_result: 全体分析結果
        
        Returns:
            Markdown形式の分析
        """
        country_name = country_result["name"]
        country_code = country_result["code"]
        directions = country_result["directions"]
        
        section = f"## {country_name} 市場判断\n\n"
        
        for timeframe in self.config['timeframes']:
            timeframe_code = timeframe['code']
            timeframe_name = timeframe['name']
            
            direction = directions.get(timeframe_code, {})
            score = direction.get("score", 0)
            label = direction.get("label", "中立")
            has_risk = direction.get("has_risk", False)
            
            section += f"### {timeframe_name} ({label}"
            if has_risk:
                section += " ⚠"
            section += ")\n\n"
            
            # LLM生成された分析を含める（ある場合）
            analysis_text = country_result.get("analysis", {}).get(timeframe_code, {})
            
            if analysis_text.get("結論"):
                section += f"#### 結論\n\n{analysis_text['結論']}\n\n"
            if analysis_text.get("前提"):
                section += f"#### 前提\n\n{analysis_text['前提']}\n\n"
            if analysis_text.get("最大リスク"):
                section += f"#### 最大リスク\n\n{analysis_text['最大リスク']}\n\n"
            if analysis_text.get("転換シグナル"):
                section += f"#### 転換シグナル\n\n{analysis_text['転換シグナル']}\n\n"
            
            # 思考ログへのリンク
            section += f"[思考ログ](./logs/{country_code}-{timeframe_code}.md)\n\n"
            
            section += "---\n\n"
        
        return section
    
    def generate_sector_analysis(self, sectors: List[Dict]) -> str:
        """
        セクター分析セクションを生成
        
        Args:
            sectors: セクター分析リスト
        
        Returns:
            Markdown形式のセクター分析
        """
        section = "## 注目セクター\n\n"
        
        for i, sector in enumerate(sectors[:3], 1):
            section += f"### {i}. {sector.get('name', 'セクター')}\n\n"
            
            if sector.get('reason'):
                section += f"**注目される理由**: {sector['reason']}\n\n"
            
            if sector.get('related_fields'):
                fields = sector['related_fields']
                if isinstance(fields, str):
                    fields = [fields]
                section += f"**波及する分野**: {', '.join(fields)}\n\n"
            
            if sector.get('timeframe'):
                section += f"**期間**: {sector['timeframe']}\n\n"
            
            section += "---\n\n"
        
        return section
    
    def generate_stock_recommendations(self, recommendations: Dict) -> str:
        """
        銘柄推奨セクションを生成
        
        Args:
            recommendations: 推奨銘柄の辞書（国コード -> リスト）
        
        Returns:
            Markdown形式の推奨銘柄
        """
        section = "## おすすめ銘柄\n\n"
        
        # 日本株
        jp_stocks = recommendations.get("JP", [])
        if jp_stocks:
            section += "### 日本株\n\n"
            for stock in jp_stocks:
                section += f"#### {stock.get('rank', '')}位: {stock.get('name', '')} ({stock.get('ticker', '')})\n\n"
                section += f"- **投資期間**: {stock.get('timeframe', '中期')}\n"
                section += f"- **割安度**: {stock.get('value_rating', '評価なし')}\n"
                section += f"- **注目理由**: {stock.get('reason', '')}\n"
                section += f"- **前提条件**: {stock.get('precondition', '')}\n\n"
            
            section += "---\n\n"
        
        # 米国株
        us_stocks = recommendations.get("US", [])
        if us_stocks:
            section += "### 米国株\n\n"
            for stock in us_stocks:
                section += f"#### {stock.get('rank', '')}位: {stock.get('name', '')} ({stock.get('ticker', '')})\n\n"
                section += f"- **投資期間**: {stock.get('timeframe', '中期')}\n"
                section += f"- **割安度**: {stock.get('value_rating', '評価なし')}\n"
                section += f"- **注目理由**: {stock.get('reason', '')}\n"
                section += f"- **前提条件**: {stock.get('precondition', '')}\n\n"
            
            section += "---\n\n"
        
        return section
    
    def generate_full_page(self, analysis_result: Dict, sectors: List[Dict], recommendations: Dict) -> str:
        """
        フルページを生成
        
        Args:
            analysis_result: 分析結果
            sectors: セクター分析
            recommendations: 銘柄推奨
        
        Returns:
            完全なMarkdownページ
        """
        date_str = datetime.now().strftime("%Y年%m月%d日 %H:%M")
        
        content = f"""# 株式市場分析レポート

**更新日時**: {date_str}

---
"""
        
        # Overview
        content += self.generate_overview_table(analysis_result) + "\n"
        
        # サマリー
        content += self.generate_summary(analysis_result) + "\n"
        
        # 国別分析
        for country_code, country_result in analysis_result["countries"].items():
            content += self.generate_country_analysis(country_result, analysis_result) + "\n"
        
        # セクター分析
        if sectors:
            content += self.generate_sector_analysis(sectors) + "\n"
        
        # 銘柄推奨
        if recommendations:
            content += self.generate_stock_recommendations(recommendations) + "\n"
        
        # フッター
        content += """---
**免責事項**: 本レポートは研究用途であり、投資助言や売買指示を目的としたものではありません。投資判断は自己責任で行ってください。
"""
        
        return content
    
    def save_markdown(self, content: str, filename: str = "market-analysis.md"):
        """
        Markdownファイルを保存
        
        Args:
            content: Markdownコンテンツ
            filename: ファイル名
        """
        filepath = self.output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Markdownファイルを保存しました: {filepath}")
    
    def generate_detail_page(self, country_result: Dict, timeframe_code: str, analysis_text: Dict) -> str:
        """
        詳細ページを生成
        
        Args:
            country_result: 国別結果
            timeframe_code: 期間コード
            analysis_text: 分析テキスト
        
        Returns:
            Markdownコンテンツ
        """
        country_name = country_result["name"]
        timeframe_name = next(
            (tf['name'] for tf in self.config['timeframes'] if tf['code'] == timeframe_code),
            timeframe_code
        )
        
        date_str = datetime.now().strftime("%Y年%m月%d日 %H:%M")
        
        content = f"""# {country_name} 市場分析 - {timeframe_name}

**更新日時**: {date_str}

[← トップページに戻る](./index.md)

---

"""
        
        if analysis_text.get("結論"):
            content += f"## 結論\n\n{analysis_text['結論']}\n\n"
        if analysis_text.get("前提"):
            content += f"## 前提\n\n{analysis_text['前提']}\n\n"
        if analysis_text.get("最大リスク"):
            content += f"## 最大リスク\n\n{analysis_text['最大リスク']}\n\n"
        if analysis_text.get("転換シグナル"):
            content += f"## 転換シグナル\n\n{analysis_text['転換シグナル']}\n\n"
        
        return content
    
    def save_detail_page(self, content: str, country_code: str, timeframe_code: str):
        """
        詳細ページを保存
        
        Args:
            content: Markdownコンテンツ
            country_code: 国コード
            timeframe_code: 期間コード
        """
        detail_dir = self.output_dir / "details"
        detail_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"{country_code}-{timeframe_code}.md"
        filepath = detail_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"詳細ページを保存しました: {filepath}")
    
    def generate_thought_log(self, country_code: str, timeframe_code: str, data: Dict, analysis: Dict) -> str:
        """
        思考ログを生成
        
        Args:
            country_code: 国コード
            timeframe_code: 期間コード
            data: 元データ
            analysis: 分析結果
        
        Returns:
            Markdownコンテンツ
        """
        date_str = datetime.now().strftime("%Y年%m月%d日 %H:%M")
        
        # データをJSON文字列に変換（見やすくするため）
        data_str = json.dumps(data, ensure_ascii=False, indent=2, default=str)
        analysis_str = json.dumps(analysis, ensure_ascii=False, indent=2, default=str)
        
        content = f"""# 思考ログ: {country_code} - {timeframe_code}

**更新日時**: {date_str}

[← トップページに戻る](./index.md)

---

## 判断に至ったプロセス

### 使用データ

```json
{data_str}
```

### 分析結果

```json
{analysis_str}
```

### 判断理由

上記のデータと分析結果に基づき、以下の判断を行いました：

- マクロ指標: {analysis.get('components', {}).get('macro', 0):.2f}
- 金融指標: {analysis.get('components', {}).get('financial', 0):.2f}
- テクニカル指標: {analysis.get('components', {}).get('technical', 0):.2f}
- 構造的指標: {analysis.get('components', {}).get('structural', 0):.2f}

**最終スコア**: {analysis.get('score', 0)} ({analysis.get('label', '中立')})

"""
        
        return content
    
    def save_thought_log(self, content: str, country_code: str, timeframe_code: str):
        """
        思考ログを保存
        
        Args:
            content: Markdownコンテンツ
            country_code: 国コード
            timeframe_code: 期間コード
        """
        log_dir = self.output_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"{country_code}-{timeframe_code}.md"
        filepath = log_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"思考ログを保存しました: {filepath}")


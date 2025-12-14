"""
LLM統合モジュール
市場データを解釈し、文章を生成する
"""

import yaml
import os
import json
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

# OpenAI API使用（環境変数から取得）
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OpenAI = None
    OPENAI_AVAILABLE = False
    logger.warning("OpenAIライブラリがインストールされていません。LLM機能は無効化されます。")


class LLMGenerator:
    """LLM文章生成クラス"""
    
    def __init__(self, config_path: str = "config/config.yml"):
        """初期化"""
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.ai_config = self.config.get('ai', {})
        self.enabled = self.ai_config.get('enabled', True) and OPENAI_AVAILABLE
        
        self.client = None
        if self.enabled:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                self.client = OpenAI(api_key=api_key)
            else:
                logger.warning("OPENAI_API_KEYが設定されていません。LLM機能は無効化されます。")
                self.enabled = False
    
    def _call_llm(self, prompt: str, max_tokens: int = 1000) -> Optional[str]:
        """
        LLM APIを呼び出す
        
        Args:
            prompt: プロンプト
            max_tokens: 最大トークン数
        
        Returns:
            生成されたテキスト
        """
        if not self.enabled:
            return None
        
        try:
            if not self.client:
                return None
            
            model = self.ai_config.get('model', 'gpt-4o-mini')
            temperature = self.ai_config.get('temperature', 0.7)
            
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "あなたは金融市場の分析アシスタントです。投資助言や売買指示は行いません。断定的表現は避け、前提・リスク・転換シグナルを必ず明示してください。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"LLM API呼び出しエラー: {e}")
            return None
    
    def generate_market_analysis(self, country_data: Dict, direction_data: Dict, timeframe_name: str) -> Dict:
        """
        市場分析文章を生成
        
        Args:
            country_data: 国別データ
            direction_data: 方向感データ
            timeframe_name: 期間名
        
        Returns:
            分析結果の辞書（結論、前提、リスク、転換シグナル）
        """
        if not self.enabled:
            # LLM無効時はテンプレートベースの簡易生成
            return self._generate_fallback_analysis(country_data, direction_data, timeframe_name)
        
        # データを整形
        data_summary = {
            "国": country_data["name"],
            "期間": timeframe_name,
            "スコア": direction_data["score"],
            "ラベル": direction_data["label"],
            "構成要素": direction_data["components"],
            "リスクフラグ": direction_data["has_risk"]
        }
        
        # プロンプト取得
        prompt_template = self.ai_config['prompts']['market_analysis']
        prompt = prompt_template.format(data=json.dumps(data_summary, ensure_ascii=False, indent=2))
        
        # LLM呼び出し
        result_text = self._call_llm(prompt)
        
        if result_text:
            # 結果をパース（簡易的な分割）
            return self._parse_analysis_result(result_text)
        else:
            return self._generate_fallback_analysis(country_data, direction_data, timeframe_name)
    
    def _parse_analysis_result(self, text: str) -> Dict:
        """
        LLM出力をパース
        
        Args:
            text: LLM出力テキスト
        
        Returns:
            構造化された分析結果
        """
        # 簡易的なパース（実際はより堅牢な実装が必要）
        sections = {
            "結論": "",
            "前提": "",
            "最大リスク": "",
            "転換シグナル": ""
        }
        
        lines = text.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # セクション検出
            if '結論' in line or '1.' in line:
                current_section = "結論"
                sections["結論"] = line.split(':', 1)[-1].strip() if ':' in line else line
            elif '前提' in line or '2.' in line:
                current_section = "前提"
                sections["前提"] = line.split(':', 1)[-1].strip() if ':' in line else line
            elif 'リスク' in line or '3.' in line:
                current_section = "最大リスク"
                sections["最大リスク"] = line.split(':', 1)[-1].strip() if ':' in line else line
            elif '転換' in line or 'シグナル' in line or '4.' in line:
                current_section = "転換シグナル"
                sections["転換シグナル"] = line.split(':', 1)[-1].strip() if ':' in line else line
            elif current_section:
                # 継続行
                sections[current_section] += " " + line
        
        # 空のセクションがあればテキスト全体を使用
        if not any(sections.values()):
            sections["結論"] = text[:200]  # 最初の200文字
        
        return sections
    
    def _generate_fallback_analysis(self, country_data: Dict, direction_data: Dict, timeframe_name: str) -> Dict:
        """
        フォールバック分析（LLM無効時）
        
        Args:
            country_data: 国別データ
            direction_data: 方向感データ
            timeframe_name: 期間名
        
        Returns:
            分析結果の辞書
        """
        score = direction_data["score"]
        label = direction_data["label"]
        
        if score >= 1:
            conclusion = f"{country_data['name']}市場は{timeframe_name}で強気の傾向を示しています。{label}"
            premise = "テクニカル指標およびマクロ環境が良好な水準にあります。"
            risk = "上昇トレンドが継続する前提で、急激な調整や外部ショックに注意が必要です。"
            signal = "価格がMA200を大きく下回る、またはボラティリティが急上昇した場合に方向性が転換する可能性があります。"
        elif score <= -1:
            conclusion = f"{country_data['name']}市場は{timeframe_name}で弱気の傾向を示しています。{label}"
            premise = "テクニカル指標およびマクロ環境が弱い水準にあります。"
            risk = "下方リスクが高く、さらなる調整の可能性があります。"
            signal = "価格がMA200を上回り、出来高とともに上昇した場合に反転の可能性があります。"
        else:
            conclusion = f"{country_data['name']}市場は{timeframe_name}で中立の状況です。{label}"
            premise = "テクニカル指標およびマクロ環境が中立的な水準にあります。"
            risk = "方向性が明確でないため、外部要因に敏感に反応する可能性があります。"
            signal = "明確な方向性を示すマクロデータやテクニカルブレイクが転換シグナルとなります。"
        
        if direction_data["has_risk"]:
            risk += " 集中リスクやイベントリスクが検知されています。"
        
        return {
            "結論": conclusion,
            "前提": premise,
            "最大リスク": risk,
            "転換シグナル": signal
        }
    
    def generate_sector_analysis(self, market_data: Dict) -> List[Dict]:
        """
        セクター分析を生成
        
        Args:
            market_data: 市場データ
        
        Returns:
            セクター分析のリスト
        """
        if not self.enabled:
            # フォールバック：一般的なセクターを返す
            return [
                {
                    "name": "AI・半導体",
                    "reason": "構造的な技術革新による長期成長が見込まれる分野",
                    "related_fields": ["半導体製造装置", "クラウドインフラ", "データセンター"],
                    "timeframe": "長期"
                },
                {
                    "name": "防衛・セキュリティ",
                    "reason": "地政学的リスクの高まりにより注目度が上昇",
                    "related_fields": ["防衛装備", "サイバーセキュリティ", "資源安全保障"],
                    "timeframe": "中期"
                }
            ]
        
        # データサマリー
        data_summary = {
            "市場データ": market_data
        }
        
        prompt_template = self.ai_config['prompts']['sector_analysis']
        prompt = prompt_template.format(data=json.dumps(data_summary, ensure_ascii=False, indent=2))
        
        result_text = self._call_llm(prompt)
        
        if result_text:
            # 簡易的なパース（実際はより堅牢な実装が必要）
            return self._parse_sector_result(result_text)
        else:
            # フォールバック：一般的なセクターを返す
            return [
                {
                    "name": "AI・半導体",
                    "reason": "構造的な技術革新による長期成長が見込まれる分野",
                    "related_fields": ["半導体製造装置", "クラウドインフラ", "データセンター"],
                    "timeframe": "長期"
                },
                {
                    "name": "防衛・セキュリティ",
                    "reason": "地政学的リスクの高まりにより注目度が上昇",
                    "related_fields": ["防衛装備", "サイバーセキュリティ", "資源安全保障"],
                    "timeframe": "中期"
                }
            ]
    
    def _parse_sector_result(self, text: str) -> List[Dict]:
        """セクター結果をパース（簡易実装）"""
        # 実際の実装では、より堅牢なパースが必要
        sectors = []
        lines = text.split('\n')
        
        current_sector = {}
        for line in lines:
            line = line.strip()
            if 'セクター' in line or '分野' in line:
                if current_sector:
                    sectors.append(current_sector)
                current_sector = {"name": line}
            elif '理由' in line:
                current_sector["reason"] = line.split(':', 1)[-1].strip()
            elif '波及' in line or '関連' in line:
                current_sector["related_fields"] = line.split(':', 1)[-1].strip().split('、')
            elif '期間' in line:
                current_sector["timeframe"] = line.split(':', 1)[-1].strip()
        
        if current_sector:
            sectors.append(current_sector)
        
        return sectors[:3]  # 最大3つ
    
    def generate_stock_recommendations(self, stocks_data: List[Dict], country_code: str) -> List[Dict]:
        """
        銘柄推奨を生成
        
        Args:
            stocks_data: 銘柄データリスト
            country_code: 国コード
        
        Returns:
            推奨銘柄のリスト
        """
        if not self.enabled:
            # フォールバック：データベースから簡易推奨
            return self._generate_fallback_stock_recommendations(stocks_data, country_code)
        
        data_summary = {
            "銘柄データ": stocks_data[:20]  # 最大20銘柄
        }
        
        prompt_template = self.ai_config['prompts']['stock_recommendation']
        prompt = prompt_template.format(data=json.dumps(data_summary, ensure_ascii=False, indent=2))
        
        result_text = self._call_llm(prompt, max_tokens=2000)
        
        if result_text:
            return self._parse_stock_recommendations(result_text, stocks_data)
        else:
            return self._generate_fallback_stock_recommendations(stocks_data, country_code)
    
    def _parse_stock_recommendations(self, text: str, stocks_data: List[Dict]) -> List[Dict]:
        """銘柄推奨結果をパース（簡易実装）"""
        # 実際の実装では、より堅牢なパースが必要
        recommendations = []
        
        # 簡易実装：データから上位を選出
        sorted_stocks = sorted(
            stocks_data,
            key=lambda x: x.get("price_vs_ma200", 0),
            reverse=True
        )[:5]
        
        for i, stock in enumerate(sorted_stocks, 1):
            recommendations.append({
                "rank": i,
                "ticker": stock.get("ticker", ""),
                "name": stock.get("name", stock.get("ticker", "")),
                "timeframe": "中期",
                "value_rating": "やや割安" if stock.get("price_vs_ma200", 0) < 0 else "適正",
                "reason": f"テクニカル指標が良好で、{stock.get('sector', '')}セクターの成長が見込まれます。",
                "precondition": "マクロ環境が悪化しないこと、セクター全体のトレンドが継続すること。"
            })
        
        return recommendations
    
    def _generate_fallback_stock_recommendations(self, stocks_data: List[Dict], country_code: str) -> List[Dict]:
        """フォールバック銘柄推奨"""
        recommendations = []
        
        # データから上位を選出
        sorted_stocks = sorted(
            stocks_data,
            key=lambda x: x.get("price_vs_ma200", 0),
            reverse=True
        )[:5]
        
        for i, stock in enumerate(sorted_stocks, 1):
            recommendations.append({
                "rank": i,
                "ticker": stock.get("ticker", ""),
                "name": stock.get("name", stock.get("ticker", "")),
                "timeframe": "中期",
                "value_rating": "やや割安" if stock.get("price_vs_ma200", 0) < 0 else "適正",
                "reason": f"テクニカル指標が良好です。MA200に対する相対位置が{stock.get('price_vs_ma200', 0):.1f}%です。",
                "precondition": "マクロ環境が悪化しないこと、セクター全体のトレンドが継続すること。"
            })
        
        return recommendations


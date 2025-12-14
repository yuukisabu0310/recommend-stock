"""
LLM統合モジュール
市場データを解釈し、文章を生成する
Groq APIを使用
"""

import yaml
import os
import json
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

# Groq API使用（環境変数から取得）
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    Groq = None
    GROQ_AVAILABLE = False
    logger.warning("Groqライブラリがインストールされていません。LLM機能は無効化されます。")


class LLMGenerator:
    """LLM文章生成クラス（Groq API使用）"""
    
    def __init__(self, config_path: str = "config/config.yml"):
        """初期化"""
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.ai_config = self.config.get('ai', {})
        self.enabled = self.ai_config.get('enabled', True) and GROQ_AVAILABLE
        
        self.client = None
        if self.enabled:
            api_key = os.getenv('GROQ_API_KEY')
            if api_key:
                self.client = Groq(api_key=api_key)
            else:
                logger.warning("GROQ_API_KEYが設定されていません。LLM機能は無効化されます。")
                self.enabled = False
    
    def _call_llm(self, system_prompt: str, user_prompt: str, max_tokens: int = 2000, response_format: Optional[Dict] = None) -> Optional[str]:
        """
        Groq LLM APIを呼び出す
        
        Args:
            system_prompt: システムプロンプト
            user_prompt: ユーザープロンプト
            max_tokens: 最大トークン数
            response_format: レスポンス形式（JSON等）
        
        Returns:
            生成されたテキスト
        """
        if not self.enabled:
            return None
        
        try:
            if not self.client:
                return None
            
            model = self.ai_config.get('model', 'llama-3.1-70b-versatile')
            temperature = self.ai_config.get('temperature', 0.25)
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            params = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            # JSON形式を要求する場合
            if response_format:
                params["response_format"] = response_format
            
            response = self.client.chat.completions.create(**params)
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Groq API呼び出しエラー: {e}")
            return None
    
    def generate_market_direction(self, country_data: Dict, timeframe_code: str, timeframe_name: str) -> Dict:
        """
        市場方向感をGroq LLMで分析・評価
        
        Args:
            country_data: 国別データ（マクロ、金融、テクニカル、構造的指標を含む）
            timeframe_code: 期間コード（short/medium/long）
            timeframe_name: 期間名（短期/中期/長期）
        
        Returns:
            市場方向感の辞書（score, direction_label, summary, key_factors, risks, turning_points）
        """
        if not self.enabled:
            # LLM無効時はルールベース分析を使用
            return self._generate_fallback_direction(country_data, timeframe_code, timeframe_name)
        
        # システムプロンプト（固定）
        system_prompt = """あなたは株式市場分析を行うAIアシスタントです。
このシステムは投資判断や売買助言を目的としません。

以下の制約を必ず守ってください：
- 売買・推奨・目標価格の提示は禁止
- 断定表現は禁止（「〜と考えられる」「〜の可能性」）
- 与えられたデータ以外を想像しない
- 出力は必ずJSONのみ"""
        
        # データを整形
        macro_data = country_data.get("macro", {})
        financial_data = country_data.get("financial", {})
        technical_data = {}
        structural_data = {}
        
        # インデックスデータからテクニカル・構造的指標を取得
        indices = country_data.get("indices", {})
        if indices:
            first_index = list(indices.values())[0]
            technical_data = {
                "price_vs_ma200": first_index.get("price_vs_ma200", 0),
                "volatility": first_index.get("volatility", 0),
                "volume_ratio": first_index.get("volume_ratio", 1.0),
                "latest_price": first_index.get("latest_price", 0),
                "ma200": first_index.get("ma200", 0)
            }
            structural_data = {
                "top_stocks_concentration": first_index.get("top_stocks_concentration", 0)
            }
        
        # ユーザープロンプト生成
        country_name = country_data.get("name", "")
        
        # 期間に応じた考慮事項
        timeframe_notes = {
            "short": "短期：需給・金融イベント・テクニカル",
            "medium": "中期：景気・金融政策・業績環境",
            "long": "長期：人口動態・産業構造・地政学・制度"
        }
        timeframe_note = timeframe_notes.get(timeframe_code, "")
        
        user_prompt = f"""分析対象は以下の通りです。

Country: {country_name}
Time Horizon: {timeframe_name}

以下は Python 側で取得・整理された指標データです。

【マクロ指標】
{json.dumps(macro_data, ensure_ascii=False, indent=2)}

【金融指標】
{json.dumps(financial_data, ensure_ascii=False, indent=2)}

【テクニカル指標】
{json.dumps(technical_data, ensure_ascii=False, indent=2)}

【構造的指標】
{json.dumps(structural_data, ensure_ascii=False, indent=2)}

これらを総合し、市場全体の方向感を以下の5段階で評価してください。

+2 : 超強気
+1 : やや強気
 0 : 中立
-1 : やや弱気
-2 : 超弱気

{timeframe_note}で以下を特に考慮してください。

出力は以下のJSON形式で返してください：

{{
  "score": number,
  "direction_label": "超強気 | やや強気 | 中立 | やや弱気 | 超弱気",
  "summary": "市場環境を1〜2文で要約",
  "key_factors": [
    "判断に最も影響した要因1",
    "判断に最も影響した要因2",
    "判断に最も影響した要因3"
  ],
  "risks": [
    "想定される最大リスク1",
    "想定される最大リスク2"
  ],
  "turning_points": [
    "方向感が変わる可能性のある条件・イベント"
  ]
}}"""
        
        # Groq API呼び出し（JSON形式を要求）
        result_text = self._call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        
        if result_text:
            try:
                # JSONをパース
                result = json.loads(result_text)
                
                # 必須フィールドの検証
                if "score" not in result:
                    logger.warning("LLM出力にscoreが含まれていません。フォールバックを使用します。")
                    return self._generate_fallback_direction(country_data, timeframe_code, timeframe_name)
                
                # スコアの範囲チェック
                score = int(result.get("score", 0))
                score = max(-2, min(2, score))
                result["score"] = score
                
                # direction_labelが正しいかチェック
                valid_labels = ["超強気", "やや強気", "中立", "やや弱気", "超弱気"]
                if result.get("direction_label") not in valid_labels:
                    # スコアから自動設定
                    label_map = {
                        2: "超強気",
                        1: "やや強気",
                        0: "中立",
                        -1: "やや弱気",
                        -2: "超弱気"
                    }
                    result["direction_label"] = label_map.get(score, "中立")
                
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"JSONパースエラー: {e}, レスポンス: {result_text[:200]}")
                return self._generate_fallback_direction(country_data, timeframe_code, timeframe_name)
        else:
            return self._generate_fallback_direction(country_data, timeframe_code, timeframe_name)
    
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
    
    def _generate_fallback_direction(self, country_data: Dict, timeframe_code: str, timeframe_name: str) -> Dict:
        """
        フォールバック方向感分析（LLM無効時またはエラー時）
        ルールベースで簡易評価
        
        Args:
            country_data: 国別データ
            timeframe_code: 期間コード
            timeframe_name: 期間名
        
        Returns:
            市場方向感の辞書
        """
        # 簡易的なルールベース評価
        score = 0
        summary = f"{country_data.get('name', '')}市場は{timeframe_name}で中立の状況です。"
        key_factors = []
        risks = []
        turning_points = []
        
        # インデックスデータから簡易評価
        indices = country_data.get("indices", {})
        if indices:
            first_index = list(indices.values())[0]
            price_vs_ma = first_index.get("price_vs_ma200", 0)
            volatility = first_index.get("volatility", 0)
            
            if price_vs_ma > 5:
                score = 1
                summary = f"{country_data.get('name', '')}市場は{timeframe_name}でやや強気の傾向を示しています。"
                key_factors.append("価格がMA200を大きく上回っている")
            elif price_vs_ma < -5:
                score = -1
                summary = f"{country_data.get('name', '')}市場は{timeframe_name}でやや弱気の傾向を示しています。"
                key_factors.append("価格がMA200を大きく下回っている")
            
            if volatility > 30:
                risks.append("高ボラティリティによる急激な変動の可能性")
                turning_points.append("ボラティリティが低下し、方向性が明確になった場合")
        
        label_map = {
            2: "超強気",
            1: "やや強気",
            0: "中立",
            -1: "やや弱気",
            -2: "超弱気"
        }
        
        return {
            "score": score,
            "direction_label": label_map.get(score, "中立"),
            "summary": summary,
            "key_factors": key_factors if key_factors else ["データが不足しているため、中立と判断"],
            "risks": risks if risks else ["方向性が明確でないため、外部要因に敏感に反応する可能性"],
            "turning_points": turning_points if turning_points else ["明確な方向性を示すマクロデータやテクニカルブレイク"]
        }
    
    def generate_market_analysis(self, country_data: Dict, direction_data: Dict, timeframe_name: str) -> Dict:
        """
        市場分析文章を生成（後方互換性のため残す）
        
        Args:
            country_data: 国別データ
            direction_data: 方向感データ
            timeframe_name: 期間名
        
        Returns:
            分析結果の辞書（結論、前提、リスク、転換シグナル）
        """
        # 新しい形式に変換
        timeframe_code = "medium"  # デフォルト
        for tf in self.config.get('timeframes', []):
            if tf.get('name') == timeframe_name:
                timeframe_code = tf.get('code', 'medium')
                break
        
        llm_result = self.generate_market_direction(country_data, timeframe_code, timeframe_name)
        
        # 旧形式に変換
        return {
            "結論": llm_result.get("summary", ""),
            "前提": "、".join(llm_result.get("key_factors", [])),
            "最大リスク": "、".join(llm_result.get("risks", [])),
            "転換シグナル": "、".join(llm_result.get("turning_points", []))
        }
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


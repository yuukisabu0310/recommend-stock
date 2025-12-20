"""
市場分析モジュール
データを分析し、スコア化する
"""

import yaml
from typing import Dict, List, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class MarketAnalyzer:
    """市場分析クラス"""
    
    def __init__(self, config_path: str = "config/config.yml"):
        """初期化"""
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.score_range = self.config['score_range']
        self.event_config = self.config.get('event_detection', {})
    
    def calculate_macro_score(self, macro_data: Dict, timeframe_code: str) -> Dict:
        """
        マクロ指標スコアと状態を計算
        
        Args:
            macro_data: マクロ指標データ
            timeframe_code: 期間コード
        
        Returns:
            {"score": float, "state": str} の辞書
        """
        # 実際の実装では、PMI, CPI, 雇用などの指標をスコア化
        # ここでは簡易的なモック実装
        score = 0.0
        state_parts = []
        
        # PMIが50以上なら強気、以下なら弱気
        if macro_data.get("PMI"):
            if macro_data["PMI"] > 50:
                score += 0.5
                state_parts.append("pmi_expansion")
            else:
                score -= 0.5
                state_parts.append("pmi_contraction")
        
        # CPI上昇率が適切なら中立、高すぎれば弱気
        if macro_data.get("CPI"):
            cpi_change = macro_data.get("CPI_change", 0)
            if 1.0 < cpi_change < 3.0:
                score += 0.3
                state_parts.append("inflation_optimal")
            elif cpi_change > 5.0:
                score -= 0.8
                state_parts.append("inflation_high_sticky")
            elif cpi_change < 1.0:
                state_parts.append("inflation_low")
        
        # 雇用データ
        if macro_data.get("employment"):
            employment_rate = macro_data.get("employment_rate", 0)
            if employment_rate > 95:
                score += 0.2
                state_parts.append("employment_strong")
            elif employment_rate < 90:
                score -= 0.3
                state_parts.append("employment_weak")
        
        final_score = max(self.score_range['min'], min(self.score_range['max'], score))
        state = "_".join(state_parts) if state_parts else "macro_neutral"
        
        return {"score": final_score, "state": state}
    
    def calculate_technical_score(self, index_data: Dict) -> Dict:
        """
        テクニカル指標スコアと状態を計算
        
        Args:
            index_data: インデックスデータ
        
        Returns:
            {"score": float, "state": str} の辞書
        """
        score = 0.0
        state_parts = []
        
        # 価格 vs MA200
        price_vs_ma = index_data.get("price_vs_ma200", 0)
        if price_vs_ma > 5:
            score += 1.0
            state_parts.append("price_well_above_ma200")
        elif price_vs_ma > 2:
            score += 0.5
            state_parts.append("price_above_ma200")
        elif price_vs_ma < -5:
            score -= 1.0
            state_parts.append("price_well_below_ma200")
        elif price_vs_ma < -2:
            score -= 0.5
            state_parts.append("price_below_ma200")
        else:
            state_parts.append("price_near_ma200")
        
        # 出来高
        volume_ratio = index_data.get("volume_ratio", 1.0)
        if volume_ratio > 1.5:
            score += 0.3  # 出来高増加は強気シグナル
            state_parts.append("volume_increasing")
        elif volume_ratio < 0.7:
            score -= 0.2  # 出来高減少は弱気シグナル
            state_parts.append("volume_decreasing")
        else:
            state_parts.append("volume_stable")
        
        # ボラティリティ
        volatility = index_data.get("volatility", 0)
        if volatility > 30:
            score -= 0.5  # 高ボラティリティはリスク
            state_parts.append("volatility_high")
        elif volatility < 15:
            state_parts.append("volatility_low")
        else:
            state_parts.append("volatility_normal")
        
        final_score = max(self.score_range['min'], min(self.score_range['max'], score))
        state = "_".join(state_parts) if state_parts else "technical_neutral"
        
        return {"score": final_score, "state": state}
    
    def calculate_financial_score(self, financial_data: Dict, timeframe_code: str) -> Dict:
        """
        金融指標スコアと状態を計算
        
        Args:
            financial_data: 金融指標データ
            timeframe_code: 期間コード
        
        Returns:
            {"score": float, "state": str} の辞書
        """
        # 実際の実装では、政策金利、長期金利、クレジットスプレッドを評価
        score = 0.0
        state_parts = []
        
        # 政策金利
        if financial_data.get("policy_rate"):
            policy_rate = financial_data["policy_rate"]
            if policy_rate < 1.0:
                score += 0.3
                state_parts.append("policy_rate_low")
            elif policy_rate > 5.0:
                score -= 0.5
                state_parts.append("policy_rate_high")
            else:
                state_parts.append("policy_rate_normal")
        
        # 長期金利が適切なら中立
        if financial_data.get("long_term_rate"):
            rate = financial_data["long_term_rate"]
            if 2.0 < rate < 4.0:
                score += 0.2
                state_parts.append("long_rate_optimal")
            elif rate > 5.0:
                score -= 0.5
                state_parts.append("long_rate_high_level")
            elif rate < 1.0:
                state_parts.append("long_rate_low")
            else:
                state_parts.append("long_rate_normal")
        
        final_score = max(self.score_range['min'], min(self.score_range['max'], score))
        state = "_".join(state_parts) if state_parts else "financial_neutral"
        
        return {"score": final_score, "state": state}
    
    def calculate_structural_score(self, index_data: Dict, country_code: str) -> Dict:
        """
        構造的指標スコアと状態を計算
        
        Args:
            index_data: インデックスデータ
            country_code: 国コード
        
        Returns:
            {"score": float, "state": str} の辞書
        """
        # 上位銘柄集中度を評価（集中度が高い場合はリスク）
        score = 0.0
        state_parts = []
        
        # 実際の実装では、上位銘柄の時価総額シェアを計算
        # ここでは簡易的な評価
        
        concentration = index_data.get("top_stocks_concentration", 0)
        threshold = self.event_config.get('concentration_risk', {}).get('threshold', 0.35)
        
        if concentration > threshold:
            score -= 0.8  # 集中リスク
            state_parts.append("concentration_high_risk")
        elif concentration > 0.25:
            state_parts.append("concentration_moderate")
        else:
            state_parts.append("concentration_low")
        
        final_score = max(self.score_range['min'], min(self.score_range['max'], score))
        state = "_".join(state_parts) if state_parts else "structural_neutral"
        
        return {"score": final_score, "state": state}
    
    def calculate_market_direction(self, country_data: Dict, timeframe_code: str) -> Dict:
        """
        市場方向感を計算
        
        Args:
            country_data: 国別データ
            timeframe_code: 期間コード
        
        Returns:
            市場方向感の辞書
        """
        # 期間ごとの重みを取得
        timeframe_config = next(
            (tf for tf in self.config['timeframes'] if tf['code'] == timeframe_code),
            None
        )
        
        if not timeframe_config:
            weights = {"technical": 0.4, "macro": 0.4, "financial": 0.2}
        else:
            weights = timeframe_config.get('weights', {})
        
        # 各指標スコアと状態を計算
        macro_result = self.calculate_macro_score(country_data.get("macro", {}), timeframe_code)
        financial_result = self.calculate_financial_score(country_data.get("financial", {}), timeframe_code)
        
        # インデックスデータからテクニカルスコアを計算（最初のインデックスを使用）
        technical_result = {"score": 0.0, "state": "technical_neutral"}
        structural_result = {"score": 0.0, "state": "structural_neutral"}
        
        indices = country_data.get("indices", {})
        if indices:
            first_index = list(indices.values())[0]
            technical_result = self.calculate_technical_score(first_index)
            structural_result = self.calculate_structural_score(first_index, country_data["code"])
        
        macro_score = macro_result["score"]
        financial_score = financial_result["score"]
        technical_score = technical_result["score"]
        structural_score = structural_result["score"]
        
        # 重み付け平均
        total_score = (
            macro_score * weights.get("macro", 0.3) +
            financial_score * weights.get("financial", 0.2) +
            technical_score * weights.get("technical", 0.3) +
            structural_score * weights.get("structural", 0.2)
        )
        
        # スコアを整数に丸める（-2, -1, 0, 1, 2）
        rounded_score = round(total_score)
        rounded_score = max(self.score_range['min'], min(self.score_range['max'], rounded_score))
        
        # イベントリスクチェック
        has_risk = self.check_event_risks(country_data, first_index if indices else {})
        
        # 主要要因を特定（スコアの絶対値が大きい順）
        factor_scores = {
            "macro": abs(macro_score),
            "financial": abs(financial_score),
            "technical": abs(technical_score),
            "structural": abs(structural_score)
        }
        dominant_factors = sorted(factor_scores.items(), key=lambda x: x[1], reverse=True)[:2]
        dominant_factor_names = [name for name, _ in dominant_factors if _ > 0]
        
        # 全状態を収集
        all_states = [
            macro_result["state"],
            financial_result["state"],
            technical_result["state"],
            structural_result["state"]
        ]
        
        return {
            "score": rounded_score,
            "raw_score": total_score,
            "components": {
                "macro": {
                    "score": macro_score,
                    "state": macro_result["state"]
                },
                "financial": {
                    "score": financial_score,
                    "state": financial_result["state"]
                },
                "technical": {
                    "score": technical_score,
                    "state": technical_result["state"]
                },
                "structural": {
                    "score": structural_score,
                    "state": structural_result["state"]
                }
            },
            "states": all_states,
            "dominant_factors": dominant_factor_names,
            "has_risk": has_risk,
            "label": self.config['score_labels'].get(str(rounded_score), "→ 中立")
        }
    
    def check_event_risks(self, country_data: Dict, index_data: Dict) -> bool:
        """
        イベントリスクをチェック
        
        Args:
            country_data: 国別データ
            index_data: インデックスデータ
        
        Returns:
            リスクがあるかどうか
        """
        # 集中リスク
        if self.event_config.get('concentration_risk', {}).get('enabled', False):
            concentration = index_data.get("top_stocks_concentration", 0)
            threshold = self.event_config['concentration_risk']['threshold']
            if concentration > threshold:
                return True
        
        # ボラティリティスパイク
        if self.event_config.get('volatility_spike', {}).get('enabled', False):
            volatility = index_data.get("volatility", 0)
            threshold = self.event_config['volatility_spike']['threshold']
            # 簡易的なチェック（実際は過去平均と比較）
            if volatility > 30:  # 仮の閾値
                return True
        
        return False
    
    def analyze_all_markets(self, data: Dict) -> Dict:
        """
        全市場を分析
        
        Args:
            data: 全データ
        
        Returns:
            分析結果
        """
        analysis_result = {
            "overview": {},
            "countries": {},
            "timestamp": datetime.now().isoformat()
        }
        
        # 各国 × 期間ごとに分析
        for country_code, country_data in data["countries"].items():
            country_result = {}
            
            for timeframe in self.config['timeframes']:
                timeframe_code = timeframe['code']
                direction = self.calculate_market_direction(country_data, timeframe_code)
                
                country_result[timeframe_code] = direction
                
                # Overview用にスコアを記録
                if country_code not in analysis_result["overview"]:
                    analysis_result["overview"][country_code] = {}
                analysis_result["overview"][country_code][timeframe_code] = {
                    "score": direction["score"],
                    "has_risk": direction["has_risk"]
                }
            
            analysis_result["countries"][country_code] = {
                "name": country_data["name"],
                "code": country_code,
                "directions": country_result,
                "data": country_data
            }
        
        return analysis_result


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
    
    def calculate_macro_score(self, macro_data: Dict, timeframe_code: str) -> float:
        """
        マクロ指標スコアを計算
        
        Args:
            macro_data: マクロ指標データ
            timeframe_code: 期間コード
        
        Returns:
            スコア (-2 ~ +2)
        """
        # 実際の実装では、PMI, CPI, 雇用などの指標をスコア化
        # ここでは簡易的なモック実装
        score = 0.0
        
        # PMIが50以上なら強気、以下なら弱気
        if macro_data.get("PMI"):
            if macro_data["PMI"] > 50:
                score += 0.5
            else:
                score -= 0.5
        
        # CPI上昇率が適切なら中立、高すぎれば弱気
        if macro_data.get("CPI"):
            cpi_change = macro_data.get("CPI_change", 0)
            if 1.0 < cpi_change < 3.0:
                score += 0.3
            elif cpi_change > 5.0:
                score -= 0.8
        
        return max(self.score_range['min'], min(self.score_range['max'], score))
    
    def calculate_technical_score(self, index_data: Dict) -> float:
        """
        テクニカル指標スコアを計算
        
        Args:
            index_data: インデックスデータ
        
        Returns:
            スコア (-2 ~ +2)
        """
        score = 0.0
        
        # 価格 vs MA200
        price_vs_ma = index_data.get("price_vs_ma200", 0)
        if price_vs_ma > 5:
            score += 1.0
        elif price_vs_ma > 2:
            score += 0.5
        elif price_vs_ma < -5:
            score -= 1.0
        elif price_vs_ma < -2:
            score -= 0.5
        
        # 出来高
        volume_ratio = index_data.get("volume_ratio", 1.0)
        if volume_ratio > 1.5:
            score += 0.3  # 出来高増加は強気シグナル
        elif volume_ratio < 0.7:
            score -= 0.2  # 出来高減少は弱気シグナル
        
        # ボラティリティ
        volatility = index_data.get("volatility", 0)
        if volatility > 30:
            score -= 0.5  # 高ボラティリティはリスク
        
        return max(self.score_range['min'], min(self.score_range['max'], score))
    
    def calculate_financial_score(self, financial_data: Dict, timeframe_code: str) -> float:
        """
        金融指標スコアを計算
        
        Args:
            financial_data: 金融指標データ
            timeframe_code: 期間コード
        
        Returns:
            スコア (-2 ~ +2)
        """
        # 実際の実装では、政策金利、長期金利、クレジットスプレッドを評価
        score = 0.0
        
        # 長期金利が適切なら中立
        if financial_data.get("long_term_rate"):
            rate = financial_data["long_term_rate"]
            if 2.0 < rate < 4.0:
                score += 0.2
            elif rate > 5.0:
                score -= 0.5
        
        return max(self.score_range['min'], min(self.score_range['max'], score))
    
    def calculate_structural_score(self, index_data: Dict, country_code: str) -> float:
        """
        構造的指標スコアを計算
        
        Args:
            index_data: インデックスデータ
            country_code: 国コード
        
        Returns:
            スコア (-2 ~ +2)
        """
        # 上位銘柄集中度を評価（集中度が高い場合はリスク）
        score = 0.0
        
        # 実際の実装では、上位銘柄の時価総額シェアを計算
        # ここでは簡易的な評価
        
        concentration = index_data.get("top_stocks_concentration", 0)
        threshold = self.event_config.get('concentration_risk', {}).get('threshold', 0.35)
        
        if concentration > threshold:
            score -= 0.8  # 集中リスク
        
        return max(self.score_range['min'], min(self.score_range['max'], score))
    
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
        
        # 各指標スコアを計算
        macro_score = self.calculate_macro_score(country_data.get("macro", {}), timeframe_code)
        financial_score = self.calculate_financial_score(country_data.get("financial", {}), timeframe_code)
        
        # インデックスデータからテクニカルスコアを計算（最初のインデックスを使用）
        technical_score = 0.0
        structural_score = 0.0
        
        indices = country_data.get("indices", {})
        if indices:
            first_index = list(indices.values())[0]
            technical_score = self.calculate_technical_score(first_index)
            structural_score = self.calculate_structural_score(first_index, country_data["code"])
        
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
        
        return {
            "score": rounded_score,
            "raw_score": total_score,
            "components": {
                "macro": macro_score,
                "financial": financial_score,
                "technical": technical_score,
                "structural": structural_score
            },
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


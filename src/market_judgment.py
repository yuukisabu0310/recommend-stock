"""
市場判断モジュール
状態（enum）から市場判断（超強気〜弱気）をルールベースで決定
"""

from typing import Dict, List, Optional
from state_mapper import (
    InflationState, PolicyRateState, EmploymentState, GrowthState,
    LongRateState, EquityValuationState, VolatilityState,
    SectorConcentrationState, LiquidityState, ExternalRiskState,
    MarketViewState
)
import logging

logger = logging.getLogger(__name__)


class MarketJudgment:
    """市場判断クラス - 状態から市場判断を決定"""
    
    def __init__(self):
        """初期化"""
        pass
    
    def judge_market_view(
        self,
        states: Dict[str, str],
        timeframe_code: str
    ) -> Dict:
        """
        市場判断を決定
        
        Args:
            states: 状態の辞書
            timeframe_code: 期間コード（short/medium/long）
        
        Returns:
            市場判断の辞書（view, score, reasoning）
        """
        # 状態をEnumに変換
        inflation = InflationState(states.get("inflation", "moderate"))
        policy_rate = PolicyRateState(states.get("policy_rate", "hold"))
        employment = EmploymentState(states.get("employment", "stable"))
        growth = GrowthState(states.get("growth", "stable"))
        long_rate = LongRateState(states.get("long_rate", "low_level"))
        equity_valuation = EquityValuationState(states.get("equity_valuation", "fair"))
        volatility = VolatilityState(states.get("volatility", "medium"))
        sector_concentration = SectorConcentrationState(states.get("sector_concentration", "none"))
        liquidity = LiquidityState(states.get("liquidity", "neutral"))
        external_risk = ExternalRiskState(states.get("external_risk", "low"))
        
        # 期間別の重み付けで判断
        if timeframe_code == "short":
            view, score, reasoning = self._judge_short_term(
                inflation, policy_rate, long_rate, equity_valuation,
                volatility, liquidity
            )
        elif timeframe_code == "medium":
            view, score, reasoning = self._judge_medium_term(
                growth, employment, equity_valuation, sector_concentration,
                liquidity
            )
        elif timeframe_code == "long":
            view, score, reasoning = self._judge_long_term(
                growth, sector_concentration, external_risk, inflation
            )
        else:
            # デフォルト：中期判断
            view, score, reasoning = self._judge_medium_term(
                growth, employment, equity_valuation, sector_concentration,
                liquidity
            )
        
        return {
            "view": view.value,
            "score": score,
            "reasoning": reasoning,
            "key_states": self._format_key_states(states)
        }
    
    def _judge_short_term(
        self,
        inflation: InflationState,
        policy_rate: PolicyRateState,
        long_rate: LongRateState,
        equity_valuation: EquityValuationState,
        volatility: VolatilityState,
        liquidity: LiquidityState
    ) -> tuple:
        """
        短期判断（金融政策・金利・ボラティリティを最重視）
        
        Returns:
            (view, score, reasoning)
        """
        score = 0
        reasoning = []
        
        # インフレ × 政策金利
        if inflation == InflationState.HIGH_STICKY and policy_rate == PolicyRateState.TIGHTENING:
            score -= 1
            reasoning.append("インフレ高止まりと金融引き締めが同時発生")
        elif inflation == InflationState.LOW and policy_rate == PolicyRateState.EASING:
            score += 1
            reasoning.append("低インフレと金融緩和が同時発生")
        
        # 長期金利
        if long_rate == LongRateState.HIGH_LEVEL:
            score -= 1
            reasoning.append("長期金利が高水準")
        elif long_rate == LongRateState.LOW_LEVEL:
            score += 0.5
            reasoning.append("長期金利が低水準")
        
        # 株式評価
        if equity_valuation == EquityValuationState.HIGH_ZONE:
            score -= 0.5
            reasoning.append("株式評価が高水準")
        elif equity_valuation == EquityValuationState.CHEAP:
            score += 0.5
            reasoning.append("株式評価が割安水準")
        
        # ボラティリティ
        if volatility == VolatilityState.HIGH:
            score -= 0.5
            reasoning.append("ボラティリティが高水準")
        elif volatility == VolatilityState.LOW:
            score += 0.5
            reasoning.append("ボラティリティが低水準")
        
        # 流動性
        if liquidity == LiquidityState.LOOSE:
            score += 0.5
            reasoning.append("流動性が緩和")
        elif liquidity == LiquidityState.TIGHT:
            score -= 0.5
            reasoning.append("流動性が引き締め")
        
        # スコアを整数に丸める
        rounded_score = max(-2, min(2, round(score)))
        
        # 市場判断を決定
        if rounded_score >= 1.5:
            view = MarketViewState.STRONG_BULLISH
        elif rounded_score >= 0.5:
            view = MarketViewState.BULLISH
        elif rounded_score >= -0.5:
            view = MarketViewState.NEUTRAL
        elif rounded_score >= -1.5:
            view = MarketViewState.BEARISH
        else:
            view = MarketViewState.STRONG_BEARISH
        
        return view, rounded_score, reasoning
    
    def _judge_medium_term(
        self,
        growth: GrowthState,
        employment: EmploymentState,
        equity_valuation: EquityValuationState,
        sector_concentration: SectorConcentrationState,
        liquidity: LiquidityState
    ) -> tuple:
        """
        中期判断（景気・企業業績・需給を重視）
        
        Returns:
            (view, score, reasoning)
        """
        score = 0
        reasoning = []
        
        # 成長
        if growth == GrowthState.RECOVERY:
            score += 1
            reasoning.append("成長が回復傾向")
        elif growth == GrowthState.SLOWDOWN:
            score -= 1
            reasoning.append("成長が減速傾向")
        
        # 雇用
        if employment == EmploymentState.STRONG:
            score += 0.5
            reasoning.append("雇用が堅調")
        elif employment == EmploymentState.WEAK:
            score -= 0.5
            reasoning.append("雇用が弱い")
        
        # 株式評価
        if equity_valuation == EquityValuationState.FAIR:
            score += 0.5
            reasoning.append("株式評価が適正水準")
        elif equity_valuation == EquityValuationState.HIGH_ZONE:
            score -= 0.5
            reasoning.append("株式評価が高水準")
        
        # セクター集中
        if sector_concentration == SectorConcentrationState.SINGLE_THEME_HEAVY:
            score -= 0.5
            reasoning.append("単一テーマへの集中が高い")
        elif sector_concentration == SectorConcentrationState.NONE:
            score += 0.5
            reasoning.append("セクター分散が良好")
        
        # 流動性
        if liquidity == LiquidityState.LOOSE:
            score += 0.5
            reasoning.append("流動性が緩和")
        
        # スコアを整数に丸める
        rounded_score = max(-2, min(2, round(score)))
        
        # 市場判断を決定
        if rounded_score >= 1.5:
            view = MarketViewState.STRONG_BULLISH
        elif rounded_score >= 0.5:
            view = MarketViewState.BULLISH
        elif rounded_score >= -0.5:
            view = MarketViewState.NEUTRAL
        elif rounded_score >= -1.5:
            view = MarketViewState.BEARISH
        else:
            view = MarketViewState.STRONG_BEARISH
        
        return view, rounded_score, reasoning
    
    def _judge_long_term(
        self,
        growth: GrowthState,
        sector_concentration: SectorConcentrationState,
        external_risk: ExternalRiskState,
        inflation: InflationState
    ) -> tuple:
        """
        長期判断（成長率・構造要因・人口・技術革新を重視）
        
        Returns:
            (view, score, reasoning)
        """
        score = 0
        reasoning = []
        
        # 成長
        if growth == GrowthState.RECOVERY:
            score += 1
            reasoning.append("成長が回復傾向")
        elif growth == GrowthState.SLOWDOWN:
            score -= 1
            reasoning.append("成長が減速傾向")
        
        # セクター集中
        if sector_concentration == SectorConcentrationState.SINGLE_THEME_HEAVY:
            score -= 1
            reasoning.append("単一テーマへの集中が高い（長期リスク）")
        elif sector_concentration == SectorConcentrationState.AI_HEAVY:
            score += 0.5
            reasoning.append("AI集中は構造的成長要因")
        elif sector_concentration == SectorConcentrationState.NONE:
            score += 1
            reasoning.append("セクター分散が良好")
        
        # 外部リスク
        if external_risk == ExternalRiskState.HIGH:
            score -= 0.5
            reasoning.append("外部リスクが高い")
        elif external_risk == ExternalRiskState.LOW:
            score += 0.5
            reasoning.append("外部リスクが低い")
        
        # インフレ（長期では構造的要因）
        if inflation == InflationState.REACCELERATING:
            score -= 0.5
            reasoning.append("インフレ再加速の懸念")
        elif inflation == InflationState.MODERATE:
            score += 0.5
            reasoning.append("インフレが適正水準")
        
        # スコアを整数に丸める
        rounded_score = max(-2, min(2, round(score)))
        
        # 市場判断を決定
        if rounded_score >= 1.5:
            view = MarketViewState.STRONG_BULLISH
        elif rounded_score >= 0.5:
            view = MarketViewState.BULLISH
        elif rounded_score >= -0.5:
            view = MarketViewState.NEUTRAL
        elif rounded_score >= -1.5:
            view = MarketViewState.BEARISH
        else:
            view = MarketViewState.STRONG_BEARISH
        
        return view, rounded_score, reasoning
    
    def _format_key_states(self, states: Dict[str, str]) -> List[str]:
        """
        主要状態をフォーマット
        
        Args:
            states: 状態の辞書
        
        Returns:
            フォーマット済み状態リスト
        """
        key_states = []
        for key, value in states.items():
            key_states.append(f"{key}:{value}")
        return key_states


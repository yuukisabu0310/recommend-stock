"""
状態定義・マッピングモジュール
生データを状態（enum）に変換し、ルールベースで市場判断を行う
"""

from enum import Enum
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


# ============================================
# 状態定義（enum）
# ============================================

class InflationState(Enum):
    """インフレ状態"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH_STICKY = "high_sticky"  # 高止まり
    REACCELERATING = "reaccelerating"  # 再加速


class PolicyRateState(Enum):
    """政策金利状態"""
    EASING = "easing"  # 緩和
    HOLD = "hold"  # 維持
    TIGHTENING = "tightening"  # 引き締め


class EmploymentState(Enum):
    """雇用状態"""
    WEAK = "weak"
    STABLE = "stable"
    STRONG = "strong"


class GrowthState(Enum):
    """成長状態"""
    SLOWDOWN = "slowdown"  # 減速
    STABLE = "stable"
    RECOVERY = "recovery"  # 回復


class LongRateState(Enum):
    """長期金利状態"""
    LOW_LEVEL = "low_level"
    RISING = "rising"
    HIGH_LEVEL = "high_level"


class EquityValuationState(Enum):
    """株式評価状態"""
    CHEAP = "cheap"
    FAIR = "fair"
    HIGH_ZONE = "high_zone"


class VolatilityState(Enum):
    """ボラティリティ状態"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SectorConcentrationState(Enum):
    """セクター集中状態"""
    NONE = "none"
    MODERATE = "moderate"
    AI_HEAVY = "ai_heavy"
    SINGLE_THEME_HEAVY = "single_theme_heavy"


class LiquidityState(Enum):
    """流動性状態"""
    LOOSE = "loose"  # 緩い
    NEUTRAL = "neutral"
    TIGHT = "tight"  # 引き締め


class ExternalRiskState(Enum):
    """外部リスク状態"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class MarketViewState(Enum):
    """市場判断レベル"""
    STRONG_BULLISH = "strong_bullish"  # 超強気
    BULLISH = "bullish"  # やや強気
    NEUTRAL = "neutral"  # 中立
    BEARISH = "bearish"  # やや弱気
    STRONG_BEARISH = "strong_bearish"  # 弱気


# ============================================
# 状態変換ロジック
# ============================================

class StateMapper:
    """状態マッパークラス - 生データを状態に変換"""
    
    def __init__(self):
        """初期化"""
        pass
    
    def map_inflation(self, cpi: Optional[float], cpi_change: Optional[float] = None) -> InflationState:
        """
        インフレ状態を判定
        
        Args:
            cpi: CPI値
            cpi_change: CPI前年同月比変化率（%）
        
        Returns:
            インフレ状態
        """
        if cpi is None:
            return InflationState.MODERATE  # デフォルト
        
        # cpi_changeが利用可能な場合はそれを使用
        if cpi_change is not None:
            if cpi_change < 1.0:
                return InflationState.LOW
            elif 1.0 <= cpi_change < 3.0:
                return InflationState.MODERATE
            elif 3.0 <= cpi_change < 5.0:
                return InflationState.HIGH_STICKY
            else:
                # 前回より加速しているかチェック（簡易実装）
                return InflationState.REACCELERATING
        
        # cpi_changeがない場合はcpi値で判定（簡易）
        if cpi < 100:
            return InflationState.LOW
        elif cpi < 105:
            return InflationState.MODERATE
        elif cpi < 110:
            return InflationState.HIGH_STICKY
        else:
            return InflationState.REACCELERATING
    
    def map_policy_rate(self, current_rate: Optional[float], previous_rate: Optional[float] = None) -> PolicyRateState:
        """
        政策金利状態を判定
        
        Args:
            current_rate: 現在の政策金利（%）
            previous_rate: 前回の政策金利（%）
        
        Returns:
            政策金利状態
        """
        if current_rate is None:
            return PolicyRateState.HOLD  # デフォルト
        
        if previous_rate is not None:
            if current_rate < previous_rate:
                return PolicyRateState.EASING
            elif current_rate > previous_rate:
                return PolicyRateState.TIGHTENING
        
        return PolicyRateState.HOLD
    
    def map_employment(self, employment_rate: Optional[float], unemployment_rate: Optional[float] = None) -> EmploymentState:
        """
        雇用状態を判定
        
        Args:
            employment_rate: 雇用率（%）
            unemployment_rate: 失業率（%）
        
        Returns:
            雇用状態
        """
        if unemployment_rate is not None:
            if unemployment_rate < 3.0:
                return EmploymentState.STRONG
            elif unemployment_rate < 5.0:
                return EmploymentState.STABLE
            else:
                return EmploymentState.WEAK
        
        if employment_rate is not None:
            if employment_rate > 95.0:
                return EmploymentState.STRONG
            elif employment_rate > 90.0:
                return EmploymentState.STABLE
            else:
                return EmploymentState.WEAK
        
        return EmploymentState.STABLE  # デフォルト
    
    def map_growth(self, gdp_growth: Optional[float], pmi: Optional[float] = None) -> GrowthState:
        """
        成長状態を判定
        
        Args:
            gdp_growth: GDP成長率（%）
            pmi: PMI値
        
        Returns:
            成長状態
        """
        # PMIを優先
        if pmi is not None:
            if pmi > 55:
                return GrowthState.RECOVERY
            elif pmi > 50:
                return GrowthState.STABLE
            else:
                return GrowthState.SLOWDOWN
        
        # GDP成長率で判定
        if gdp_growth is not None:
            if gdp_growth > 3.0:
                return GrowthState.RECOVERY
            elif gdp_growth > 0:
                return GrowthState.STABLE
            else:
                return GrowthState.SLOWDOWN
        
        return GrowthState.STABLE  # デフォルト
    
    def map_long_rate(self, long_rate: Optional[float], historical_avg: Optional[float] = None) -> LongRateState:
        """
        長期金利状態を判定
        
        Args:
            long_rate: 長期金利（10年債、%）
            historical_avg: 過去平均値（%）
        
        Returns:
            長期金利状態
        """
        if long_rate is None:
            return LongRateState.LOW_LEVEL  # デフォルト
        
        if historical_avg is not None:
            if long_rate < historical_avg * 0.8:
                return LongRateState.LOW_LEVEL
            elif long_rate > historical_avg * 1.2:
                return LongRateState.HIGH_LEVEL
            elif long_rate > historical_avg * 1.05:
                return LongRateState.RISING
        
        # 絶対値で判定（簡易）
        if long_rate < 2.0:
            return LongRateState.LOW_LEVEL
        elif long_rate > 4.0:
            return LongRateState.HIGH_LEVEL
        elif long_rate > 3.0:
            return LongRateState.RISING
        
        return LongRateState.LOW_LEVEL
    
    def map_equity_valuation(self, pe_ratio: Optional[float], historical_pe: Optional[float] = None) -> EquityValuationState:
        """
        株式評価状態を判定
        
        Args:
            pe_ratio: PER値
            historical_pe: 過去平均PER
        
        Returns:
            株式評価状態
        """
        if pe_ratio is None:
            return EquityValuationState.FAIR  # デフォルト
        
        if historical_pe is not None:
            if pe_ratio < historical_pe * 0.8:
                return EquityValuationState.CHEAP
            elif pe_ratio > historical_pe * 1.2:
                return EquityValuationState.HIGH_ZONE
        
        # 絶対値で判定（簡易）
        if pe_ratio < 15:
            return EquityValuationState.CHEAP
        elif pe_ratio > 25:
            return EquityValuationState.HIGH_ZONE
        
        return EquityValuationState.FAIR
    
    def map_volatility(self, volatility: Optional[float]) -> VolatilityState:
        """
        ボラティリティ状態を判定
        
        Args:
            volatility: ボラティリティ（年率換算、%）
        
        Returns:
            ボラティリティ状態
        """
        if volatility is None:
            return VolatilityState.MEDIUM  # デフォルト
        
        if volatility < 15:
            return VolatilityState.LOW
        elif volatility > 30:
            return VolatilityState.HIGH
        
        return VolatilityState.MEDIUM
    
    def map_sector_concentration(self, top_concentration: Optional[float], ai_weight: Optional[float] = None) -> SectorConcentrationState:
        """
        セクター集中状態を判定
        
        Args:
            top_concentration: 上位銘柄集中度（0-1）
            ai_weight: AI関連セクターの重み（0-1）
        
        Returns:
            セクター集中状態
        """
        if top_concentration is None:
            return SectorConcentrationState.NONE
        
        # AI集中度チェック
        if ai_weight is not None and ai_weight > 0.3:
            return SectorConcentrationState.AI_HEAVY
        
        # 単一テーマ集中チェック
        if top_concentration > 0.35:
            return SectorConcentrationState.SINGLE_THEME_HEAVY
        elif top_concentration > 0.2:
            return SectorConcentrationState.MODERATE
        
        return SectorConcentrationState.NONE
    
    def map_liquidity(self, credit_spread: Optional[float], policy_rate: Optional[float] = None) -> LiquidityState:
        """
        流動性状態を判定
        
        Args:
            credit_spread: クレジットスプレッド（%）
            policy_rate: 政策金利（%）
        
        Returns:
            流動性状態
        """
        if credit_spread is None:
            return LiquidityState.NEUTRAL  # デフォルト
        
        if credit_spread < 1.0:
            return LiquidityState.LOOSE
        elif credit_spread > 3.0:
            return LiquidityState.TIGHT
        
        return LiquidityState.NEUTRAL
    
    def map_external_risk(self, vix: Optional[float] = None, geopolitical_events: Optional[List[str]] = None) -> ExternalRiskState:
        """
        外部リスク状態を判定
        
        Args:
            vix: VIX指数
            geopolitical_events: 地政学的イベントリスト
        
        Returns:
            外部リスク状態
        """
        if vix is not None:
            if vix > 25:
                return ExternalRiskState.HIGH
            elif vix > 15:
                return ExternalRiskState.MEDIUM
        
        if geopolitical_events and len(geopolitical_events) > 0:
            return ExternalRiskState.MEDIUM
        
        return ExternalRiskState.LOW  # デフォルト
    
    def map_all_states(self, country_data: Dict) -> Dict[str, str]:
        """
        全状態をマッピング
        
        Args:
            country_data: 国別データ
        
        Returns:
            状態の辞書
        """
        macro = country_data.get("macro", {})
        financial = country_data.get("financial", {})
        indices = country_data.get("indices", {})
        
        states = {}
        
        # マクロ指標
        states["inflation"] = self.map_inflation(
            macro.get("CPI"),
            macro.get("CPI_change")
        ).value
        
        states["policy_rate"] = self.map_policy_rate(
            financial.get("policy_rate"),
            financial.get("previous_policy_rate")
        ).value
        
        states["employment"] = self.map_employment(
            macro.get("employment_rate"),
            macro.get("unemployment_rate")
        ).value
        
        states["growth"] = self.map_growth(
            macro.get("GDP_growth"),
            macro.get("PMI")
        ).value
        
        # 金融市場
        states["long_rate"] = self.map_long_rate(
            financial.get("long_term_rate")
        ).value
        
        # インデックスデータから評価・ボラティリティを取得
        if indices:
            first_index = list(indices.values())[0]
            # PERは簡易的に価格/MA200の比率から推定（実際は別途取得が必要）
            states["equity_valuation"] = self.map_equity_valuation(
                first_index.get("pe_ratio")
            ).value
            
            states["volatility"] = self.map_volatility(
                first_index.get("volatility")
            ).value
        
        # 構造・需給
        if indices:
            first_index = list(indices.values())[0]
            states["sector_concentration"] = self.map_sector_concentration(
                first_index.get("top_stocks_concentration"),
                first_index.get("ai_sector_weight")
            ).value
        
        states["liquidity"] = self.map_liquidity(
            financial.get("credit_spread"),
            financial.get("policy_rate")
        ).value
        
        states["external_risk"] = self.map_external_risk(
            financial.get("vix")
        ).value
        
        return states


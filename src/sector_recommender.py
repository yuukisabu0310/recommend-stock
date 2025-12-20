"""
セクターおすすめロジック
テーマ → 波及 → 周辺産業の流れで決定
"""

from typing import Dict, List, Optional
from state_mapper import (
    InflationState, ExternalRiskState, PolicyRateState,
    SectorConcentrationState, GrowthState
)
import logging

logger = logging.getLogger(__name__)


class SectorRecommender:
    """セクター推薦クラス"""
    
    def __init__(self):
        """初期化"""
        # テーマ別セクターマッピング
        self.theme_sectors = {
            "geopolitical_risk": {
                "primary": ["防衛", "セキュリティ"],
                "spillover": ["資源安全保障", "食料・水", "鉱山・レアメタル"],
                "related": ["インフラ", "物流"]
            },
            "ai_concentration": {
                "primary": ["半導体", "AI"],
                "spillover": ["データセンター", "クラウドインフラ"],
                "related": ["電力・インフラ", "冷却・素材", "半導体製造装置"]
            },
            "financial_tightening": {
                "primary": ["高配当", "生活必需品"],
                "spillover": ["保険", "不動産（REIT）"],
                "related": ["公共事業", "通信"]
            },
            "inflation_hedge": {
                "primary": ["資源", "不動産"],
                "spillover": ["素材", "エネルギー"],
                "related": ["物流", "小売"]
            },
            "growth_recovery": {
                "primary": ["製造業", "自動車"],
                "spillover": ["機械", "素材"],
                "related": ["物流", "小売"]
            }
        }
    
    def recommend_sectors(
        self,
        states: Dict[str, str],
        timeframe_code: str
    ) -> List[Dict]:
        """
        セクターを推薦
        
        Args:
            states: 状態の辞書
            timeframe_code: 期間コード
        
        Returns:
            セクター推薦リスト
        """
        themes = self._identify_themes(states, timeframe_code)
        sectors = []
        
        for theme in themes:
            theme_data = self.theme_sectors.get(theme["name"], {})
            if not theme_data:
                continue
            
            # 主要セクター
            for sector_name in theme_data.get("primary", []):
                sectors.append({
                    "name": sector_name,
                    "theme": theme["name"],
                    "reason": theme["reason"],
                    "related_fields": theme_data.get("spillover", []),
                    "timeframe": timeframe_code,
                    "trend": "strong"
                })
            
            # 波及セクター
            for sector_name in theme_data.get("spillover", []):
                sectors.append({
                    "name": sector_name,
                    "theme": theme["name"],
                    "reason": f"{theme['reason']}の波及効果",
                    "related_fields": theme_data.get("related", []),
                    "timeframe": timeframe_code,
                    "trend": "moderate"
                })
        
        # 重複を除去し、上位3つを返す
        unique_sectors = {}
        for sector in sectors:
            name = sector["name"]
            if name not in unique_sectors or sector["trend"] == "strong":
                unique_sectors[name] = sector
        
        return list(unique_sectors.values())[:3]
    
    def _identify_themes(
        self,
        states: Dict[str, str],
        timeframe_code: str
    ) -> List[Dict]:
        """
        テーマを特定
        
        Args:
            states: 状態の辞書
            timeframe_code: 期間コード
        
        Returns:
            テーマリスト
        """
        themes = []
        
        # 地政学リスク
        external_risk = ExternalRiskState(states.get("external_risk", "low"))
        if external_risk == ExternalRiskState.HIGH or external_risk == ExternalRiskState.MEDIUM:
            themes.append({
                "name": "geopolitical_risk",
                "reason": "地政学リスク上昇により、防衛・セキュリティ関連が注目"
            })
        
        # AI集中
        sector_concentration = SectorConcentrationState(states.get("sector_concentration", "none"))
        if sector_concentration == SectorConcentrationState.AI_HEAVY:
            themes.append({
                "name": "ai_concentration",
                "reason": "AI関連セクターへの集中が高く、関連インフラ需要が拡大"
            })
        
        # 金融引き締め
        policy_rate = PolicyRateState(states.get("policy_rate", "hold"))
        if policy_rate == PolicyRateState.TIGHTENING:
            themes.append({
                "name": "financial_tightening",
                "reason": "金融引き締め長期化により、高配当・生活必需品が注目"
            })
        
        # インフレヘッジ
        inflation = InflationState(states.get("inflation", "moderate"))
        if inflation == InflationState.HIGH_STICKY or inflation == InflationState.REACCELERATING:
            themes.append({
                "name": "inflation_hedge",
                "reason": "インフレ高止まりにより、実物資産・資源が注目"
            })
        
        # 成長回復
        growth = GrowthState(states.get("growth", "stable"))
        if growth == GrowthState.RECOVERY:
            themes.append({
                "name": "growth_recovery",
                "reason": "成長回復により、製造業・自動車関連が注目"
            })
        
        return themes


"""
ベースページクラス
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Tuple
import yaml
import os
from datetime import datetime, timedelta


class BasePage(ABC):
    """ページの基底クラス"""
    
    def __init__(self, market_code: str, timeframe_code: str):
        """
        Args:
            market_code: 市場コード（"US" or "JP"）
            timeframe_code: 期間コード（"short", "medium", "long"）
        """
        self.market_code = market_code
        self.timeframe_code = timeframe_code
        self._load_configs()
    
    def _load_configs(self):
        """設定ファイルを読み込む"""
        config_dir = "config"
        
        # 市場設定
        with open(os.path.join(config_dir, "markets.yaml"), "r", encoding="utf-8") as f:
            markets_config = yaml.safe_load(f)
            self.market_config = next(
                (m for m in markets_config["markets"] if m["code"] == self.market_code),
                None
            )
        
        # 期間設定
        with open(os.path.join(config_dir, "timeframes.yaml"), "r", encoding="utf-8") as f:
            timeframes_config = yaml.safe_load(f)
            self.timeframe_config = next(
                (t for t in timeframes_config["timeframes"] if t["code"] == self.timeframe_code),
                None
            )
        
        # 指標設定
        with open(os.path.join(config_dir, "indicators.yaml"), "r", encoding="utf-8") as f:
            self.indicators_config = yaml.safe_load(f)
    
    def get_years(self) -> int:
        """デフォルトの表示年数を取得"""
        if self.timeframe_config:
            return self.timeframe_config.get("default_years", 1)
        return 1
    
    def get_switchable_years(self) -> list:
        """切替可能な年数のリストを取得"""
        if self.timeframe_config:
            return self.timeframe_config.get("switchable_years", [])
        return []
    
    def get_date_range(self, years: Optional[int] = None) -> Tuple[datetime, datetime]:
        """
        日付範囲を取得
        
        Args:
            years: 年数（Noneの場合はデフォルト値を使用）
        
        Returns:
            tuple: (開始日, 終了日)
        """
        if years is None:
            years = self.get_years()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years * 365)
        
        return start_date, end_date
    
    @abstractmethod
    def build(self) -> Dict[str, Any]:
        """
        ページを組み立てる
        
        Returns:
            dict: ページデータ（チャート、解釈など）
        """
        pass


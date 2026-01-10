"""
日本 - 短期ページ
"""
from .us_short import USShortPage


class JPShortPage(USShortPage):
    """日本 - 短期ページクラス"""
    
    def __init__(self):
        super().__init__()
        self.market_code = "JP"
        self.timeframe_code = "short"
        self._load_configs()


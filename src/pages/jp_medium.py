"""
日本 - 中期ページ
"""
from .us_short import USShortPage


class JPMediumPage(USShortPage):
    """日本 - 中期ページクラス"""
    
    def __init__(self):
        super().__init__()
        self.market_code = "JP"
        self.timeframe_code = "medium"
        self._load_configs()


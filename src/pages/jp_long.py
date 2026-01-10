"""
日本 - 長期ページ
"""
from .us_short import USShortPage


class JPLongPage(USShortPage):
    """日本 - 長期ページクラス"""
    
    def __init__(self):
        super().__init__()
        self.market_code = "JP"
        self.timeframe_code = "long"
        self._load_configs()


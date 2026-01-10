"""
米国 - 中期ページ
"""
from .us_short import USShortPage


class USMediumPage(USShortPage):
    """米国 - 中期ページクラス"""
    
    def __init__(self):
        super().__init__()
        self.timeframe_code = "medium"
        self._load_configs()


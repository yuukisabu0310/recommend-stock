"""
米国 - 長期ページ
"""
from .us_short import USShortPage


class USLongPage(USShortPage):
    """米国 - 長期ページクラス"""
    
    def __init__(self):
        super().__init__()
        self.timeframe_code = "long"
        self._load_configs()


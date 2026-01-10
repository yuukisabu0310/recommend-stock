"""
ベースチャートクラス
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


class BaseChart(ABC):
    """チャートの基底クラス"""
    
    def __init__(self, title: str):
        """
        Args:
            title: チャートタイトル
        """
        self.title = title
        self.fig: Optional[go.Figure] = None
    
    @abstractmethod
    def create_chart(self, data: pd.DataFrame, **kwargs) -> Optional[go.Figure]:
        """
        チャートを作成
        
        Args:
            data: チャート用データ
            **kwargs: 追加パラメータ
        
        Returns:
            Figure: PlotlyのFigureオブジェクト（データが無効な場合はNone）
        """
        pass
    
    def to_html(self, fig: Optional[go.Figure] = None) -> str:
        """
        チャートをHTMLに変換
        
        Args:
            fig: Figureオブジェクト（Noneの場合はself.figを使用）
        
        Returns:
            str: HTML文字列
        """
        if fig is None:
            fig = self.fig
        
        if fig is None:
            return "<p>この指標は現在データを取得できません</p>"
        
        return fig.to_html(include_plotlyjs='cdn', div_id=f"chart_{id(self)}")
    
    def get_no_data_message(self) -> str:
        """データが取得できない場合のメッセージ"""
        return "<p>この指標は現在データを取得できません</p>"


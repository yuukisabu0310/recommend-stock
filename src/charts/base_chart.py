"""
ベースチャートクラス
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
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
        チャートを作成（後方互換性のため残す）
        
        Args:
            data: チャート用データ
            **kwargs: 追加パラメータ
        
        Returns:
            Figure: PlotlyのFigureオブジェクト（データが無効な場合はNone）
        """
        pass
    
    @abstractmethod
    def create_multi_period_data(self, data: pd.DataFrame, periods: List[int], **kwargs) -> Dict[int, Dict[str, Any]]:
        """
        複数期間のチャートデータを生成（憲法準拠：すべての期間データを事前生成）
        
        Args:
            data: チャート用データ
            periods: 期間のリスト（例: [1, 5, 10]）
            **kwargs: 追加パラメータ
        
        Returns:
            Dict[int, Dict[str, Any]]: {years: {"traces": [...], "layout": {...}}, ...}
        """
        pass
    
    def to_html(self, fig: Optional[go.Figure] = None, chart_id: Optional[str] = None) -> str:
        """
        チャートをHTMLに変換（憲法準拠：初期表示用divのみ生成、Plotly.newPlotは1回だけ）
        
        Args:
            fig: Figureオブジェクト（Noneの場合はself.figを使用）
            chart_id: チャートID（指定されない場合は自動生成）
        
        Returns:
            str: HTML文字列（div要素のみ、Plotly.newPlotのscriptは含まない）
        """
        if chart_id is None:
            chart_id = f"chart_{id(self)}"
        
        if fig is None:
            fig = self.fig
        
        if fig is None:
            return f'<div id="{chart_id}" class="plotly-graph-div" style="height:400px; width:100%;"></div>'
        
        # Plotlyのto_htmlは完全なHTMLを返すため、div要素のみを抽出
        html = fig.to_html(include_plotlyjs=False, div_id=chart_id)
        
        # <html>タグや<head>タグ、<body>タグを削除し、div要素のみを返す
        import re
        # <body>タグの中身を抽出
        body_match = re.search(r'<body[^>]*>(.*?)</body>', html, re.DOTALL)
        if body_match:
            body_content = body_match.group(1)
            # <div>要素のみを抽出（scriptは除外）
            div_matches = re.findall(r'<div[^>]*>.*?</div>', body_content, re.DOTALL)
            
            if div_matches:
                return div_matches[0]
        
        # フォールバック：div要素のみを返す
        return f'<div id="{chart_id}" class="plotly-graph-div" style="height:400px; width:100%;"></div>'
    
    def get_no_data_message(self) -> str:
        """データが取得できない場合のメッセージ"""
        return "<p>この指標は現在データを取得できません</p>"


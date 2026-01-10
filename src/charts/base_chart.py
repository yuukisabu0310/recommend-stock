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
        チャートをHTMLに変換（CSP準拠：完全なHTMLではなくdiv要素のみ返す）
        
        Args:
            fig: Figureオブジェクト（Noneの場合はself.figを使用）
        
        Returns:
            str: HTML文字列（div要素とscript要素のみ）
        """
        if fig is None:
            fig = self.fig
        
        if fig is None:
            return "<p>この指標は現在データを取得できません</p>"
        
        # Plotlyのto_htmlは完全なHTMLを返すため、div要素とscript要素のみを抽出
        html = fig.to_html(include_plotlyjs='cdn', div_id=f"chart_{id(self)}")
        
        # <html>タグや<head>タグ、<body>タグを削除し、div要素とscript要素のみを返す
        import re
        # <body>タグの中身を抽出
        body_match = re.search(r'<body[^>]*>(.*?)</body>', html, re.DOTALL)
        if body_match:
            body_content = body_match.group(1)
            # <div>要素と<script>要素のみを抽出
            div_matches = re.findall(r'<div[^>]*>.*?</div>', body_content, re.DOTALL)
            script_matches = re.findall(r'<script[^>]*>.*?</script>', body_content, re.DOTALL)
            
            result = ""
            for div in div_matches:
                result += div + "\n"
            for script in script_matches:
                result += script + "\n"
            
            return result.strip()
        
        # フォールバック：元のHTMLを返す
        return html
    
    def get_no_data_message(self) -> str:
        """データが取得できない場合のメッセージ"""
        return "<p>この指標は現在データを取得できません</p>"


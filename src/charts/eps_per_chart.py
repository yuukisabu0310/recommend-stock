"""
EPS + PERチャート
"""
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Optional
from .base_chart import BaseChart


class EPSPERChart(BaseChart):
    """EPS + PERチャートクラス"""
    
    def __init__(self, market_name: str):
        """
        Args:
            market_name: 市場名（例: "米国", "日本"）
        """
        title = f"{market_name} - EPS + PER"
        super().__init__(title)
        self.market_name = market_name
    
    def create_chart(self, data: pd.DataFrame) -> Optional[go.Figure]:
        """
        EPS + PERチャートを作成（20年固定）
        
        Args:
            data: EPS + PERデータ（EPS, PER）
        
        Returns:
            Figure: PlotlyのFigureオブジェクト
        """
        if data is None or data.empty:
            return None
        
        if 'EPS' not in data.columns or 'PER' not in data.columns:
            return None
        
        # 20年前からフィルタリング
        end_date = datetime.now()
        start_date = end_date - timedelta(days=20 * 365)
        filtered_data = data[(data.index >= start_date) & (data.index <= end_date)]
        
        if filtered_data.empty:
            return None
        
        # サブプロット作成（上下2段）
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('EPS', 'PER'),
            vertical_spacing=0.1,
            shared_xaxes=True
        )
        
        # EPSチャート
        fig.add_trace(
            go.Scatter(
                x=filtered_data.index,
                y=filtered_data['EPS'],
                mode='lines+markers',
                name='EPS',
                line=dict(color='#2563eb', width=2),
                marker=dict(size=4)
            ),
            row=1, col=1
        )
        
        # PERチャート
        fig.add_trace(
            go.Scatter(
                x=filtered_data.index,
                y=filtered_data['PER'],
                mode='lines+markers',
                name='PER',
                line=dict(color='#f59e0b', width=2),
                marker=dict(size=4)
            ),
            row=2, col=1
        )
        
        # レイアウト設定
        fig.update_layout(
            title=self.title,
            height=600,
            hovermode='x unified',
            template='plotly_white',
            margin=dict(l=50, r=50, t=50, b=50),
            showlegend=False
        )
        
        # Y軸ラベル設定
        fig.update_yaxes(title_text="EPS", row=1, col=1)
        fig.update_yaxes(title_text="PER", row=2, col=1)
        fig.update_xaxes(title_text="日付", row=2, col=1)
        
        self.fig = fig
        return fig


"""
CPIチャート
"""
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Optional
from .base_chart import BaseChart


class CPIChart(BaseChart):
    """CPIチャートクラス"""
    
    def __init__(self, market_name: str):
        """
        Args:
            market_name: 市場名（例: "米国", "日本"）
        """
        title = f"{market_name} - CPI（消費者物価指数）前年比"
        super().__init__(title)
        self.market_name = market_name
    
    def create_chart(self, data: pd.DataFrame, years: int = 1) -> Optional[go.Figure]:
        """
        CPIチャートを作成
        
        Args:
            data: CPIデータ（CPI_YoY）
            years: 表示年数
        
        Returns:
            Figure: PlotlyのFigureオブジェクト
        """
        if data is None or data.empty:
            return None
        
        if 'CPI_YoY' not in data.columns:
            return None
        
        # 期間でフィルタリング
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years * 365)
        filtered_data = data[(data.index >= start_date) & (data.index <= end_date)]
        
        if filtered_data.empty:
            return None
        
        # チャート作成
        fig = go.Figure()
        
        # CPI前年比
        fig.add_trace(go.Scatter(
            x=filtered_data.index,
            y=filtered_data['CPI_YoY'],
            mode='lines+markers',
            name='CPI前年比',
            line=dict(color='#2563eb', width=2),
            marker=dict(size=4)
        ))
        
        # 0%の基準線
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
        
        # レイアウト設定
        fig.update_layout(
            title=self.title,
            xaxis_title="日付",
            yaxis_title="CPI前年比 (%)",
            hovermode='x unified',
            template='plotly_white',
            height=400,
            margin=dict(l=50, r=50, t=50, b=50),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        self.fig = fig
        return fig


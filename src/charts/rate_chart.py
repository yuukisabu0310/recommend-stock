"""
政策金利 + 長期金利チャート
"""
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Optional
from .base_chart import BaseChart


class RateChart(BaseChart):
    """政策金利 + 長期金利チャートクラス"""
    
    def __init__(self, market_name: str):
        """
        Args:
            market_name: 市場名（例: "米国", "日本"）
        """
        title = f"{market_name} - 政策金利・長期金利"
        super().__init__(title)
        self.market_name = market_name
    
    def create_chart(self, policy_data: pd.DataFrame, long_rate_data: pd.DataFrame, 
                    years: int = 1) -> Optional[go.Figure]:
        """
        金利チャートを作成（政策金利と長期金利を重ねて表示）
        
        Args:
            policy_data: 政策金利データ
            long_rate_data: 長期金利データ
            years: 表示年数
        
        Returns:
            Figure: PlotlyのFigureオブジェクト
        """
        # データが空の場合はNoneを返す
        if (policy_data is None or policy_data.empty) and (long_rate_data is None or long_rate_data.empty):
            return None
        
        # 期間でフィルタリング
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years * 365)
        
        policy_filtered = pd.DataFrame()
        long_rate_filtered = pd.DataFrame()
        
        if policy_data is not None and not policy_data.empty:
            policy_filtered = policy_data[(policy_data.index >= start_date) & (policy_data.index <= end_date)]
        
        if long_rate_data is not None and not long_rate_data.empty:
            long_rate_filtered = long_rate_data[(long_rate_data.index >= start_date) & (long_rate_data.index <= end_date)]
        
        # 両方空の場合はNoneを返す
        if policy_filtered.empty and long_rate_filtered.empty:
            return None
        
        # チャート作成
        fig = go.Figure()
        
        # 政策金利
        if not policy_filtered.empty and 'policy_rate' in policy_filtered.columns:
            fig.add_trace(go.Scatter(
                x=policy_filtered.index,
                y=policy_filtered['policy_rate'],
                mode='lines',
                name='政策金利（名目）',
                line=dict(color='#2563eb', width=2)
            ))
        
        # 長期金利（10年）
        if not long_rate_filtered.empty and 'long_rate_10y' in long_rate_filtered.columns:
            fig.add_trace(go.Scatter(
                x=long_rate_filtered.index,
                y=long_rate_filtered['long_rate_10y'],
                mode='lines',
                name='長期金利（10年）',
                line=dict(color='#f59e0b', width=2)
            ))
        
        # レイアウト設定
        fig.update_layout(
            title=self.title,
            xaxis_title="日付",
            yaxis_title="金利 (%)",
            hovermode='x unified',
            template='plotly_white',
            height=400,
            margin=dict(l=50, r=50, t=50, b=50),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        self.fig = fig
        return fig


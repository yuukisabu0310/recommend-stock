"""
CPIチャート
"""
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
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
        
        # タイムゾーン情報を削除（比較エラーを回避）
        data = data.copy()
        if data.index.tz is not None:
            data.index = data.index.tz_localize(None)
        
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
    
    def create_multi_period_data(self, data: pd.DataFrame, periods: List[int]) -> Dict[int, Dict[str, Any]]:
        """
        複数期間のチャートデータを生成（憲法準拠）
        
        Args:
            data: CPIデータ（CPI_YoY）
            periods: 期間のリスト（例: [1, 5, 10]）
        
        Returns:
            Dict[int, Dict[str, Any]]: {years: {"traces": [...], "layout": {...}}, ...}
        """
        result = {}
        
        if data is None or data.empty:
            return result
        
        if 'CPI_YoY' not in data.columns:
            return result
        
        # タイムゾーン情報を削除
        data = data.copy()
        if data.index.tz is not None:
            data.index = data.index.tz_localize(None)
        
        for years in periods:
            # 期間でフィルタリング
            end_date = datetime.now()
            start_date = end_date - timedelta(days=years * 365)
            filtered_data = data[(data.index >= start_date) & (data.index <= end_date)]
            
            if filtered_data.empty:
                continue
            
            # tracesを生成
            traces = [{
                "x": filtered_data.index.strftime("%Y-%m-%d").tolist(),
                "y": filtered_data['CPI_YoY'].tolist(),
                "mode": "lines+markers",
                "name": "CPI前年比",
                "line": {"color": "#2563eb", "width": 2},
                "marker": {"size": 4},
                "type": "scatter"
            }]
            
            # layoutを生成
            layout = {
                "title": self.title,
                "xaxis": {"title": "日付"},
                "yaxis": {"title": "CPI前年比 (%)"},
                "hovermode": "x unified",
                "height": 400,
                "margin": {"l": 50, "r": 50, "t": 50, "b": 50},
                "legend": {"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
                "shapes": [{
                    "type": "line",
                    "xref": "x domain",
                    "yref": "y",
                    "x0": 0,
                    "x1": 1,
                    "y0": 0,
                    "y1": 0,
                    "line": {"color": "gray", "dash": "dash", "opacity": 0.5}
                }]
            }
            
            result[years] = {
                "traces": traces,
                "layout": layout
            }
        
        return result


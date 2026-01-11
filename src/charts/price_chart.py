"""
株価指数チャート
"""
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from .base_chart import BaseChart


class PriceChart(BaseChart):
    """株価指数チャートクラス"""
    
    def __init__(self, market_name: str, index_name: str):
        """
        Args:
            market_name: 市場名（例: "米国", "日本"）
            index_name: 指数名（例: "S&P500", "日経平均"）
        """
        title = f"{market_name} - {index_name}"
        super().__init__(title)
        self.market_name = market_name
        self.index_name = index_name
    
    def create_chart(self, data: pd.DataFrame, years: int = 1, 
                    switchable_years: Optional[list] = None) -> Optional[go.Figure]:
        """
        株価チャートを作成
        
        Args:
            data: 株価データ（Close, MA20, MA75, MA200）
            years: 表示年数
            switchable_years: 切替可能な年数のリスト
        
        Returns:
            Figure: PlotlyのFigureオブジェクト
        """
        if data is None or data.empty:
            return None
        
        if 'Close' not in data.columns:
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
        
        # 株価（実線）
        fig.add_trace(go.Scatter(
            x=filtered_data.index,
            y=filtered_data['Close'],
            mode='lines',
            name='株価',
            line=dict(color='#2563eb', width=2)
        ))
        
        # 移動平均（波線）
        if 'MA20' in filtered_data.columns:
            fig.add_trace(go.Scatter(
                x=filtered_data.index,
                y=filtered_data['MA20'],
                mode='lines',
                name='MA20',
                line=dict(color='#f59e0b', width=1, dash='dash')
            ))
        
        if 'MA75' in filtered_data.columns:
            fig.add_trace(go.Scatter(
                x=filtered_data.index,
                y=filtered_data['MA75'],
                mode='lines',
                name='MA75',
                line=dict(color='#10b981', width=1, dash='dash')
            ))
        
        if 'MA200' in filtered_data.columns:
            fig.add_trace(go.Scatter(
                x=filtered_data.index,
                y=filtered_data['MA200'],
                mode='lines',
                name='MA200',
                line=dict(color='#ef4444', width=1, dash='dash')
            ))
        
        # レイアウト設定
        fig.update_layout(
            title=self.title,
            xaxis_title="日付",
            yaxis_title="株価",
            hovermode='x unified',
            template='plotly_white',
            height=400,
            margin=dict(l=50, r=50, t=50, b=50),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        # Y軸のマージンを確保
        y_min = filtered_data['Close'].min()
        y_max = filtered_data['Close'].max()
        y_range = y_max - y_min
        fig.update_yaxes(range=[y_min - y_range * 0.1, y_max + y_range * 0.1])
        
        self.fig = fig
        return fig
    
    def create_multi_period_data(self, data: pd.DataFrame, periods: List[int]) -> Dict[int, Dict[str, Any]]:
        """
        複数期間のチャートデータを生成（憲法準拠）
        
        Args:
            data: 株価データ（Close, MA20, MA75, MA200）
            periods: 期間のリスト（例: [1, 5, 10]）
        
        Returns:
            Dict[int, Dict[str, Any]]: {years: {"traces": [...], "layout": {...}}, ...}
        """
        result = {}
        
        if data is None or data.empty:
            return result
        
        if 'Close' not in data.columns:
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
            traces = []
            
            # 株価（実線）
            traces.append({
                "x": filtered_data.index.strftime("%Y-%m-%d").tolist(),
                "y": filtered_data['Close'].tolist(),
                "mode": "lines",
                "name": "株価",
                "line": {"color": "#2563eb", "width": 2},
                "type": "scatter"
            })
            
            # 移動平均（波線）
            if 'MA20' in filtered_data.columns:
                traces.append({
                    "x": filtered_data.index.strftime("%Y-%m-%d").tolist(),
                    "y": filtered_data['MA20'].tolist(),
                    "mode": "lines",
                    "name": "MA20",
                    "line": {"color": "#f59e0b", "width": 1, "dash": "dash"},
                    "type": "scatter"
                })
            
            if 'MA75' in filtered_data.columns:
                traces.append({
                    "x": filtered_data.index.strftime("%Y-%m-%d").tolist(),
                    "y": filtered_data['MA75'].tolist(),
                    "mode": "lines",
                    "name": "MA75",
                    "line": {"color": "#10b981", "width": 1, "dash": "dash"},
                    "type": "scatter"
                })
            
            if 'MA200' in filtered_data.columns:
                traces.append({
                    "x": filtered_data.index.strftime("%Y-%m-%d").tolist(),
                    "y": filtered_data['MA200'].tolist(),
                    "mode": "lines",
                    "name": "MA200",
                    "line": {"color": "#ef4444", "width": 1, "dash": "dash"},
                    "type": "scatter"
                })
            
            # layoutを生成
            layout = {
                "title": self.title,
                "xaxis": {"title": "日付"},
                "yaxis": {"title": "株価"},
                "hovermode": "x unified",
                "height": 400,
                "margin": {"l": 50, "r": 50, "t": 50, "b": 50},
                "legend": {"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1}
            }
            
            # Y軸のマージンを確保
            y_min = filtered_data['Close'].min()
            y_max = filtered_data['Close'].max()
            y_range = y_max - y_min
            layout["yaxis"]["range"] = [y_min - y_range * 0.1, y_max + y_range * 0.1]
            
            result[years] = {
                "traces": traces,
                "layout": layout
            }
        
        return result


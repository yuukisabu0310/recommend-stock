"""
EPS + PERチャート
"""
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
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
        
        if 'PER' not in data.columns:
            return None
        
        # USの場合はEPSがNoneでもOK
        has_eps = 'EPS' in data.columns and data['EPS'].notna().any()
        
        # タイムゾーン情報を削除（比較エラーを回避）
        data = data.copy()
        if data.index.tz is not None:
            data.index = data.index.tz_localize(None)
        
        # 20年前からフィルタリング
        end_date = datetime.now()
        start_date = end_date - timedelta(days=20 * 365)
        filtered_data = data[(data.index >= start_date) & (data.index <= end_date)]
        
        if filtered_data.empty:
            return None
        
        # サブプロット作成（EPSがある場合は上下2段、ない場合は1段）
        if has_eps:
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
            
            # Y軸ラベル設定
            fig.update_yaxes(title_text="EPS", row=1, col=1)
            fig.update_yaxes(title_text="PER", row=2, col=1)
            fig.update_xaxes(title_text="日付", row=2, col=1)
        else:
            # USの場合、PERのみ
            fig = make_subplots(
                rows=1, cols=1,
                subplot_titles=('PER',),
                shared_xaxes=True
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
                row=1, col=1
            )
            
            # Y軸ラベル設定
            fig.update_yaxes(title_text="PER", row=1, col=1)
            fig.update_xaxes(title_text="日付", row=1, col=1)
        
        # レイアウト設定
        fig.update_layout(
            title=self.title,
            height=600 if has_eps else 400,
            hovermode='x unified',
            template='plotly_white',
            margin=dict(l=50, r=50, t=50, b=50),
            showlegend=False
        )
        
        self.fig = fig
        return fig
    
    def create_multi_period_data(self, data: pd.DataFrame, periods: List[int] = None) -> Dict[int, Dict[str, Any]]:
        """
        複数期間のチャートデータを生成（憲法準拠：EPS/PERは20年固定）
        
        Args:
            data: EPS + PERデータ（EPS, PER）
            periods: 期間のリスト（EPS/PERは無視され、20年固定）
        
        Returns:
            Dict[int, Dict[str, Any]]: {20: {"traces": [...], "layout": {...}}}
        """
        result = {}
        
        if data is None or data.empty:
            return result
        
        if 'PER' not in data.columns:
            return result
        
        # USの場合はEPSがNoneでもOK
        has_eps = 'EPS' in data.columns and data['EPS'].notna().any()
        
        # タイムゾーン情報を削除
        data = data.copy()
        if data.index.tz is not None:
            data.index = data.index.tz_localize(None)
        
        # 20年前からフィルタリング
        end_date = datetime.now()
        start_date = end_date - timedelta(days=20 * 365)
        filtered_data = data[(data.index >= start_date) & (data.index <= end_date)]
        
        if filtered_data.empty:
            return result
        
        # tracesを生成（サブプロット用）
        traces = []
        if has_eps:
            traces.append({
                "x": filtered_data.index.strftime("%Y-%m-%d").tolist(),
                "y": filtered_data['EPS'].tolist(),
                "mode": "lines+markers",
                "name": "EPS",
                "line": {"color": "#2563eb", "width": 2},
                "marker": {"size": 4},
                "type": "scatter",
                "xaxis": "x",
                "yaxis": "y"
            })
            traces.append({
                "x": filtered_data.index.strftime("%Y-%m-%d").tolist(),
                "y": filtered_data['PER'].tolist(),
                "mode": "lines+markers",
                "name": "PER",
                "line": {"color": "#f59e0b", "width": 2},
                "marker": {"size": 4},
                "type": "scatter",
                "xaxis": "x2",
                "yaxis": "y2"
            })
        else:
            traces.append({
                "x": filtered_data.index.strftime("%Y-%m-%d").tolist(),
                "y": filtered_data['PER'].tolist(),
                "mode": "lines+markers",
                "name": "PER",
                "line": {"color": "#f59e0b", "width": 2},
                "marker": {"size": 4},
                "type": "scatter",
                "xaxis": "x",
                "yaxis": "y"
            })
        
        # layoutを生成（サブプロット用）
        if has_eps:
            layout = {
                "title": self.title,
                "height": 600,
                "hovermode": "x unified",
                "margin": {"l": 50, "r": 50, "t": 50, "b": 50},
                "showlegend": False,
                "grid": {"rows": 2, "columns": 1, "pattern": "independent"},
                "xaxis": {"title": "", "domain": [0, 1], "anchor": "y"},
                "xaxis2": {"title": "日付", "domain": [0, 1], "anchor": "y2"},
                "yaxis": {"title": "EPS", "domain": [0.55, 1]},
                "yaxis2": {"title": "PER", "domain": [0, 0.45]}
            }
        else:
            layout = {
                "title": self.title,
                "height": 400,
                "hovermode": "x unified",
                "margin": {"l": 50, "r": 50, "t": 50, "b": 50},
                "showlegend": False,
                "xaxis": {"title": "日付", "domain": [0, 1], "anchor": "y"},
                "yaxis": {"title": "PER", "domain": [0, 1]}
            }
        
        result[20] = {
            "traces": traces,
            "layout": layout
        }
        
        return result


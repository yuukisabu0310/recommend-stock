"""
EPS + PERチャート
"""
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from .base_chart import BaseChart

# 定数定義
PER_BENCHMARK = 20.0  # PER固定基準線


class EPSPERChart(BaseChart):
    """EPS + PERチャートクラス"""
    
    def __init__(self, market_name: str):
        """
        Args:
            market_name: 市場名（例: "米国", "日本"）
        """
        title = f"{market_name} - Market EPS & PER Analysis"
        super().__init__(title)
        self.market_name = market_name
    
    def create_chart(self, data: pd.DataFrame, years: int = 20) -> Optional[go.Figure]:
        """
        EPS + PERチャートを作成
        EPS中央値と市場PERを表示、PER=20の固定基準線を追加
        
        Args:
            data: EPS + PERデータ（EPS: EPS中央値, PER: 市場PER）
            years: 表示年数（short: 5, medium: 10, long: 20）
        
        Returns:
            Figure: PlotlyのFigureオブジェクト
        """
        if data is None or data.empty:
            return None
        
        if 'PER' not in data.columns:
            return None
        
        # EPSデータの有無を確認
        has_eps = 'EPS' in data.columns and data['EPS'].notna().any()
        
        # タイムゾーン情報を削除（比較エラーを回避）
        data = data.copy()
        if data.index.tz is not None:
            data.index = data.index.tz_localize(None)
        
        # 指定年数前からフィルタリング
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years * 365)
        filtered_data = data[(data.index >= start_date) & (data.index <= end_date)]
        
        if filtered_data.empty:
            return None
        
        # サブプロット作成（EPSがある場合は上下2段、ない場合は1段）
        if has_eps:
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=(f'EPS中央値（{years}年推移）', f'市場PER（{years}年推移）'),
                vertical_spacing=0.1,
                shared_xaxes=True
            )
            
            # EPS中央値チャート
            fig.add_trace(
                go.Scatter(
                    x=filtered_data.index,
                    y=filtered_data['EPS'],
                    mode='lines+markers',
                    name='EPS中央値',
                    line=dict(color='#2563eb', width=2),
                    marker=dict(size=4)
                ),
                row=1, col=1
            )
            
            # 市場PERチャート
            fig.add_trace(
                go.Scatter(
                    x=filtered_data.index,
                    y=filtered_data['PER'],
                    mode='lines+markers',
                    name='市場PER',
                    line=dict(color='#f59e0b', width=2),
                    marker=dict(size=4)
                ),
                row=2, col=1
            )
            
            # PER=20の固定基準線
            fig.add_hline(
                y=PER_BENCHMARK,
                line_dash="dash",
                line_color="gray",
                annotation_text=f"PER={PER_BENCHMARK}",
                annotation_position="right",
                row=2, col=1
            )
            
            # Y軸ラベル設定
            fig.update_yaxes(title_text="EPS中央値", row=1, col=1)
            fig.update_yaxes(title_text="市場PER", row=2, col=1)
            fig.update_xaxes(title_text="日付", row=2, col=1)
        else:
            # EPSがない場合（USなど）、PERのみ
            fig = make_subplots(
                rows=1, cols=1,
                subplot_titles=(f'市場PER（{years}年推移）',),
                shared_xaxes=True
            )
            
            # 市場PERチャート
            fig.add_trace(
                go.Scatter(
                    x=filtered_data.index,
                    y=filtered_data['PER'],
                    mode='lines+markers',
                    name='市場PER',
                    line=dict(color='#f59e0b', width=2),
                    marker=dict(size=4)
                ),
                row=1, col=1
            )
            
            # PER=20の固定基準線
            fig.add_hline(
                y=PER_BENCHMARK,
                line_dash="dash",
                line_color="gray",
                annotation_text=f"PER={PER_BENCHMARK}",
                annotation_position="right",
                row=1, col=1
            )
            
            # Y軸ラベル設定
            fig.update_yaxes(title_text="市場PER", row=1, col=1)
            fig.update_xaxes(title_text="日付", row=1, col=1)
        
        # レイアウト設定
        fig.update_layout(
            title=self.title,
            height=600 if has_eps else 400,
            hovermode='x unified',
            template='plotly_white',
            margin=dict(l=50, r=50, t=50, b=50),
            showlegend=True
        )
        
        self.fig = fig
        return fig
    
    def create_multi_period_data(self, data: pd.DataFrame, periods: List[int] = None) -> Dict[int, Dict[str, Any]]:
        """
        複数期間のチャートデータを生成（憲法準拠：EPS/PERは20年固定）
        short/medium/longに応じて表示範囲を調整
        
        Args:
            data: EPS + PERデータ（EPS: EPS中央値, PER: 市場PER）
            periods: 期間のリスト（short: 5年, medium: 10年, long: 20年）
        
        Returns:
            Dict[int, Dict[str, Any]]: {5/10/20: {"traces": [...], "layout": {...}}}
        """
        result = {}
        
        if data is None or data.empty:
            return result
        
        if 'PER' not in data.columns:
            return result
        
        # EPSデータの有無を確認
        has_eps = 'EPS' in data.columns and data['EPS'].notna().any()
        
        # タイムゾーン情報を削除
        data = data.copy()
        if data.index.tz is not None:
            data.index = data.index.tz_localize(None)
        
        # 期間ごとにデータを生成
        end_date = datetime.now()
        period_years = [5, 10, 20]  # short, medium, long
        
        for years in period_years:
            start_date = end_date - timedelta(days=years * 365)
            filtered_data = data[(data.index >= start_date) & (data.index <= end_date)]
            
            if filtered_data.empty:
                continue
            
            # tracesを生成（サブプロット用）
            traces = []
            if has_eps:
                traces.append({
                    "x": filtered_data.index.strftime("%Y-%m-%d").tolist(),
                    "y": filtered_data['EPS'].tolist(),
                    "mode": "lines+markers",
                    "name": "EPS中央値",
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
                    "name": "市場PER",
                    "line": {"color": "#f59e0b", "width": 2},
                    "marker": {"size": 4},
                    "type": "scatter",
                    "xaxis": "x2",
                    "yaxis": "y2"
                })
                # PER=20の固定基準線
                traces.append({
                    "x": [filtered_data.index.min().strftime("%Y-%m-%d"), filtered_data.index.max().strftime("%Y-%m-%d")],
                    "y": [PER_BENCHMARK, PER_BENCHMARK],
                    "mode": "lines",
                    "name": f"PER={PER_BENCHMARK}",
                    "line": {"color": "gray", "dash": "dash", "width": 1},
                    "type": "scatter",
                    "xaxis": "x2",
                    "yaxis": "y2"
                })
            else:
                traces.append({
                    "x": filtered_data.index.strftime("%Y-%m-%d").tolist(),
                    "y": filtered_data['PER'].tolist(),
                    "mode": "lines+markers",
                    "name": "市場PER",
                    "line": {"color": "#f59e0b", "width": 2},
                    "marker": {"size": 4},
                    "type": "scatter",
                    "xaxis": "x",
                    "yaxis": "y"
                })
                # PER=20の固定基準線
                traces.append({
                    "x": [filtered_data.index.min().strftime("%Y-%m-%d"), filtered_data.index.max().strftime("%Y-%m-%d")],
                    "y": [PER_BENCHMARK, PER_BENCHMARK],
                    "mode": "lines",
                    "name": f"PER={PER_BENCHMARK}",
                    "line": {"color": "gray", "dash": "dash", "width": 1},
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
                    "showlegend": True,
                    "grid": {"rows": 2, "columns": 1, "pattern": "independent"},
                    "xaxis": {"title": "", "domain": [0, 1], "anchor": "y"},
                    "xaxis2": {"title": "日付", "domain": [0, 1], "anchor": "y2"},
                    "yaxis": {"title": "EPS中央値", "domain": [0.55, 1]},
                    "yaxis2": {"title": "市場PER", "domain": [0, 0.45]}
                }
            else:
                layout = {
                    "title": self.title,
                    "height": 400,
                    "hovermode": "x unified",
                    "margin": {"l": 50, "r": 50, "t": 50, "b": 50},
                    "showlegend": True,
                    "xaxis": {"title": "日付", "domain": [0, 1], "anchor": "y"},
                    "yaxis": {"title": "市場PER", "domain": [0, 1]}
                }
            
            result[years] = {
                "traces": traces,
                "layout": layout
            }
        
        return result


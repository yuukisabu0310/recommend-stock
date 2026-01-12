"""
EPS + PERデータ取得
"""
import pandas as pd
from datetime import datetime
from typing import Optional
import requests
from bs4 import BeautifulSoup
import re
from .base_fetcher import BaseFetcher


def fetch_sp500_per() -> pd.DataFrame:
    """
    S&P500 PERデータを取得（multpl.comからスクレイピング）
    
    Returns:
        DataFrame: S&P500 PERデータ
            columns:
            - date
            - sp500_per
    """
    try:
        url = "https://www.multpl.com/s-p-500-pe-ratio"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, timeout=30, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # JavaScript内のデータを探す
        scripts = soup.find_all('script')
        data_points = []
        
        for script in scripts:
            if script.string:
                # データ配列を探す（例: [[date, value], ...]）
                # multpl.comは通常、JavaScript内にデータ配列を含む
                matches = re.findall(r'\["([^"]+)",\s*([\d.]+)\]', script.string)
                if matches:
                    for date_str, per_str in matches:
                        try:
                            date = pd.to_datetime(date_str)
                            per_value = float(per_str)
                            data_points.append({'date': date, 'sp500_per': per_value})
                        except (ValueError, AttributeError):
                            continue
        
        # JavaScript内のデータが見つからない場合、テーブルから抽出を試みる
        if not data_points:
            table = soup.find('table', {'id': 'datatable'}) or soup.find('table')
            if table:
                rows = table.find_all('tr')
                for row in rows[1:]:  # ヘッダー行をスキップ
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        date_str = cells[0].get_text(strip=True)
                        per_str = cells[1].get_text(strip=True)
                        
                        try:
                            date = pd.to_datetime(date_str)
                            per_value = float(re.sub(r'[^\d.]', '', per_str))
                            data_points.append({'date': date, 'sp500_per': per_value})
                        except (ValueError, AttributeError):
                            continue
        
        if not data_points:
            print("multpl.comから有効なデータを取得できませんでした")
            return pd.DataFrame()
        
        df = pd.DataFrame(data_points)
        df.set_index('date', inplace=True)
        df.sort_index(inplace=True)
        
        return df
        
    except Exception as e:
        print(f"S&P500 PERデータ取得エラー: {e}")
        return pd.DataFrame()


def fetch_nikkei_eps_per() -> pd.DataFrame:
    """
    日経平均EPS/PERデータを取得（nikkei.co.jpからCSV読み込み）
    
    Returns:
        DataFrame: 日経平均EPS/PERデータ
            columns:
            - date
            - nikkei_eps
            - nikkei_per
    """
    try:
        # 日経平均のCSV URL（実際のURLを確認して調整が必要）
        url = "https://indexes.nikkei.co.jp/nkave/archives/data"
        
        # エンコーディングを試行（shift_jis, utf-8）
        for encoding in ['shift_jis', 'utf-8', 'cp932']:
            try:
                df = pd.read_csv(url, encoding=encoding)
                break
            except (UnicodeDecodeError, pd.errors.ParserError):
                continue
        else:
            print("日経平均CSVの読み込みに失敗しました")
            return pd.DataFrame()
        
        # カラム名を確認・調整
        # 実際のCSV構造に応じて調整が必要
        if df.empty:
            print("日経平均CSVが空です")
            return pd.DataFrame()
        
        # 日付カラムとEPS/PERカラムを特定
        # 実際のCSV構造に応じて調整が必要
        date_col = None
        eps_col = None
        per_col = None
        
        for col in df.columns:
            col_lower = col.lower()
            if 'date' in col_lower or '日付' in col or '年月' in col:
                date_col = col
            elif 'eps' in col_lower or '1株当たり利益' in col:
                eps_col = col
            elif 'per' in col_lower or '株価収益率' in col:
                per_col = col
        
        if not date_col:
            print("日経平均CSVに日付カラムが見つかりませんでした")
            return pd.DataFrame()
        
        # データフレームを構築
        result_data = []
        for _, row in df.iterrows():
            try:
                date = pd.to_datetime(row[date_col])
                eps = float(row[eps_col]) if eps_col and pd.notna(row[eps_col]) else None
                per = float(row[per_col]) if per_col and pd.notna(row[per_col]) else None
                
                result_data.append({
                    'date': date,
                    'nikkei_eps': eps,
                    'nikkei_per': per
                })
            except (ValueError, KeyError):
                continue
        
        if not result_data:
            print("日経平均CSVから有効なデータを取得できませんでした")
            return pd.DataFrame()
        
        df_result = pd.DataFrame(result_data)
        df_result.set_index('date', inplace=True)
        df_result.sort_index(inplace=True)
        
        return df_result
        
    except Exception as e:
        print(f"日経平均EPS/PERデータ取得エラー: {e}")
        return pd.DataFrame()


class EPSPERFetcher(BaseFetcher):
    """EPS + PERデータを取得するクラス"""
    
    def __init__(self, market_code: str, symbol: str = None):
        """
        Args:
            market_code: 市場コード（"US" or "JP"）
            symbol: シンボル（使用しない、互換性のため残す）
        """
        super().__init__(market_code)
        self.symbol = symbol
    
    def fetch(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> pd.DataFrame:
        """
        EPS + PERデータを取得
        
        Args:
            start_date: 開始日（使用しない、可能な限り過去から）
            end_date: 終了日（使用しない、今日まで）
        
        Returns:
            DataFrame: EPS + PERデータ
                - index: 日付
                - columns: USの場合は['sp500_per']、JPの場合は['nikkei_eps', 'nikkei_per']
        """
        try:
            if self.market_code == "US":
                # S&P500 PERデータを取得
                df = fetch_sp500_per()
                if df.empty:
                    return pd.DataFrame()
                
                # 期間でフィルタリング
                if start_date:
                    df = df[df.index >= start_date]
                if end_date:
                    df = df[df.index <= end_date]
                
                # 既存のチャートクラスが期待する形式に変換
                # EPSカラムは空（USはPERのみ）
                # PERカラムにsp500_perをマッピング
                df_result = pd.DataFrame(index=df.index)
                df_result['EPS'] = None  # USはEPSデータなし
                df_result['PER'] = df['sp500_per']
                
                # 生データを保存（元の形式で）
                self.save_raw_data(df, "eps_per")
                
                return df_result
                
            elif self.market_code == "JP":
                # 日経平均EPS/PERデータを取得
                df = fetch_nikkei_eps_per()
                if df.empty:
                    return pd.DataFrame()
                
                # 期間でフィルタリング
                if start_date:
                    df = df[df.index >= start_date]
                if end_date:
                    df = df[df.index <= end_date]
                
                # 既存のチャートクラスが期待する形式に変換
                # EPSとPERカラムにマッピング
                df_result = pd.DataFrame(index=df.index)
                df_result['EPS'] = df['nikkei_eps']
                df_result['PER'] = df['nikkei_per']
                
                # 生データを保存（元の形式で）
                self.save_raw_data(df, "eps_per")
                
                return df_result
            else:
                print(f"サポートされていない市場コード: {self.market_code}")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"EPS/PERデータ取得エラー ({self.market_code}): {e}")
            return pd.DataFrame()

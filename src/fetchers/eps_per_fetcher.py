"""
EPS + PERデータ取得（yfinanceのみ使用）
構成銘柄のEPS中央値と市場PERを計算
"""
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple
import requests
from bs4 import BeautifulSoup
import os
import logging
import re
from .base_fetcher import BaseFetcher

# 定数定義
PER_BENCHMARK = 20.0  # PER固定基準線

# ログ設定
def setup_logger(market_code: str) -> logging.Logger:
    """ロガーを設定"""
    log_dir = f"logs/{market_code.lower()}"
    os.makedirs(log_dir, exist_ok=True)
    
    logger = logging.getLogger(f"eps_per_{market_code}")
    logger.setLevel(logging.INFO)
    
    # 既存のハンドラをクリア
    logger.handlers.clear()
    
    # ファイルハンドラ
    for log_file in ["missing_financials.log", "missing_shares.log", "missing_price.log", "excluded_eps.log"]:
        handler = logging.FileHandler(os.path.join(log_dir, log_file), encoding="utf-8")
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger


def get_sp500_symbols() -> List[str]:
    """
    S&P500構成銘柄リストをWikipediaから取得
    
    Returns:
        List[str]: yfinance互換シンボルリスト（例: ['AAPL', 'MSFT', ...]）
    """
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, timeout=30, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'id': 'constituents'})
        
        if not table:
            # フォールバック: 最初のテーブルを探す
            table = soup.find('table')
        
        if not table:
            raise ValueError("S&P500テーブルが見つかりません")
        
        symbols = []
        rows = table.find_all('tr')[1:]  # ヘッダー行をスキップ
        
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) > 0:
                symbol_cell = cells[0]
                symbol = symbol_cell.get_text(strip=True)
                # . を - に変換（yfinance互換）
                symbol = symbol.replace('.', '-')
                if symbol:
                    symbols.append(symbol)
        
        return symbols[:500]  # 最大500銘柄
        
    except Exception as e:
        print(f"S&P500銘柄リスト取得エラー: {e}")
        return []


def get_nikkei225_symbols() -> List[str]:
    """
    日経225構成銘柄リストを取得（Wikipediaから）
    
    Returns:
        List[str]: yfinance互換シンボルリスト（例: ['7203.T', '6758.T', ...]）
    """
    try:
        # Wikipediaから日経225構成銘柄を取得
        url = "https://ja.wikipedia.org/wiki/日経平均株価"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, timeout=30, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 日経225構成銘柄のテーブルを探す
        symbols = []
        
        # テーブルから銘柄コードを抽出
        tables = soup.find_all('table', {'class': 'wikitable'})
        for table in tables:
            rows = table.find_all('tr')
            for row in rows[1:]:  # ヘッダー行をスキップ
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    # 銘柄コード列を探す（通常は最初の列）
                    code_text = cells[0].get_text(strip=True)
                    # 4桁の数字コードを抽出
                    match = re.search(r'(\d{4})', code_text)
                    if match:
                        code = match.group(1)
                        # yfinance用に .T を付与
                        symbols.append(f"{code}.T")
        
        if symbols:
            return symbols[:225]  # 最大225銘柄
        
        # フォールバック: 別のWikipediaページを試す
        url2 = "https://en.wikipedia.org/wiki/Nikkei_225"
        try:
            response2 = requests.get(url2, timeout=30, headers=headers)
            response2.raise_for_status()
            soup2 = BeautifulSoup(response2.text, 'html.parser')
            
            tables2 = soup2.find_all('table')
            for table in tables2:
                rows = table.find_all('tr')
                for row in rows[1:]:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 1:
                        code_text = cells[0].get_text(strip=True)
                        match = re.search(r'(\d{4})', code_text)
                        if match:
                            code = match.group(1)
                            symbol = f"{code}.T"
                            if symbol not in symbols:
                                symbols.append(symbol)
            
            if symbols:
                return symbols[:225]
        except:
            pass
        
        # 最終フォールバック: 主要な日経225銘柄のハードコードリスト
        major_symbols = [
            "7203.T", "6758.T", "6861.T", "9984.T", "6098.T",  # トヨタ、ソニーGHD、キーエンス、ソフトバンクG、リクルート
            "8035.T", "8306.T", "8058.T", "9434.T", "4503.T",  # 東京エレクトロン、三菱UFJ、三菱商事、KDDI、アステラス
            "4063.T", "4519.T", "6367.T", "6501.T", "7267.T",  # 信越化学、中外製薬、ダイキン、日立製作所、ホンダ
            "4901.T", "7741.T", "6981.T", "8801.T", "8411.T",  # 富士フイルム、HOYA、村田製作所、三井不動産、みずほFG
            "4568.T", "6954.T", "7732.T", "3407.T", "4661.T",  # 第一三共、ファナック、トプコン、旭化成、オリエンタルランド
        ]
        
        return major_symbols
        
    except Exception as e:
        print(f"日経225銘柄リスト取得エラー: {e}")
        return []


def fetch_annual_financials(tickers: yf.Tickers, logger: logging.Logger) -> Dict[str, Dict]:
    """
    年次財務データを一括取得
    
    Args:
        tickers: yf.Tickersオブジェクト
        logger: ロガー
    
    Returns:
        Dict[str, Dict]: {symbol: {'net_income': [...], 'shares': [...], 'years': [...]}}
    """
    financials_data = {}
    
    try:
        # 財務情報を取得
        for symbol, ticker in tickers.tickers.items():
            try:
                # 年次財務情報を取得（デフォルトで年次）
                financials = ticker.financials
                balance_sheet = ticker.balance_sheet
                info = ticker.info
                
                if financials is None or financials.empty:
                    logger.info(f"missing_financials: {symbol}")
                    continue
                
                # Net Incomeを取得
                net_income_row = None
                for idx in financials.index:
                    idx_lower = str(idx).lower()
                    if 'net income' in idx_lower or '純利益' in idx_lower or 'netincome' in idx_lower.replace(' ', ''):
                        net_income_row = financials.loc[idx]
                        break
                
                if net_income_row is None:
                    logger.info(f"missing_financials: {symbol} (Net Income not found)")
                    continue
                
                # 年度データを整理
                years = []
                net_incomes = []
                shares_list = []
                
                # 発行済株式数を年次で取得（balance_sheetから）
                shares_row = None
                if balance_sheet is not None and not balance_sheet.empty:
                    for idx in balance_sheet.index:
                        idx_lower = str(idx).lower()
                        if 'shares outstanding' in idx_lower or '発行済株式数' in idx_lower or 'sharesoutstanding' in idx_lower.replace(' ', ''):
                            shares_row = balance_sheet.loc[idx]
                            break
                
                # フォールバック: infoから現在の発行済株式数を取得
                current_shares = info.get('sharesOutstanding') if info else None
                
                for col in financials.columns:
                    year = None
                    net_income = None
                    shares = None
                    
                    # 年を抽出
                    if isinstance(col, datetime):
                        year = col.year
                        net_income = net_income_row[col]
                    elif isinstance(col, str):
                        # 文字列の場合は年を抽出
                        year_match = re.search(r'(\d{4})', col)
                        if year_match:
                            year = int(year_match.group(1))
                            net_income = net_income_row[col]
                    
                    if year is None or pd.isna(net_income):
                        continue
                    
                    # 発行済株式数を取得（年次データがあれば使用、なければ現在値を使用）
                    shares = current_shares  # デフォルトは現在値
                    if shares_row is not None:
                        try:
                            if isinstance(col, datetime):
                                if col in balance_sheet.columns:
                                    shares = shares_row[col]
                            else:
                                # 対応する年の列を探す
                                for bs_col in balance_sheet.columns:
                                    if isinstance(bs_col, datetime) and bs_col.year == year:
                                        shares = shares_row[bs_col]
                                        break
                                    elif isinstance(bs_col, str):
                                        year_match = re.search(r'(\d{4})', str(bs_col))
                                        if year_match and int(year_match.group(1)) == year:
                                            shares = shares_row[bs_col]
                                            break
                        except:
                            pass
                    
                    if shares is None or shares <= 0:
                        continue
                    
                    years.append(year)
                    net_incomes.append(net_income)
                    shares_list.append(shares)
                
                if not years:
                    logger.info(f"missing_financials: {symbol} (No valid years)")
                    continue
                
                financials_data[symbol] = {
                    'net_income': net_incomes,
                    'shares': shares_list,  # 年次ごとの発行済株式数
                    'years': years
                }
                
            except Exception as e:
                logger.info(f"missing_financials: {symbol} (Error: {str(e)})")
                continue
    
    except Exception as e:
        print(f"財務データ取得エラー: {e}")
    
    return financials_data


def calculate_annual_eps(financials_data: Dict[str, Dict], logger: logging.Logger) -> pd.DataFrame:
    """
    年次EPSを計算
    
    Args:
        financials_data: 財務データ
        logger: ロガー
    
    Returns:
        pd.DataFrame: 銘柄別年次EPS（index: 年, columns: 銘柄シンボル）
    """
    eps_data = {}
    
    for symbol, data in financials_data.items():
        try:
            net_incomes = data['net_income']
            shares_list = data['shares']  # 年次ごとの発行済株式数
            years = data['years']
            
            # EPS計算
            eps_list = []
            valid_years = []
            
            for i, net_income in enumerate(net_incomes):
                year = years[i]
                shares = shares_list[i] if i < len(shares_list) else None
                
                # 欠損値チェック
                if pd.isna(net_income) or net_income is None:
                    continue
                
                # 発行済株式数が0以下の場合はスキップ
                if shares is None or shares <= 0:
                    continue
                
                # EPS = Net Income / Shares Outstanding
                eps = net_income / shares
                
                # 異常値チェック（EPSが極端に大きい場合は除外）
                if abs(eps) > 1e10:  # 異常値の閾値
                    logger.info(f"excluded_eps: {symbol} (Year: {year}, EPS: {eps:.2f})")
                    continue
                
                eps_list.append(eps)
                valid_years.append(year)
            
            if eps_list:
                eps_data[symbol] = pd.Series(eps_list, index=valid_years)
        
        except Exception as e:
            logger.info(f"excluded_eps: {symbol} (Error: {str(e)})")
            continue
    
    if not eps_data:
        return pd.DataFrame()
    
    # DataFrameに変換
    df_eps = pd.DataFrame(eps_data)
    df_eps.index.name = 'year'
    
    return df_eps


def calculate_eps_median(df_eps: pd.DataFrame) -> pd.Series:
    """
    EPS中央値を計算（年ごと）
    
    Args:
        df_eps: 銘柄別年次EPS
    
    Returns:
        pd.Series: 年次EPS中央値（index: 年）
    """
    if df_eps.empty:
        return pd.Series(dtype=float)
    
    # 年ごとに中央値を計算
    eps_median = df_eps.median(axis=1)
    eps_median.name = 'eps_median'
    
    return eps_median


def calculate_market_per(eps_median: pd.Series, index_symbol: str, logger: logging.Logger) -> pd.Series:
    """
    市場PERを計算
    
    Args:
        eps_median: EPS中央値（年次）
        index_symbol: 指数シンボル（^GSPC or ^N225）
        logger: ロガー
    
    Returns:
        pd.Series: 市場PER（index: 年）
    """
    if eps_median.empty:
        return pd.Series(dtype=float)
    
    try:
        # 指数の年次終値を取得
        ticker = yf.Ticker(index_symbol)
        hist = ticker.history(period="max")
        
        if hist.empty:
            logger.info(f"missing_price: {index_symbol} (No price data)")
            return pd.Series(dtype=float)
        
        # 各年の年末終値を取得
        year_end_prices = {}
        for year in eps_median.index:
            year_data = hist[hist.index.year == year]
            if not year_data.empty:
                # その年の最後の終値
                year_end_prices[year] = year_data['Close'].iloc[-1]
            else:
                logger.info(f"missing_price: {index_symbol} (Year: {year})")
        
        # 市場PER = 指数価格 / EPS中央値
        market_per = pd.Series(dtype=float, index=eps_median.index)
        for year in eps_median.index:
            if year in year_end_prices and not pd.isna(eps_median[year]) and eps_median[year] != 0:
                market_per[year] = year_end_prices[year] / eps_median[year]
        
        market_per.name = 'market_per'
        return market_per
        
    except Exception as e:
        logger.info(f"missing_price: {index_symbol} (Error: {str(e)})")
        return pd.Series(dtype=float)


def save_eps_data(market_code: str, df_eps: pd.DataFrame, eps_median: pd.Series, market_per: pd.Series):
    """
    EPSデータを保存
    
    Args:
        market_code: 市場コード
        df_eps: 銘柄別EPS
        eps_median: EPS中央値
        market_per: 市場PER
    """
    base_dir = f"data/{market_code.lower()}"
    
    # 銘柄別EPS
    eps_raw_dir = os.path.join(base_dir, "eps_raw")
    os.makedirs(eps_raw_dir, exist_ok=True)
    df_eps.to_csv(os.path.join(eps_raw_dir, "eps_by_stock.csv"), encoding='utf-8-sig')
    
    # EPS中央値
    eps_median_dir = os.path.join(base_dir, "eps_median")
    os.makedirs(eps_median_dir, exist_ok=True)
    eps_median.to_csv(os.path.join(eps_median_dir, "eps_median.csv"), encoding='utf-8-sig', header=True)
    
    # 市場PER
    per_market_dir = os.path.join(base_dir, "per_market")
    os.makedirs(per_market_dir, exist_ok=True)
    market_per.to_csv(os.path.join(per_market_dir, "market_per.csv"), encoding='utf-8-sig', header=True)


class EPSPERFetcher(BaseFetcher):
    """EPS + PERデータを取得するクラス（yfinanceのみ使用）"""
    
    def __init__(self, market_code: str, symbol: str = None):
        """
        Args:
            market_code: 市場コード（"US" or "JP"）
            symbol: 指数シンボル（^GSPC or ^N225）
        """
        super().__init__(market_code)
        self.symbol = symbol
        self.logger = setup_logger(market_code)
    
    def fetch(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> pd.DataFrame:
        """
        EPS + PERデータを取得
        
        Args:
            start_date: 開始日（使用しない、可能な限り過去から）
            end_date: 終了日（使用しない、今日まで）
        
        Returns:
            DataFrame: EPS + PERデータ
                - index: 日付（年次）
                - columns: ['EPS', 'PER']
        """
        try:
            # 銘柄リスト取得
            if self.market_code == "US":
                symbols = get_sp500_symbols()
                index_symbol = "^GSPC"
            elif self.market_code == "JP":
                symbols = get_nikkei225_symbols()
                index_symbol = "^N225"
            else:
                print(f"サポートされていない市場コード: {self.market_code}")
                return pd.DataFrame()
            
            if not symbols:
                print(f"{self.market_code}の銘柄リストが取得できませんでした")
                return pd.DataFrame()
            
            print(f"{self.market_code} 構成銘柄数: {len(symbols)}")
            
            # yfinanceで一括取得
            print(f"財務データを取得中...")
            tickers = yf.Tickers(" ".join(symbols))
            
            # 年次財務データ取得
            financials_data = fetch_annual_financials(tickers, self.logger)
            
            if not financials_data:
                print(f"{self.market_code}の財務データが取得できませんでした")
                return pd.DataFrame()
            
            print(f"取得できた銘柄数: {len(financials_data)}")
            
            # EPS計算
            print(f"EPSを計算中...")
            df_eps = calculate_annual_eps(financials_data, self.logger)
            
            if df_eps.empty:
                print(f"{self.market_code}のEPSデータが計算できませんでした")
                return pd.DataFrame()
            
            # EPS中央値計算
            print(f"EPS中央値を計算中...")
            eps_median = calculate_eps_median(df_eps)
            
            if eps_median.empty:
                print(f"{self.market_code}のEPS中央値が計算できませんでした")
                return pd.DataFrame()
            
            # 市場PER計算
            print(f"市場PERを計算中...")
            market_per = calculate_market_per(eps_median, index_symbol, self.logger)
            
            if market_per.empty:
                print(f"{self.market_code}の市場PERが計算できませんでした")
                return pd.DataFrame()
            
            # データ保存
            save_eps_data(self.market_code, df_eps, eps_median, market_per)
            
            # 既存のチャートクラスが期待する形式に変換
            # indexを日付型に変換（年を日付に変換）
            result_data = []
            for year in eps_median.index:
                if year in market_per.index and not pd.isna(market_per[year]):
                    result_data.append({
                        'date': datetime(year, 12, 31),
                        'EPS': eps_median[year],
                        'PER': market_per[year]
                    })
            
            if not result_data:
                return pd.DataFrame()
            
            df_result = pd.DataFrame(result_data)
            df_result.set_index('date', inplace=True)
            df_result.sort_index(inplace=True)
            
            # 生データを保存（元の形式で）
            self.save_raw_data(df_result, "eps_per")
            
            return df_result
            
        except Exception as e:
            print(f"EPS/PERデータ取得エラー ({self.market_code}): {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()

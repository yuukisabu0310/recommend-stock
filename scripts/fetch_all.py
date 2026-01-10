"""
データ一括取得スクリプト
"""
import sys
import os
import io

# Windowsのコンソールエンコーディング問題を回避
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import yaml
from datetime import datetime, timedelta
from src.fetchers.price_fetcher import PriceFetcher
from src.fetchers.rate_fetcher import RateFetcher
from src.fetchers.cpi_fetcher import CPIFetcher
from src.fetchers.eps_per_fetcher import EPSPERFetcher


def fetch_all_data():
    """すべてのデータを取得"""
    # 設定読み込み
    with open("config/markets.yaml", "r", encoding="utf-8") as f:
        markets_config = yaml.safe_load(f)
    
    markets = markets_config["markets"]
    
    print("データ取得を開始します...")
    
    for market in markets:
        market_code = market["code"]
        market_name = market["name"]
        print(f"\n{market_name} ({market_code}) のデータを取得中...")
        
        # 株価指数
        price_index = market.get("price_index")
        if price_index:
            symbol_config = next(
                (idx for idx in market["indices"] if idx["name"] == price_index),
                None
            )
            if symbol_config:
                symbol = symbol_config["symbol"]
                print(f"  株価指数 ({price_index}): {symbol}")
                try:
                    fetcher = PriceFetcher(market_code, symbol)
                    data = fetcher.fetch()
                    if not data.empty:
                        print(f"    [OK] 取得完了: {len(data)}件")
                    else:
                        print(f"    [NG] データが取得できませんでした")
                except Exception as e:
                    print(f"    [NG] エラー: {e}")
        
        # 政策金利
        print(f"  政策金利")
        try:
            fetcher = RateFetcher(market_code, "policy")
            data = fetcher.fetch()
            if not data.empty:
                print(f"    [OK] 取得完了: {len(data)}件")
            else:
                print(f"    [NG] データが取得できませんでした")
        except Exception as e:
            print(f"    [NG] エラー: {e}")
        
        # 長期金利
        print(f"  長期金利（10年）")
        try:
            fetcher = RateFetcher(market_code, "long_10y")
            data = fetcher.fetch()
            if not data.empty:
                print(f"    [OK] 取得完了: {len(data)}件")
            else:
                print(f"    [NG] データが取得できませんでした")
        except Exception as e:
            print(f"    [NG] エラー: {e}")
        
        # CPI
        print(f"  CPI（消費者物価指数）")
        try:
            fetcher = CPIFetcher(market_code)
            data = fetcher.fetch()
            if not data.empty:
                print(f"    [OK] 取得完了: {len(data)}件")
            else:
                print(f"    [NG] データが取得できませんでした")
        except Exception as e:
            print(f"    [NG] エラー: {e}")
        
        # EPS + PER
        if price_index:
            symbol_config = next(
                (idx for idx in market["indices"] if idx["name"] == price_index),
                None
            )
            if symbol_config:
                symbol = symbol_config["symbol"]
                print(f"  EPS + PER ({price_index})")
                try:
                    fetcher = EPSPERFetcher(market_code, symbol)
                    data = fetcher.fetch()
                    if not data.empty:
                        print(f"    [OK] 取得完了: {len(data)}件")
                    else:
                        print(f"    [NG] データが取得できませんでした")
                except Exception as e:
                    print(f"    [NG] エラー: {e}")
    
    print("\nデータ取得が完了しました。")


if __name__ == "__main__":
    fetch_all_data()


"""
データ検証スクリプト
"""
import sys
import os
import io

# Windowsのコンソールエンコーディング問題を回避
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import os
import pandas as pd
from src.processors.validator import DataValidator


def validate_data():
    """データの妥当性をチェック"""
    print("データ検証を開始します...")
    
    markets = ["us", "jp"]
    data_types = ["price", "policy_rate", "long_rate_10y", "cpi_yoy", "eps_per"]
    
    for market in markets:
        print(f"\n{market.upper()} のデータを検証中...")
        
        raw_dir = f"data/raw/{market}"
        if not os.path.exists(raw_dir):
            print(f"  [NG] ディレクトリが存在しません: {raw_dir}")
            continue
        
        for data_type in data_types:
            filepath = os.path.join(raw_dir, f"{data_type}.csv")
            
            if not os.path.exists(filepath):
                print(f"  [NG] {data_type}: ファイルが存在しません")
                continue
            
            try:
                df = pd.read_csv(filepath, index_col=0, parse_dates=True)
                
                validator = DataValidator()
                
                if not validator.is_valid(df):
                    print(f"  [NG] {data_type}: データが無効です")
                    continue
                
                missing_info = validator.check_missing_values(df)
                date_range = validator.check_date_range(df)
                
                print(f"  [OK] {data_type}:")
                print(f"    - データポイント数: {len(df)}")
                print(f"    - 日付範囲: {date_range[0]} ～ {date_range[1]}")
                
                if missing_info:
                    for col, info in missing_info.items():
                        if info['count'] > 0:
                            print(f"    - {col}: 欠損値 {info['count']}件 ({info['rate']:.1f}%)")
                
            except Exception as e:
                print(f"  [NG] {data_type}: エラー - {e}")
    
    print("\nデータ検証が完了しました。")


if __name__ == "__main__":
    validate_data()


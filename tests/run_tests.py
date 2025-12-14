"""
簡単なテスト実行スクリプト
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backtest import run_backtest

if __name__ == "__main__":
    success = run_backtest()
    sys.exit(0 if success else 1)


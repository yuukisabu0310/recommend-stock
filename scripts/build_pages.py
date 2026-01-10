"""
ページ生成スクリプト
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
from src.pages.us_short import USShortPage
from src.pages.us_medium import USMediumPage
from src.pages.us_long import USLongPage
from src.pages.jp_short import JPShortPage
from src.pages.jp_medium import JPMediumPage
from src.pages.jp_long import JPLongPage
from src.renderer.html_generator import HTMLGenerator


def build_all_pages():
    """すべてのページを生成"""
    # 出力ディレクトリ作成
    os.makedirs("public/logs", exist_ok=True)
    
    pages = [
        ("US", "short", USShortPage()),
        ("US", "medium", USMediumPage()),
        ("US", "long", USLongPage()),
        ("JP", "short", JPShortPage()),
        ("JP", "medium", JPMediumPage()),
        ("JP", "long", JPLongPage()),
    ]
    
    print("ページ生成を開始します...")
    
    for market_code, timeframe_code, page in pages:
        print(f"\n{market_code}-{timeframe_code} ページを生成中...")
        try:
            page_data = page.build()
            html = HTMLGenerator.generate_page_html(page_data)
            
            filename = f"public/logs/{market_code}-{timeframe_code}.html"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(html)
            
            print(f"  [OK] 生成完了: {filename}")
        except Exception as e:
            print(f"  [NG] エラー: {e}")
            import traceback
            traceback.print_exc()
    
    # インデックスページ生成
    print("\nインデックスページを生成中...")
    try:
        index_html = HTMLGenerator.generate_index_html()
        with open("public/index.html", "w", encoding="utf-8") as f:
            f.write(index_html)
        print("  [OK] 生成完了: public/index.html")
    except Exception as e:
        print(f"  [NG] エラー: {e}")
        import traceback
        traceback.print_exc()
    
    print("\nページ生成が完了しました。")


if __name__ == "__main__":
    build_all_pages()


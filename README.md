# v2 Market Report

## 目的（最重要）

本プロジェクトは「予測・スコア化・断定」を行わない。  
**実データ（Fact）を正確に取得・可視化し、人が判断できる材料を提供すること**を唯一の目的とする。

- 天井・底の断定は禁止
- 「可能性が高い」「買い」などの主観表現は禁止
- 数値・推移・方向・勢いなど **事実のみを表示**
- 解釈（Interpretation）と売買判断（Decision）は将来層として完全分離

## 技術構成

- **Python 3.11+**: データ取得・分析
- **yfinance**: 株価データ取得（Yahoo Finance、無料）
- **FRED API**: 米国・日本の経済指標取得（無料、APIキー必要）
- **GitHub Actions**: 定期実行・自動デプロイ（将来実装）
- **GitHub Pages**: HTML静的表示（将来実装）

## セットアップ

### 1. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定

`.env` ファイルを作成して以下を設定：

```bash
FRED_API_KEY=your_fred_api_key  # 必須（FRED APIキーを取得してください）
```

**FRED APIキーの取得方法**:
- [FRED API Key](https://fred.stlouisfed.org/docs/api/api_key.html) にアクセス
- アカウントを作成（無料）
- API Keys セクションでAPIキーを生成

### 3. データ取得

```bash
python scripts/fetch_all.py
```

### 4. ページ生成

```bash
python scripts/build_pages.py
```

実行結果は `public/` ディレクトリに HTML ファイルとして出力されます。

## プロジェクト構造

```
recommend-stock-v2/
├─ README.md
├─ config/              # 設定ファイル（市場・期間・指標定義）
├─ data/                # データ保存先
│   ├─ raw/            # APIから取得した生データ
│   └─ processed/      # 表示用に整形した時系列データ
├─ src/                 # ソースコード
│   ├─ fetchers/       # データ取得層
│   ├─ processors/     # データ加工層
│   ├─ facts/          # Fact層（事実の構造化）
│   ├─ interpretations/# Interpretation層（文章要約のみ）
│   ├─ decisions/      # Decision層（将来用・今は空）
│   ├─ charts/         # チャート生成専用
│   ├─ pages/          # ページ単位の組み立て
│   └─ renderer/       # HTML生成のみ
├─ public/              # 出力HTMLファイル
└─ scripts/             # 実行スクリプト
```

## 免責事項

**本アプリは研究用途であり、投資助言や売買指示を目的としたものではありません。**

- 投資判断はユーザーの自己責任
- 過去の実績は将来を保証しない
- 売買を断定する表現は禁止
- 実データのみを表示し、判断材料を提供する

## ライセンス

MIT License


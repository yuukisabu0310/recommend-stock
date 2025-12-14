# 株式市場分析・銘柄選定アプリ

株初心者〜中級者向けの市場環境分析・銘柄選定アプリです。GitHub Actions + Python + GitHub Pages を使用して、定期的に市場分析レポートを自動生成します。

## 機能

- **Market Direction Overview**: 国別（米国・日本・中国）× 期間（短期/中期/長期）ごとの市場方向感を5段階で表示
- **国別市場判断**: 各国の短期・中期・長期の市場環境を分析（結論・前提・リスク・転換シグナル）
- **注目セクター**: マクロ・地政学・政策を元に注目セクターを提示
- **おすすめ銘柄**: 日本株・米国株の推奨銘柄を提示（投資助言ではありません）
- **思考ログ**: 判断に至ったプロセスを記録

## 技術構成

- **Python 3.11+**: データ取得・分析
- **yfinance**: 株価データ取得（Yahoo Finance、無料）
- **Groq API**: 市場方向感の分析・評価（LLM: `llama-3.1-70b-versatile`）
- **GitHub Actions**: 定期実行・自動デプロイ
- **GitHub Pages**: HTML静的表示

**重要なポイント**: 
- **Groq APIキーが必要です**（`GROQ_API_KEY`環境変数）
- LLMは市場方向感の総合判断を担当（データ取得・計算はPython側で実施）
- ルールベース分析も併用（思考ログに表示）

## セットアップ

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd recommend-stock
```

### 2. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 3. 環境変数の設定

`.env` ファイルを作成して以下を設定：

```bash
GROQ_API_KEY=your_groq_api_key  # 必須（Groq APIキーを取得してください）
```

または、GitHub Actions を使用する場合は、リポジトリの Secrets に `GROQ_API_KEY` を設定してください。

**Groq APIキーの取得方法**:
1. [Groq Console](https://console.groq.com/) にアクセス
2. アカウントを作成（無料）
3. API Keys セクションでAPIキーを生成
4. 環境変数またはGitHub Secretsに設定

### 4. 設定ファイルの確認

`config/config.yml` で以下を設定可能です：

- 対象国・指数
- 投資期間の定義
- おすすめ銘柄件数
- AI設定（ON/OFF、プロンプト等）
- イベント検知条件

## 実行方法

### ローカル実行

```bash
python src/main.py
```

実行結果は `docs/` ディレクトリに HTML ファイルとして出力されます。

### GitHub Actions での自動実行

1. `.github/workflows/market-analysis.yml` が自動実行されます
2. デフォルトでは毎日日本時間 18:00 に実行
3. `workflow_dispatch` で手動実行も可能
4. 結果は GitHub Pages に自動デプロイされます

## 出力ファイル

実行結果は `docs/` ディレクトリに出力され、GitHub Pages で閲覧可能です：

- `docs/index.html`: メインレポート（モダンなデザイン、カード形式、視覚的にわかりやすい）
- `docs/details/{country}-{timeframe}.html`: 国別・期間別詳細ページ
- `docs/logs/{country}-{timeframe}.html`: 思考ログ

内部データ（JSON形式）は `outputs/` ディレクトリに保存されます：
- `outputs/market_data.json`: 取得した市場データ
- `outputs/analysis_result.json`: 分析結果（JSON）
- `outputs/fallback/`: API失敗時用のフォールバックデータ

## 設定について

すべての設定は `config/config.yml` で管理されます：

### 対象国

```yaml
countries:
  - name: "米国"
    code: "US"
    indices: ["SPX", "NDX"]
    universe: ["S&P500", "NASDAQ100"]
```

### 投資期間

```yaml
timeframes:
  - name: "短期"
    code: "short"
    days: 30
    weights:
      technical: 0.5
      macro: 0.3
```

### スコア範囲

- `+2`: ↗↗ 超強気
- `+1`: ↗ やや強気
- `0`: → 中立
- `-1`: ↘ やや弱気
- `-2`: ↘↘ 超弱気

## 免責事項

**本アプリは研究用途であり、投資助言や売買指示を目的としたものではありません。**

- 投資判断は自己責任で行ってください
- 過去の実績は将来の結果を保証するものではありません
- 断定的表現は避けており、必ず「前提・リスク・転換シグナル」を明示しています

## ライセンス

MIT License

## 貢献

プルリクエストや Issue を歓迎します。ただし、投資助言や売買指示を含む内容は禁止です。


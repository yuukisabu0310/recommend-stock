# セットアップガイド

## 前提条件

- Python 3.11 以上
- Git
- GitHub アカウント（GitHub Actions を使用する場合）

**注意**: OpenAI API キーは不要です（デフォルトではLLM機能を使用しません）

## ローカル環境でのセットアップ

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd recommend-stock
```

### 2. 仮想環境の作成（推奨）

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 4. 環境変数の設定（オプション）

**デフォルトでは環境変数の設定は不要です。**

LLM機能を使用したい場合のみ、`.env` ファイルを作成：

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### 5. 実行

```bash
python src/main.py
```

実行結果は `docs/` ディレクトリに Markdown ファイルとして出力されます。

## GitHub Actions でのセットアップ

### 1. リポジトリの作成

GitHub で新しいリポジトリを作成し、コードをプッシュします。

### 2. GitHub Secrets の設定（オプション）

**デフォルトではSecretsの設定は不要です。**

LLM機能を使用したい場合のみ、リポジトリの Settings > Secrets and variables > Actions で以下を設定：

- `OPENAI_API_KEY`: OpenAI API キー（LLM機能を使用する場合のみ）
- `VUMDFM5V1EKSNGNU`: （オプション）Alpha Vantage API キー

### 3. GitHub Pages の有効化

1. Settings > Pages に移動
2. Source を "GitHub Actions" に設定

### 4. ワークフローの確認

`.github/workflows/market-analysis.yml` が正しく設定されているか確認します。

デフォルトでは：
- 毎日日本時間 18:00（UTC 9:00）に自動実行
- `workflow_dispatch` で手動実行も可能
- `main` ブランチにプッシュ時にも実行

### 5. 初回実行

Actions タブからワークフローを手動実行して動作確認します。

## トラブルシューティング

### API キーエラー（LLM機能を使用する場合のみ）

- LLM機能はデフォルトで無効化されているため、APIキーは不要です
- LLM機能を使用する場合のみ、`.env` ファイルまたはGitHub Secretsが正しく設定されているか確認

### データ取得エラー

- Yahoo Finance API の制限に達している可能性があります
- フォールバックデータが使用されます（`outputs/fallback/`）

### LLM 機能について

- **デフォルトではLLM機能は無効化されています**（これが推奨です）
- テンプレートベースの分析で十分に機能します
- LLM機能を使用したい場合のみ：
  - OpenAI API キーが正しく設定されているか確認
  - `config/config.yml` で `ai.enabled: true` になっているか確認
  - API の使用量制限に達していないか確認

## カスタマイズ

### 設定の変更

`config/config.yml` で以下をカスタマイズできます：

- 対象国・指数
- 投資期間の定義
- おすすめ銘柄件数
- AI設定（プロンプト等）
- イベント検知条件

変更後、GitHub Actions で自動実行されるか、ローカルで再実行してください。


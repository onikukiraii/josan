# FastAPI App Template

FastAPI + HTMX で作る Web アプリケーションのテンプレート

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, Alembic
- **Database**: MySQL 8.0, OpenSearch
- **Frontend**: HTMX
- **Tools**: uv, mise, Ruff, mypy

## Requirements

- [mise](https://mise.jdx.dev/) (Python, uv のバージョン管理 & タスクランナー)
- [Docker](https://www.docker.com/) & Docker Compose

## Quick Start

### 1. mise のインストール

```bash
# macOS (Homebrew)
brew install mise
```

### 2. リポジトリをクローン

```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>
```

### 3. ツールのインストール

```bash
mise install
```

これで Python 3.14 と uv がインストールされます。

### 4. 環境変数の設定

```bash
cp .env.template .env
```

必要に応じて `.env` を編集してください。

### 5. Docker Compose で起動

```bash
docker compose up -d
```

以下のサービスが起動します:
- **API**: http://localhost:8000
- **MySQL**: localhost:3309
- **OpenSearch**: localhost:9205

### 6. マイグレーション実行

```bash
mise run migrate
```

## Development

### ローカル開発（Docker なし）

```bash
mise run dev
```

※ MySQL と OpenSearch は別途起動が必要です。

### コマンド一覧

```bash
mise tasks  # 利用可能なタスク一覧を表示
```

| コマンド | 説明 |
|---------|------|
| `mise run migrate` | マイグレーション実行 |
| `mise run migrate-gen message="add users table"` | マイグレーションファイル生成 |
| `mise run lint` | Lint チェック (Ruff + mypy) |
| `mise run format` | コードフォーマット |
| `mise run dev` | 開発サーバー起動 |

### ディレクトリ構成

```
.
├── backend/
│   ├── alembic/        # マイグレーション
│   ├── db/             # DB接続設定
│   ├── docker/         # Dockerfile
│   ├── entity/         # SQLAlchemy モデル
│   ├── routers/        # APIルーター
│   ├── params/         # リクエストパラメータ
│   ├── response/       # レスポンススキーマ
│   └── main.py         # エントリーポイント
├── compose.yaml
├── mise.toml           # ツール & タスク定義
└── .env.template
```

## License

MIT

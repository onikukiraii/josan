# Josan - 産婦人科シフト管理アプリ

## プロジェクト構成

- `backend/` - FastAPI (Python 3.14, SQLAlchemy, Alembic)
- `frontend/` - React 19 + TypeScript + Vite + Tailwind CSS v4
- `docs/` - 仕様書

## 開発コマンド

```bash
mise install              # Python, uv のセットアップ
docker compose up -d      # 全サービス起動 (API:8000, Frontend:5173, MySQL:3309)
mise run migrate          # マイグレーション実行
mise run migrate-gen message="xxx"  # マイグレーション生成
mise run lint             # Ruff + mypy
mise run format           # Ruff フォーマット
mise run dev              # バックエンド開発サーバー
```

## コミット規約

`/commit` スキルを使用すること。

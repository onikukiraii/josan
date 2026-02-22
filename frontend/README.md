# Frontend

React + TypeScript + Vite + Tailwind CSS で構築されたフロントエンドアプリケーション。

## Tech Stack

- **React** 19
- **TypeScript**
- **Vite** (ビルドツール / 開発サーバー)
- **Tailwind CSS** v4
- **openapi-typescript** / **openapi-fetch** (API 型生成 & 型安全クライアント)

## ディレクトリ構成

```
frontend/
├── docker/
│   └── Dockerfile
├── public/
├── src/
│   ├── api/
│   │   ├── client.ts    # openapi-fetch クライアント
│   │   └── schema.d.ts  # 自動生成された型定義
│   ├── assets/
│   ├── App.tsx          # ルートコンポーネント
│   ├── main.tsx         # エントリーポイント
│   └── index.css        # Tailwind CSS インポート
├── index.html
├── vite.config.ts
├── tsconfig.json
└── package.json
```

## 開発

### Docker で起動（推奨）

プロジェクトルートで:

```bash
docker compose up frontend
```

http://localhost:5173 でアクセスできます。ホットリロード対応です。

### ローカルで起動

```bash
cd frontend
npm install
npm run dev
```

## ビルド

```bash
npm run build
```

`dist/` ディレクトリに出力されます。

## API 型生成

API サーバーが起動している状態で:

```bash
npm run generate-api
```

`src/api/schema.d.ts` に OpenAPI スキーマから TypeScript 型定義が生成されます。

```tsx
import { api } from "./api/client";

const { data, error } = await api.GET("/users/");
// data は自動的に型推論される
```

## Lint

```bash
npm run lint
```

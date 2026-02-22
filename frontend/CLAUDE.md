# Frontend

React 19 + TypeScript 5.9 + Vite 7 + Tailwind CSS v4

## コマンド

```bash
npm run dev       # 開発サーバー (localhost:5173)
npm run build     # tsc + vite build
npm run lint      # eslint
```

## API 型生成

```bash
npm run generate-api  # OpenAPI スキーマから TypeScript 型を生成
```

- `src/api/schema.d.ts` - openapi-typescript が生成する型定義（自動生成）
- `src/api/client.ts` - openapi-fetch を使った型安全な API クライアント
- API サーバー起動中に実行すること（`docker compose up api`）

### 使い方

```ts
import { api } from "./api/client";
const { data, error } = await api.GET("/endpoint");
```

## コード規約

- ESLint + react-hooks + react-refresh プラグイン
- Tailwind CSS v4 (@tailwindcss/vite プラグイン)

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

- `src/api/schema.d.ts` - openapi-typescript が生成する型定義（自動生成・編集不可）
- `src/api/constants.ts` - schema.d.ts からの型エイリアス re-export + ラベルマップ
- `src/api/fetcher.ts` - openapi-fetch を使った型安全な API クライアント
- API サーバー起動中に実行すること（`docker compose up api`）

### 使い方

```ts
// 型・ラベルのインポート
import type { MemberResponse, Qualification } from '@/api/constants'
import { QUALIFICATION_LABEL } from '@/api/constants'

// API 呼び出し
import { membersApi } from '@/api/fetcher'
const members = await membersApi.list()
```

## コード規約

- ESLint + react-hooks + react-refresh プラグイン
- Tailwind CSS v4 (@tailwindcss/vite プラグイン)

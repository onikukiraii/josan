# 新しいモデルを作成する手順

例として `Product` モデルを作成する場合の手順。

## 1. エンティティを作成

`entity/product.py` を作成:

```python
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String

from entity.base import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    price = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
```

## 2. entity/__init__.py にエクスポートを追加

```python
from entity.base import Base
from entity.product import Product  # 追加
from entity.user import User

__all__ = ["Base", "Product", "User"]  # 追加
```

## 3. マイグレーションファイルを生成

```bash
make migrate-gen
# Migration message: add products table
```

## 4. マイグレーションを実行

```bash
make migrate
```

## 確認

マイグレーション後、MySQLでテーブルが作成されていることを確認:

```bash
docker compose exec db mysql -uroot -ppassword mydatabase -e "SHOW TABLES;"
```

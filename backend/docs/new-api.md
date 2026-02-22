# 新しいAPIを作成する手順

例として `Product` のCRUD APIを作成する場合の手順。

前提: [新しいモデルを作成する手順](./new-model.md) でモデルが作成済みであること。

## 1. リクエストパラメータを作成

`params/product.py` を作成:

```python
from pydantic import BaseModel


class ProductCreateParams(BaseModel):
    name: str
    price: int
```

## 2. レスポンススキーマを作成

`response/product.py` を作成:

```python
from datetime import datetime

from pydantic import BaseModel


class ProductResponse(BaseModel):
    id: int
    name: str
    price: int
    created_at: datetime

    model_config = {"from_attributes": True}
```

`model_config = {"from_attributes": True}` はSQLAlchemyモデルからPydanticモデルへの変換を有効にする。

## 3. ルーターを作成

`routers/product.py` を作成:

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.session import get_db
from entity.product import Product
from params.product import ProductCreateParams
from response.product import ProductResponse

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=list[ProductResponse])
def get_products(db: Session = Depends(get_db)):
    return db.query(Product).all()


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("/", response_model=ProductResponse)
def create_product(params: ProductCreateParams, db: Session = Depends(get_db)):
    product = Product(name=params.name, price=params.price)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product
```

## 4. main.py にルーターを登録

```python
from fastapi import FastAPI

from routers.product import router as product_router  # 追加
from routers.user import router as user_router

app = FastAPI()
app.include_router(product_router)  # 追加
app.include_router(user_router)
```

## 確認

サーバー起動後、以下で確認:

- Swagger UI: http://localhost:8000/docs
- 一覧取得: `curl http://localhost:8000/products/`
- 作成: `curl -X POST http://localhost:8000/products/ -H "Content-Type: application/json" -d '{"name": "Test", "price": 100}'`

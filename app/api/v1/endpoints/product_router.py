from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.product_schema import ProductResponse, ProductCreate, ProductUpdate
from app.services.product_service import ProductService
from app.dependencies.auth import get_admin_user

router = APIRouter()

@router.get("/", response_model=List[ProductResponse])
def list_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    service = ProductService(db)
    return service.get_all(skip=skip, limit=limit)

@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    obj_in: ProductCreate,
    db: Session = Depends(get_db),
    admin_user = Depends(get_admin_user)
):
    service = ProductService(db)
    return service.create(obj_in)

@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    obj_in: ProductUpdate,
    db: Session = Depends(get_db),
    admin_user = Depends(get_admin_user)
):
    service = ProductService(db)
    updated_prod = service.update(product_id=product_id, obj_in=obj_in)
    if not updated_prod:
        raise HTTPException(status_code=404, detail="Product not found")
    return updated_prod
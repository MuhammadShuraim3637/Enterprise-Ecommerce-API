from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.dependencies.auth import get_admin_user
from app.schemas.category_schema import CategoryResponse, CategoryCreate, CategoryUpdate
from app.services.category_service import CategoryService

router = APIRouter()

@router.get("/", response_model=List[CategoryResponse])
def list_categories(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Har koi categories dekh sakta hai"""
    service = CategoryService(db)
    return service.get_all(skip=skip, limit=limit)

@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    obj_in: CategoryCreate, 
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """Sirf Admin category create kar sakta hai"""
    service = CategoryService(db)
    return service.create(obj_in)

@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    obj_in: CategoryUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """Sirf Admin category update kar sakta hai"""
    service = CategoryService(db)
    updated_cat = service.update(category_id=category_id, obj_in=obj_in)
    if not updated_cat:
        raise HTTPException(status_code=404, detail="Category not found")
    return updated_cat
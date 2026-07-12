from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.review_schema import ReviewResponse, ReviewCreate
from app.services.review_service import ReviewService
from app.dependencies.auth import get_current_user  # Changed from get_current_active_user
from app.services.product_service import ProductService

router = APIRouter()

@router.post("/", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def create_review(
    obj_in: ReviewCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)  # Updated dependency here
):
    # Check current product existence first
    product_service = ProductService(db)
    if not product_service.get_by_id(obj_in.product_id):
        raise HTTPException(status_code=404, detail="Product not found")

    review_service = ReviewService(db)
    return review_service.create(obj_in, user_id=current_user.id)

@router.get("/product/{product_id}", response_model=List[ReviewResponse])
def get_product_reviews(product_id: int, skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    review_service = ReviewService(db)
    return review_service.get_by_product(product_id=product_id, skip=skip, limit=limit)
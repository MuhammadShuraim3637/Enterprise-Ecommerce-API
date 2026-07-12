from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.dependencies.auth import get_current_user # Aapki auth dependency
from app.schemas.user import UserResponse # Aapka user response schema
from app.schemas.cart_schema import CartItemCreate, CartItemUpdate, CartItemResponse, CartSummaryResponse
from app.services.cart_service import CartService

router = APIRouter(prefix="/cart", tags=["Cart"])

@router.get("/", response_model=CartSummaryResponse)
def get_cart(db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    return CartService.get_user_cart(db, current_user.id)

@router.post("/", response_model=CartItemResponse, status_code=status.HTTP_201_CREATED)
def add_item_to_cart(
    cart_data: CartItemCreate, 
    db: Session = Depends(get_db), 
    current_user: UserResponse = Depends(get_current_user)
):
    return CartService.add_to_cart(db, current_user.id, cart_data)

@router.put("/{item_id}", response_model=CartItemResponse)
def update_item_quantity(
    item_id: int, 
    update_data: CartItemUpdate, 
    db: Session = Depends(get_db), 
    current_user: UserResponse = Depends(get_current_user)
):
    return CartService.update_cart_item(db, current_user.id, item_id, update_data)

@router.delete("/{item_id}")
def remove_item(
    item_id: int, 
    db: Session = Depends(get_db), 
    current_user: UserResponse = Depends(get_current_user)
):
    return CartService.remove_from_cart(db, current_user.id, item_id)

@router.delete("/clear/all")
def clear_user_cart(db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    return CartService.clear_cart(db, current_user.id)
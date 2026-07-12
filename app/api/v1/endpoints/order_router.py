from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.order_schema import OrderCreate, OrderResponse, OrderStatusUpdate
from app.services.order_service import OrderService
from app.dependencies.auth import get_current_user

router = APIRouter()

@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(obj_in: OrderCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    order_service = OrderService(db)
    return order_service.create_order(obj_in, user_id=current_user.id)

@router.get("/my-orders", response_model=List[OrderResponse])
def get_my_orders(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    order_service = OrderService(db)
    return order_service.get_user_orders(user_id=current_user.id)

@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    order_service = OrderService(db)
    order = order_service.get_order_by_id(order_id)
    
    # FIXED: is_admin ki jagah is_superuser check kiya hai
    if not current_user.is_superuser and order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this order")
    return order

@router.get("/", response_model=List[OrderResponse])
def get_all_orders_admin(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    # FIXED: is_admin ki jagah is_superuser check kiya hai
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin permissions required")
    order_service = OrderService(db)
    return order_service.get_all_orders()

@router.patch("/{order_id}/status", response_model=OrderResponse)
def update_order_status_admin(
    order_id: int, 
    obj_in: OrderStatusUpdate, 
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_user)
):
    # FIXED: is_admin ki jagah is_superuser check kiya hai
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin permissions required")
    order_service = OrderService(db)
    return order_service.update_order_status(order_id, obj_in)
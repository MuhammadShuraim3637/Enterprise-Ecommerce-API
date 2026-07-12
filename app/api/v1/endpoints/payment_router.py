from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.payment_schema import PaymentCreate, PaymentResponse
from app.services.payment_service import PaymentService

router = APIRouter()

@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def checkout_and_pay(
    payload: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    payment_service = PaymentService(db)
    return payment_service.process_order_payment(payload, user_id=current_user.id)

@router.get("/order/{order_id}", response_model=PaymentResponse)
def get_payment_by_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    payment_service = PaymentService(db)
    # Admin ko sab payments dekh sakte hain, user apni hi dekh sakte hain
    return payment_service.get_payment_details(order_id, user_id=current_user.id, is_admin=current_user.is_superuser)
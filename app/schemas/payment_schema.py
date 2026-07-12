from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from decimal import Decimal
from app.models.payment import PaymentStatus

class PaymentCreate(BaseModel):
    order_id: int
    card_number: str  # Dummy validations ke liye
    cvv: str
    expiry_date: str

class PaymentResponse(BaseModel):
    id: int
    order_id: int
    transaction_id: Optional[str]
    amount: Decimal
    status: str
    provider: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
from pydantic import BaseModel, ConfigDict
from typing import List
from datetime import datetime
from app.models.order import OrderStatus

# Order Item Schemas
class OrderItemBase(BaseModel):
    product_id: int
    quantity: int

class OrderItemResponse(OrderItemBase):
    id: int
    price: float

    model_config = ConfigDict(from_attributes=True)

# Order Schemas
class OrderCreate(BaseModel):
    shipping_address: str
    items: List[OrderItemBase]

class OrderStatusUpdate(BaseModel):
    status: OrderStatus

class OrderResponse(BaseModel):
    id: int
    user_id: int
    total_price: float
    status: str
    shipping_address: str
    created_at: datetime
    items: List[OrderItemResponse]

    model_config = ConfigDict(from_attributes=True)
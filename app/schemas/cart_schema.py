from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional
from app.schemas.product_schema import ProductResponse # Aapka product response schema

class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1, description="Quantity kam se kam 1 honi chahiye")

class CartItemUpdate(BaseModel):
    quantity: int = Field(..., ge=1, description="Quantity kam se kam 1 honi chahiye")

class CartItemResponse(BaseModel):
    id: int
    user_id: int
    product_id: int
    quantity: int
    created_at: datetime
    product: Optional[ProductResponse] = None

    model_config = ConfigDict(from_attributes=True)

class CartSummaryResponse(BaseModel):
    items: list[CartItemResponse]
    total_items: int
    total_price: float
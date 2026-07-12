from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class CategoryBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=255)

class CategoryCreate(CategoryBase):
    pass  # Name aur description creation ke waqt chahiye

class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None

class CategoryResponse(CategoryBase):
    id: int
    slug: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
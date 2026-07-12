from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class ReviewBase(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Rating must be between 1 and 5 stars")
    comment: Optional[str] = Field(None, max_length=500)

class ReviewCreate(ReviewBase):
    product_id: int

class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=500)

class UserReviewResponse(BaseModel):
    id: int
    full_name: str

    model_config = ConfigDict(from_attributes=True)

class ReviewResponse(ReviewBase):
    id: int
    product_id: int
    user_id: int
    created_at: datetime
    user: UserReviewResponse

    model_config = ConfigDict(from_attributes=True)
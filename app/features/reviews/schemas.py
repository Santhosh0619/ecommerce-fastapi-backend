from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional
from datetime import datetime
from app.features.reviews.models import ReviewStatus

class ReviewBase(BaseModel):
    product_id: int
    rating: float = Field(..., ge=0.5, le=5.0)
    review_comment: Optional[str] = Field(None, max_length=1000)

    @field_validator('rating')
    @classmethod
    def validate_rating_increment(cls, v: float) -> float:
        if (v * 2) % 1 != 0:
            raise ValueError('Rating must be in increments of 0.5 (e.g. 0.5, 1.0, 1.5, ..., 5.0)')
        return v

class ReviewCreate(ReviewBase):
    order_id: Optional[int] = None

class ReviewUpdate(BaseModel):
    rating: Optional[float] = Field(None, ge=0.5, le=5.0)
    review_comment: Optional[str] = Field(None, max_length=1000)

    @field_validator('rating')
    @classmethod
    def validate_rating_increment(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and (v * 2) % 1 != 0:
            raise ValueError('Rating must be in increments of 0.5 (e.g. 0.5, 1.0, 1.5, ..., 5.0)')
        return v

class ReviewResponse(BaseModel):
    review_id: int
    product_id: int
    user_id: int
    order_id: int
    rating: float
    review_comment: Optional[str] = None
    is_edited: bool
    helpful_votes: int
    vendor_reply: Optional[str] = None
    vendor_reply_at: Optional[datetime] = None
    review_status: ReviewStatus
    created_at: datetime
    updated_at: datetime
    user_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class VendorReplyCreate(BaseModel):
    vendor_reply: str = Field(..., min_length=1, max_length=1000)

class AdminStatusUpdate(BaseModel):
    status: ReviewStatus

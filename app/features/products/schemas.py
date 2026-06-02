from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional, Literal
from datetime import datetime

class ProductImageBase(BaseModel):
    image_url: str
    is_primary: bool = False

class ProductImageResponse(ProductImageBase):
    product_image_id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ProductBase(BaseModel):
    product_name: str = Field(..., min_length=2, max_length=200)
    product_description: str = Field(..., min_length=10)
    product_price: float = Field(..., gt=0)
    product_stock: int = Field(..., ge=0)
    category_id: int

class ProductCreate(ProductBase):
    # Vendor submits this. Status defaults to Active unless specified.
    product_status: Literal['Active', 'Inactive'] = 'Active'

class ProductUpdate(BaseModel):
    product_name: Optional[str] = Field(None, min_length=2, max_length=200)
    product_description: Optional[str] = Field(None, min_length=10)
    product_price: Optional[float] = Field(None, gt=0)
    product_stock: Optional[int] = Field(None, ge=0)
    category_id: Optional[int] = None
    product_status: Optional[Literal['Active', 'Inactive', 'Archived']] = None
    is_featured: Optional[bool] = None

class ProductResponse(ProductBase):
    product_id: int
    vendor_id: int
    product_slug: str
    product_status: str
    is_featured: bool
    average_rating: float
    review_count: int
    created_at: datetime
    updated_at: datetime
    
    images: list[ProductImageResponse] = []
    
    model_config = ConfigDict(from_attributes=True)

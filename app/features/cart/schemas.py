from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0, description="Quantity must be greater than 0")

class CartItemUpdate(BaseModel):
    quantity: Optional[int] = Field(None, gt=0, description="Quantity must be greater than 0")
    is_selected: Optional[bool] = None

class CartItemResponse(BaseModel):
    cart_item_id: int
    cart_id: int
    product_id: int
    quantity: int
    is_selected: bool
    created_at: datetime
    updated_at: datetime
    
    # Extended fields from joined load
    product_name: str
    product_price: float
    product_stock: int
    product_slug: str
    primary_image_url: Optional[str] = None
    stock_warning: Optional[bool] = False
    product_unavailable: Optional[bool] = False

    class Config:
        from_attributes = True

class CartResponse(BaseModel):
    cart_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    items: List[CartItemResponse]
    selected_item_count: int
    selected_subtotal: float

    class Config:
        from_attributes = True

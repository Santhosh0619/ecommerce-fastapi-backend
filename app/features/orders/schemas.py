from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import Literal, Optional, List
from datetime import datetime, date
from decimal import Decimal

class OrderCreateRequest(BaseModel):
    checkout_type: Literal["cart", "buy_now"] = Field(..., description="Type of checkout: from cart or immediate purchase")
    address_id: int = Field(..., description="ID of the delivery address")
    product_id: Optional[int] = Field(None, description="Required if checkout_type is buy_now")
    quantity: Optional[int] = Field(None, ge=1, description="Required if checkout_type is buy_now")

    @model_validator(mode="after")
    def validate_checkout_type(self) -> "OrderCreateRequest":
        if self.checkout_type == "buy_now":
            if not self.product_id or not self.quantity:
                raise ValueError("product_id and quantity are required for buy_now checkout")
        elif self.checkout_type == "cart":
            if self.product_id or self.quantity:
                raise ValueError("product_id and quantity must not be provided for cart checkout")
        return self

class OrderItemResponse(BaseModel):
    order_item_id: int
    product_id: int
    quantity: int
    product_price: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class OrderResponse(BaseModel):
    order_id: int
    order_number: str
    user_id: int
    address_id: int
    order_status: str
    payment_status: str
    total_amount: Decimal
    expected_delivery_date: date
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse]

    model_config = ConfigDict(from_attributes=True)

class AddedItem(BaseModel):
    product_id: int
    product_name: str
    quantity_added: int
    current_price: Decimal
    price_changed: bool

class UnavailableItem(BaseModel):
    product_id: int
    product_name: str
    reason: str

class BuyAgainResponse(BaseModel):
    message: str
    added_items: List[AddedItem]
    unavailable_items: List[UnavailableItem]
    cart_total_items: int

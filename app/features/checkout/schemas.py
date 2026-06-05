from pydantic import BaseModel, model_validator
from typing import Optional, Literal
from datetime import datetime

class CheckoutPreviewRequest(BaseModel):
    checkout_type: Literal["buy_now", "cart"]
    address_id: int
    product_id: Optional[int] = None
    quantity: Optional[int] = None

    @model_validator(mode='after')
    def validate_checkout_type_requirements(self) -> 'CheckoutPreviewRequest':
        if self.checkout_type == "buy_now":
            if self.product_id is None or self.quantity is None:
                raise ValueError("buy_now checkout requires both product_id and quantity")
            if self.quantity <= 0:
                raise ValueError("quantity must be greater than 0")
        elif self.checkout_type == "cart":
            if self.product_id is not None or self.quantity is not None:
                raise ValueError("cart checkout must not include product_id or quantity")
        return self

class CheckoutItem(BaseModel):
    product_id: int
    product_name: str
    quantity: int
    unit_price: float
    line_total: float

class FinancialSummary(BaseModel):
    subtotal: float
    delivery_fee: float
    grand_total: float

from app.features.addresses.schemas import AddressResponse

class CheckoutSummaryResponse(BaseModel):
    checkout_type: str
    delivery_address: AddressResponse
    items: list[CheckoutItem]
    financial_summary: FinancialSummary
    expected_delivery_date: str

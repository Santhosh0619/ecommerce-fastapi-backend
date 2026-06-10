from pydantic import BaseModel, ConfigDict
from typing import Literal, Optional
from datetime import datetime
from decimal import Decimal

class PaymentInitiateRequest(BaseModel):
    order_id: int
    payment_method: Literal['UPI', 'Card', 'COD']

class PaymentInitiateResponse(BaseModel):
    payment_id: int
    order_id: int
    gateway_provider: str
    client_secret: Optional[str] = None # For Stripe
    message: str

class PaymentResponse(BaseModel):
    payment_id: int
    order_id: int
    gateway_provider: str
    payment_method: str
    payment_status: str
    payment_amount: Decimal
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

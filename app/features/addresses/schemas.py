from pydantic import BaseModel, Field, constr
from typing import Optional
from datetime import datetime

class AddressBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=50, description="E.g., Home, Office")
    full_name: str = Field(..., min_length=2, max_length=100)
    # Simple regex for phone numbers: Allows optional +, digits, spaces, hyphens
    phone_number: str = Field(..., pattern=r'^\+?[\d\s\-]{7,20}$')
    address_line_1: str = Field(..., min_length=5, max_length=255)
    address_line_2: Optional[str] = Field(None, max_length=255)
    city: str = Field(..., min_length=2, max_length=100)
    state: str = Field(..., min_length=2, max_length=100)
    postal_code: str = Field(..., pattern=r'^[\w\s\-]{3,20}$')
    is_default: bool = False

class AddressCreate(AddressBase):
    pass

class AddressUpdate(AddressBase):
    title: Optional[str] = Field(None, min_length=2, max_length=50)
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone_number: Optional[str] = Field(None, pattern=r'^\+?[\d\s\-]{7,20}$')
    address_line_1: Optional[str] = Field(None, min_length=5, max_length=255)
    city: Optional[str] = Field(None, min_length=2, max_length=100)
    state: Optional[str] = Field(None, min_length=2, max_length=100)
    postal_code: Optional[str] = Field(None, pattern=r'^[\w\s\-]{3,20}$')
    is_default: Optional[bool] = None

class AddressResponse(AddressBase):
    address_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }

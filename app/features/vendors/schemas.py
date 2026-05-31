from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class VendorApplicationBase(BaseModel):
    store_name: str
    business_details: str

class VendorApplicationCreate(VendorApplicationBase):
    pass

class VendorApplicationUpdate(BaseModel):
    status: str # "approved" or "rejected"
    rejection_reason: Optional[str] = None

class VendorApplicationResponse(VendorApplicationBase):
    application_id: int
    user_id: int
    status: str
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

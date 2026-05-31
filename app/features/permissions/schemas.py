from pydantic import BaseModel, ConfigDict
from datetime import datetime

class PermissionBase(BaseModel):
    permission_name: str

class PermissionCreate(PermissionBase):
    pass

class PermissionResponse(PermissionBase):
    permission_id: int
    created_at: datetime
    
    # This allows Pydantic to read data from SQLAlchemy model objects directly
    model_config = ConfigDict(from_attributes=True)

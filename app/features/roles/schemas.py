from pydantic import BaseModel, ConfigDict
from datetime import datetime

# Schema for creating a Role
class RoleBase(BaseModel):
    role_name: str

class RoleCreate(RoleBase):
    pass

class RoleResponse(RoleBase):
    role_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Schema for assigning a Permission to a Role
class RolePermissionAssign(BaseModel):
    permission_id: int

class RolePermissionResponse(BaseModel):
    role_permission_id: int
    role_id: int
    permission_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

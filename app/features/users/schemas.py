from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from typing import Optional

# --- User Schemas ---

class UserBase(BaseModel):
    user_name: str
    email: EmailStr  # Automatically validates that it is a proper email format!
    phone_number: Optional[str] = None

class UserCreate(UserBase):
    password: str # Required for creation, but NEVER included in the response schema

class UserResponse(UserBase):
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# --- Mapping Schemas ---

class UserRoleAssign(BaseModel):
    role_id: int

class UserPermissionAssign(BaseModel):
    permission_id: int

class UserRoleResponse(BaseModel):
    user_role_id: int
    user_id: int
    role_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class UserPermissionResponse(BaseModel):
    user_permission_id: int
    user_id: int
    permission_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- User Profile Schemas ---

class UserProfileBase(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    address: Optional[str] = None
    profile_picture_url: Optional[str] = None

class UserProfileUpdate(UserProfileBase):
    pass

class UserProfileResponse(UserProfileBase):
    profile_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

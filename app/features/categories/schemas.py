from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional

# --- Category Schemas ---

class CategoryBase(BaseModel):
    category_name: str = Field(..., max_length=100)
    category_status: bool = True
    parent_category_id: Optional[int] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    category_name: Optional[str] = Field(None, max_length=100)
    category_status: Optional[bool] = None
    parent_category_id: Optional[int] = None

class CategoryChildResponse(CategoryBase):
    category_id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class CategoryResponse(CategoryChildResponse):
    # Nested subcategories limited to one level deep to match our eager loading
    subcategories: list[CategoryChildResponse] = []

    model_config = ConfigDict(from_attributes=True)

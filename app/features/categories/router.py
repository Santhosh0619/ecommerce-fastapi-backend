from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database.session import get_db
from app.features.categories import schemas, services
from app.features.auth.dependencies import RequireRole

router = APIRouter(prefix="/categories", tags=["Categories"])

# Roles allowed to read categories
READ_ROLES = ["Admin", "Vendor", "Customer"]

@router.get("/", response_model=List[schemas.CategoryResponse], dependencies=[Depends(RequireRole(READ_ROLES))])
async def read_root_categories(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """Fetch all root categories (categories without a parent)."""
    return await services.get_all_root_categories(db, skip=skip, limit=limit)

@router.get("/{category_id}", response_model=schemas.CategoryResponse, dependencies=[Depends(RequireRole(READ_ROLES))])
async def read_category(category_id: int, db: AsyncSession = Depends(get_db)):
    """Fetch a single category by ID, including its immediate subcategories."""
    return await services.get_category(db, category_id)

@router.post("/", response_model=schemas.CategoryResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RequireRole(["Admin"]))])
async def create_new_category(category_in: schemas.CategoryCreate, db: AsyncSession = Depends(get_db)):
    """Create a new category. Admin only."""
    return await services.create_category(db, category_in)

@router.put("/{category_id}", response_model=schemas.CategoryResponse, dependencies=[Depends(RequireRole(["Admin"]))])
async def update_existing_category(category_id: int, category_in: schemas.CategoryUpdate, db: AsyncSession = Depends(get_db)):
    """Update a category. Admin only."""
    return await services.update_category(db, category_id, category_in)

@router.delete("/{category_id}", status_code=status.HTTP_200_OK, dependencies=[Depends(RequireRole(["Admin"]))])
async def delete_existing_category(category_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a category. Admin only. Fails if the category has subcategories."""
    return await services.delete_category(db, category_id)

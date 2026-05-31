from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database.session import get_db
from app.features.permissions import schemas, services
from app.features.auth.dependencies import RequireRole

router = APIRouter(prefix="/permissions", tags=["Permissions"], dependencies=[Depends(RequireRole(["Admin"]))])

@router.post("/", response_model=schemas.PermissionResponse, status_code=status.HTTP_201_CREATED)
async def create_permission(permission: schemas.PermissionCreate, db: AsyncSession = Depends(get_db)):
    """API endpoint to create a new permission."""
    return await services.create_new_permission(db, permission)

@router.get("/", response_model=List[schemas.PermissionResponse])
async def read_permissions(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """API endpoint to fetch all permissions."""
    return await services.get_all_permissions(db, skip=skip, limit=limit)

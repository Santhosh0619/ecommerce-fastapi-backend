from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.features.permissions import crud, schemas

async def create_new_permission(db: AsyncSession, permission: schemas.PermissionCreate):
    """Business logic to create a permission, ensuring no duplicates."""
    db_perm = await crud.get_permission_by_name(db, permission.permission_name)
    if db_perm:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="Permission already exists"
        )
    return await crud.create_permission(db, permission)

async def get_all_permissions(db: AsyncSession, skip: int = 0, limit: int = 100):
    """Business logic to fetch permissions."""
    return await crud.get_permissions(db, skip=skip, limit=limit)

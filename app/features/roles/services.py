from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.features.roles import crud, schemas
from app.features.permissions import crud as perm_crud

async def create_new_role(db: AsyncSession, role: schemas.RoleCreate):
    """Business logic to create a role, preventing duplicates."""
    db_role = await crud.get_role_by_name(db, role.role_name)
    if db_role:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Role already exists")
    return await crud.create_role(db, role)

async def get_all_roles(db: AsyncSession, skip: int = 0, limit: int = 100):
    """Fetch roles."""
    return await crud.get_roles(db, skip=skip, limit=limit)

async def assign_permission_to_role(db: AsyncSession, role_id: int, assign_data: schemas.RolePermissionAssign):
    """Business logic to safely assign a permission to a role."""
    
    # 1. Verify Role exists
    role = await crud.get_role_by_id(db, role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
        
    # 2. Verify Permission exists by checking the other module's crud!
    # This shows the power of DDD - modules can talk to each other cleanly.
    permission = await perm_crud.get_permission_by_id(db, assign_data.permission_id)
    if not permission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")
        
    # 3. Prevent duplicate assignment
    if await crud.check_role_has_permission(db, role_id, assign_data.permission_id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Role already has this permission")
        
    return await crud.assign_permission(db, role_id=role_id, permission_id=assign_data.permission_id)

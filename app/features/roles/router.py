from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database.session import get_db
from app.features.roles import schemas, services
from app.features.auth.dependencies import RequireRole

router = APIRouter(prefix="/roles", tags=["Roles"], dependencies=[Depends(RequireRole(["Admin"]))])

@router.post("/", response_model=schemas.RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(role: schemas.RoleCreate, db: AsyncSession = Depends(get_db)):
    """API endpoint to create a new role (e.g. Admin, Customer)."""
    return await services.create_new_role(db, role)

@router.get("/", response_model=List[schemas.RoleResponse])
async def read_roles(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """API endpoint to fetch all roles."""
    return await services.get_all_roles(db, skip=skip, limit=limit)

@router.post("/{role_id}/permissions", response_model=schemas.RolePermissionResponse, status_code=status.HTTP_201_CREATED)
async def assign_permission(role_id: int, assign_data: schemas.RolePermissionAssign, db: AsyncSession = Depends(get_db)):
    """
    API endpoint to assign a Permission to a Role.
    Pass the permission_id in the JSON body.
    """
    return await services.assign_permission_to_role(db, role_id, assign_data)

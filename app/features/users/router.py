from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database.session import get_db
from app.features.users import schemas, services
from app.features.auth.dependencies import RequireRole, require_self_or_admin
from app.features.users.models import User

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/", response_model=List[schemas.UserResponse], dependencies=[Depends(RequireRole(["Admin"]))])
async def read_users(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """Fetch all users."""
    return await services.get_all_users(db, skip=skip, limit=limit)

@router.post("/", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RequireRole(["Admin"]))])
async def create_new_user(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    """API endpoint to create a new user manually. Only Admins can do this without registration."""
    return await services.create_new_user(db, user)

@router.get("/{user_id}", response_model=schemas.UserResponse)
async def read_user(user_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_self_or_admin)):
    """Fetch a specific user by ID."""
    return await services.get_user(db, user_id)

@router.post("/{user_id}/roles", response_model=schemas.UserRoleResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RequireRole(["Admin"]))])
async def assign_role_to_user(user_id: int, assign_data: schemas.UserRoleAssign, db: AsyncSession = Depends(get_db)):
    """Assign a role (e.g. Admin) to a user."""
    return await services.assign_role(db, user_id, assign_data)

@router.post("/{user_id}/permissions", response_model=schemas.UserPermissionResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RequireRole(["Admin"]))])
async def assign_permission_to_user(user_id: int, assign_data: schemas.UserPermissionAssign, db: AsyncSession = Depends(get_db)):
    """Assign a specific permission directly to a user, bypassing role assignment."""
    return await services.assign_permission(db, user_id, assign_data)

@router.get("/{user_id}/profile", response_model=schemas.UserProfileResponse)
async def read_user_profile(user_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_self_or_admin)):
    """Fetch a specific user's profile details."""
    return await services.get_user_profile(db, user_id)

@router.put("/{user_id}/profile", response_model=schemas.UserProfileResponse)
async def update_user_profile(user_id: int, profile_data: schemas.UserProfileUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_self_or_admin)):
    """Update or create a user's profile details."""
    return await services.update_user_profile(db, user_id, profile_data)

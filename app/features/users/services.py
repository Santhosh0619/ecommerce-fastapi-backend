from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.features.users import crud, schemas
from app.features.roles import crud as role_crud
from app.features.permissions import crud as perm_crud

async def get_all_users(db: AsyncSession, skip: int = 0, limit: int = 100):
    return await crud.get_users(db, skip=skip, limit=limit)

async def create_new_user(db: AsyncSession, user: schemas.UserCreate):
    existing_user = await crud.get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
        
    return await crud.create_user(db, user)

async def get_user(db: AsyncSession, user_id: int):
    user = await crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

async def assign_role(db: AsyncSession, user_id: int, assign_data: schemas.UserRoleAssign):
    # 1. Verify User exists
    user = await crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # 2. Verify Role exists using cross-module communication
    role = await role_crud.get_role_by_id(db, assign_data.role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
        
    # 3. Prevent duplicate assignment
    if await crud.check_user_has_role(db, user_id, assign_data.role_id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already has this role")
        
    return await crud.assign_role_to_user(db, user_id, assign_data.role_id)

async def assign_permission(db: AsyncSession, user_id: int, assign_data: schemas.UserPermissionAssign):
    # 1. Verify User exists
    user = await crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
    # 2. Verify Permission exists
    permission = await perm_crud.get_permission_by_id(db, assign_data.permission_id)
    if not permission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")
        
    # 3. Prevent duplicate assignment
    if await crud.check_user_has_permission(db, user_id, assign_data.permission_id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already has this permission")
        
    return await crud.assign_permission_to_user(db, user_id, assign_data.permission_id)

async def get_user_profile(db: AsyncSession, user_id: int):
    # Verify User exists
    user = await crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
    profile = await crud.get_user_profile(db, user_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return profile

async def update_user_profile(db: AsyncSession, user_id: int, profile_data: schemas.UserProfileUpdate):
    # Verify User exists
    user = await crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
    return await crud.upsert_user_profile(db, user_id, profile_data)

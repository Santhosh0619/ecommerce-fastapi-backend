from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.features.users.models import User, UserRole, UserPermission, UserProfile
from app.features.users.schemas import UserCreate, UserProfileUpdate
from app.core.security import get_password_hash

async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalars().first()

async def get_user_by_id(db: AsyncSession, user_id: int):
    result = await db.execute(select(User).filter(User.user_id == user_id))
    return result.scalars().first()

async def get_users(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(User).offset(skip).limit(limit))
    return result.scalars().all()

async def create_user(db: AsyncSession, user: UserCreate):
    # Hash password BEFORE saving to the database
    hashed_pwd = get_password_hash(user.password)
    
    db_user = User(
        user_name=user.user_name,
        email=user.email,
        phone_number=user.phone_number,
        hashed_password=hashed_pwd
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def assign_role_to_user(db: AsyncSession, user_id: int, role_id: int):
    db_user_role = UserRole(user_id=user_id, role_id=role_id)
    db.add(db_user_role)
    await db.commit()
    await db.refresh(db_user_role)
    return db_user_role

async def assign_permission_to_user(db: AsyncSession, user_id: int, permission_id: int):
    db_user_perm = UserPermission(user_id=user_id, permission_id=permission_id)
    db.add(db_user_perm)
    await db.commit()
    await db.refresh(db_user_perm)
    return db_user_perm

async def get_user_profile(db: AsyncSession, user_id: int):
    result = await db.execute(select(UserProfile).filter(UserProfile.user_id == user_id))
    return result.scalars().first()

async def upsert_user_profile(db: AsyncSession, user_id: int, profile_data: UserProfileUpdate):
    profile = await get_user_profile(db, user_id)
    if not profile:
        profile = UserProfile(user_id=user_id)
        db.add(profile)
    
    # Update fields
    if profile_data.full_name is not None:
        profile.full_name = profile_data.full_name
    if profile_data.bio is not None:
        profile.bio = profile_data.bio
    if profile_data.address is not None:
        profile.address = profile_data.address
    if profile_data.profile_picture_url is not None:
        profile.profile_picture_url = profile_data.profile_picture_url
        
    await db.commit()
    await db.refresh(profile)
    return profile

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.features.permissions.models import Permission
from app.features.permissions.schemas import PermissionCreate

async def get_permission_by_name(db: AsyncSession, permission_name: str):
    """Fetch a permission by its unique name."""
    result = await db.execute(select(Permission).filter(Permission.permission_name == permission_name))
    return result.scalars().first()

async def get_permission_by_id(db: AsyncSession, permission_id: int):
    """Fetch a permission by its ID."""
    result = await db.execute(select(Permission).filter(Permission.permission_id == permission_id))
    return result.scalars().first()

async def get_permissions(db: AsyncSession, skip: int = 0, limit: int = 100):
    """Fetch a list of permissions with pagination."""
    result = await db.execute(select(Permission).offset(skip).limit(limit))
    return result.scalars().all()

async def create_permission(db: AsyncSession, permission: PermissionCreate):
    """Create a new permission in the database."""
    db_permission = Permission(permission_name=permission.permission_name)
    db.add(db_permission)
    await db.commit()
    await db.refresh(db_permission)
    return db_permission

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.features.roles.models import Role, RolePermission
from app.features.roles.schemas import RoleCreate

async def get_role_by_name(db: AsyncSession, role_name: str):
    result = await db.execute(select(Role).filter(Role.role_name == role_name))
    return result.scalars().first()

async def get_role_by_id(db: AsyncSession, role_id: int):
    result = await db.execute(select(Role).filter(Role.role_id == role_id))
    return result.scalars().first()

async def get_roles(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(Role).offset(skip).limit(limit))
    return result.scalars().all()

async def create_role(db: AsyncSession, role: RoleCreate):
    db_role = Role(role_name=role.role_name)
    db.add(db_role)
    await db.commit()
    await db.refresh(db_role)
    return db_role

async def assign_permission(db: AsyncSession, role_id: int, permission_id: int):
    db_role_perm = RolePermission(role_id=role_id, permission_id=permission_id)
    db.add(db_role_perm)
    await db.commit()
    await db.refresh(db_role_perm)
    return db_role_perm

async def check_role_has_permission(db: AsyncSession, role_id: int, permission_id: int) -> bool:
    result = await db.execute(select(RolePermission).filter(RolePermission.role_id == role_id, RolePermission.permission_id == permission_id))
    return result.scalars().first() is not None

async def get_user_roles_names(db: AsyncSession, user_id: int) -> list[str]:
    from app.features.users.models import UserRole
    stmt = select(Role.role_name).join(UserRole, UserRole.role_id == Role.role_id).filter(UserRole.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalars().all()

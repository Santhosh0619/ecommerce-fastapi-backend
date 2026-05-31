import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.features.roles.models import Role
from app.features.users.models import User, UserRole
from app.core.security import get_password_hash

logger = logging.getLogger(__name__)

async def seed_default_roles(db: AsyncSession):
    default_roles = ["Admin", "Customer", "Vendor"]
    for role_name in default_roles:
        result = await db.execute(select(Role).filter(Role.role_name == role_name))
        role = result.scalars().first()
        if not role:
            logger.info(f"Seeding default role: {role_name}")
            new_role = Role(role_name=role_name)
            db.add(new_role)
            await db.commit()

async def seed_default_admin(db: AsyncSession):
    email = settings.FIRST_SUPERUSER_EMAIL
    password = settings.FIRST_SUPERUSER_PASSWORD
    
    result = await db.execute(select(User).filter(User.email == email))
    admin_user = result.scalars().first()
    
    if not admin_user:
        logger.info(f"Seeding default admin user: {email}")
        admin_user = User(
            user_name="System Admin",
            email=email,
            hashed_password=get_password_hash(password)
        )
        db.add(admin_user)
        await db.commit()
        await db.refresh(admin_user)
        
        # Assign Admin role
        role_result = await db.execute(select(Role).filter(Role.role_name == "Admin"))
        admin_role = role_result.scalars().first()
        if admin_role:
            user_role = UserRole(user_id=admin_user.user_id, role_id=admin_role.role_id)
            db.add(user_role)
            await db.commit()

async def run_seeders(db: AsyncSession):
    logger.info("Running database seeders...")
    await seed_default_roles(db)
    await seed_default_admin(db)
    logger.info("Database seeding completed.")

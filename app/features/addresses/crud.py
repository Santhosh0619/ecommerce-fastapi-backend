from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, desc

from app.features.addresses.models import Address

async def get_address(db: AsyncSession, address_id: int) -> Address:
    result = await db.execute(select(Address).where(Address.address_id == address_id))
    return result.scalars().first()

async def get_user_addresses(db: AsyncSession, user_id: int) -> list[Address]:
    result = await db.execute(
        select(Address)
        .where(Address.user_id == user_id)
        .order_by(desc(Address.is_default), desc(Address.updated_at))
    )
    return result.scalars().all()

async def has_addresses(db: AsyncSession, user_id: int) -> bool:
    result = await db.execute(select(Address.address_id).where(Address.user_id == user_id).limit(1))
    return result.scalars().first() is not None

async def unset_other_defaults(db: AsyncSession, user_id: int, exclude_address_id: int = None):
    stmt = update(Address).where(Address.user_id == user_id).values(is_default=False)
    if exclude_address_id is not None:
        stmt = stmt.where(Address.address_id != exclude_address_id)
    await db.execute(stmt)
    await db.commit()

async def create_address_record(db: AsyncSession, user_id: int, address_data: dict) -> Address:
    db_address = Address(user_id=user_id, **address_data)
    db.add(db_address)
    await db.commit()
    await db.refresh(db_address)
    return db_address

async def update_address_record(db: AsyncSession, db_address: Address, address_data: dict) -> Address:
    for field, value in address_data.items():
        setattr(db_address, field, value)
    await db.commit()
    await db.refresh(db_address)
    return db_address

async def delete_address_record(db: AsyncSession, db_address: Address):
    await db.delete(db_address)
    await db.commit()

async def set_default_fallback(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(Address)
        .where(Address.user_id == user_id)
        .order_by(desc(Address.updated_at))
        .limit(1)
    )
    next_address = result.scalars().first()
    if next_address:
        next_address.is_default = True
        await db.commit()

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.features.addresses import crud, schemas
from app.features.addresses.models import Address

async def get_user_addresses(db: AsyncSession, user_id: int) -> list[Address]:
    return await crud.get_user_addresses(db, user_id)

async def get_address(db: AsyncSession, address_id: int, user_id: int) -> Address:
    db_address = await crud.get_address(db, address_id)
    if not db_address or db_address.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found")
    return db_address

async def create_address(db: AsyncSession, user_id: int, address_in: schemas.AddressCreate) -> Address:
    has_existing = await crud.has_addresses(db, user_id)
    
    # If first address, force it to be default
    is_default = True if not has_existing else address_in.is_default

    if is_default and has_existing:
        await crud.unset_other_defaults(db, user_id)

    address_data = address_in.model_dump()
    address_data["is_default"] = is_default
    return await crud.create_address_record(db, user_id, address_data)

async def update_address(db: AsyncSession, address_id: int, user_id: int, address_in: schemas.AddressUpdate) -> Address:
    db_address = await get_address(db, address_id, user_id)
        
    update_data = address_in.model_dump(exclude_unset=True)
    
    if update_data.get("is_default") is True and not db_address.is_default:
        await crud.unset_other_defaults(db, user_id, exclude_address_id=address_id)
    elif update_data.get("is_default") is False and db_address.is_default:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot unset the default address directly. Please set another address as default instead.")

    return await crud.update_address_record(db, db_address, update_data)

async def delete_address(db: AsyncSession, address_id: int, user_id: int):
    db_address = await get_address(db, address_id, user_id)
        
    was_default = db_address.is_default
    await crud.delete_address_record(db, db_address)
    
    if was_default:
        await crud.set_default_fallback(db, user_id)

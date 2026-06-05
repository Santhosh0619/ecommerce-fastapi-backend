from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database.session import get_db
from app.features.auth.dependencies import get_current_user
from app.features.users.models import User
from app.features.roles.crud import get_user_roles_names
from app.features.addresses import schemas, services, crud

router = APIRouter(prefix="/addresses", tags=["Addresses"])

async def allow_customer_vendor_address(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    roles = await get_user_roles_names(db, current_user.user_id)
    if "Admin" in roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admins cannot use the addresses feature")
    if "Customer" not in roles and "Vendor" not in roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Role not permitted")
    return current_user

@router.post("/", response_model=schemas.AddressResponse, status_code=status.HTTP_201_CREATED)
async def create_user_address(
    address_in: schemas.AddressCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(allow_customer_vendor_address)
):
    return await services.create_address(db, current_user.user_id, address_in)

@router.get("/", response_model=List[schemas.AddressResponse])
async def list_user_addresses(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(allow_customer_vendor_address)
):
    return await services.get_user_addresses(db, current_user.user_id)

@router.get("/{address_id}", response_model=schemas.AddressResponse)
async def get_user_address(
    address_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(allow_customer_vendor_address)
):
    return await services.get_address(db, address_id, current_user.user_id)

@router.put("/{address_id}", response_model=schemas.AddressResponse)
async def update_user_address(
    address_id: int,
    address_in: schemas.AddressUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(allow_customer_vendor_address)
):
    return await services.update_address(db, address_id, current_user.user_id, address_in)

@router.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_address(
    address_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(allow_customer_vendor_address)
):
    await services.delete_address(db, address_id, current_user.user_id)

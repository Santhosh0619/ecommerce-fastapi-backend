from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.features.auth.dependencies import get_current_user
from app.features.users.models import User
from app.features.roles.crud import get_user_roles_names
from app.features.cart import schemas, services
import typing

router = APIRouter(prefix="/cart", tags=["Cart"])

async def allow_customer_vendor(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    roles = await get_user_roles_names(db, typing.cast(int, current_user.user_id))
    if "Admin" in roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admins cannot use the shopping cart feature")
    if "Customer" not in roles and "Vendor" not in roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to use the cart")
    return current_user

@router.get("/", response_model=schemas.CartResponse)
async def get_cart(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(allow_customer_vendor)
):
    """Retrieve the current user's cart."""
    return await services.get_user_cart(db, typing.cast(int, current_user.user_id))

@router.post("/items", response_model=schemas.CartResponse)
async def add_item_to_cart(
    item_in: schemas.CartItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(allow_customer_vendor)
):
    """Add a product to the cart or increment its quantity if it already exists."""
    return await services.add_item_to_cart(db, typing.cast(int, current_user.user_id), item_in)

@router.put("/items/{cart_item_id}", response_model=schemas.CartResponse)
async def update_cart_item(
    cart_item_id: int,
    item_in: schemas.CartItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(allow_customer_vendor)
):
    """Update the quantity or selection status of a cart item."""
    return await services.update_cart_item(db, typing.cast(int, current_user.user_id), cart_item_id, item_in)

@router.delete("/items/{cart_item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cart_item(
    cart_item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(allow_customer_vendor)
):
    """Remove a specific item from the cart."""
    await services.delete_cart_item(db, typing.cast(int, current_user.user_id), cart_item_id)
    return None

@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def empty_cart(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(allow_customer_vendor)
):
    """Empty all items from the user's cart."""
    await services.empty_cart(db, typing.cast(int, current_user.user_id))
    return None

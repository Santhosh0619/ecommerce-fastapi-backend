from fastapi import status
from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database.session import get_db
from app.features.users.models import User
from app.features.auth.dependencies import get_current_user
from app.features.orders.schemas import OrderCreateRequest, OrderResponse, BuyAgainResponse
from app.features.orders import services

router = APIRouter()

@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    request: OrderCreateRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key", description="Unique UUID for idempotency"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Initialize a new order in Pending state.
    Requires an Idempotency-Key header to prevent duplicate orders.
    """
    return await services.initialize_order(db, current_user, request, idempotency_key)

@router.get("/", response_model=List[OrderResponse])
async def get_orders(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve history of orders for the current user."""
    return await services.get_user_orders(db, current_user)

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve a specific order by ID."""
    return await services.get_order(db, order_id, current_user)

@router.post("/{order_id}/buy-again", response_model=BuyAgainResponse)
async def buy_again(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Repurchase items from a delivered order.
    Adds items directly to the cart, merging quantities and enforcing current prices and availability.
    """
    return await services.process_buy_again(db, order_id, current_user)

import uuid
import logging
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
import typing
from redis.exceptions import RedisError

from app.core.redis import redis_client
from app.features.orders import crud
from app.features.orders.schemas import OrderCreateRequest
from app.features.checkout.services import process_checkout_preview
from app.features.checkout.schemas import CheckoutPreviewRequest
from app.features.users.models import User

logger = logging.getLogger(__name__)

async def initialize_order(db: AsyncSession, current_user: User, request: OrderCreateRequest, idempotency_key: str):
    redis_key = f"idempotency:order:{current_user.user_id}:{idempotency_key}"
    
    # 1. Atomic Idempotency Check via Redis (SETNX)
    try:
        acquired = await redis_client.set(redis_key, "PROCESSING", nx=True, ex=86400)
        if not acquired:
            # Key already exists. Check what it is.
            existing_val = await redis_client.get(redis_key)
            if existing_val == "PROCESSING":
                logger.warning(f"Concurrent request blocked for key {idempotency_key}")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Order is currently being processed. Please wait."
                )
            else:
                logger.info(f"Idempotency hit for key {idempotency_key}. Returning existing order.")
                uid = typing.cast(int, current_user.user_id)
                return await crud.get_order_by_id(db, order_id=int(existing_val), user_id=uid)
    except RedisError as e:
        # If Redis is completely unavailable, we fail the request 
        # to guarantee strict idempotency. We do not want to risk duplicate pending orders.
        logger.error(f"Redis is unavailable for Idempotency check: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail="Order service is currently unavailable (Idempotency validation failed). Please try again later."
        )

    # 2. Re-use Checkout Logic for valid pricing and stock checks
    # We map OrderCreateRequest -> CheckoutPreviewRequest
    checkout_req = CheckoutPreviewRequest(
        checkout_type=request.checkout_type,
        address_id=request.address_id,
        product_id=request.product_id,
        quantity=request.quantity
    )
    
    # This securely calculates total, verifies stock (without reducing it), and checks active status
    summary_data = await process_checkout_preview(db, current_user, checkout_req)
    
    # 3. Generate Order Number: ORD-YYYYMMDD-UUID
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    short_uuid = str(uuid.uuid4()).split('-')[0].upper()
    order_number = f"ORD-{date_str}-{short_uuid}"
    
    # 4. Create Order (Stock is explicitly NOT locked here)
    try:
        new_order = await crud.create_order(db, typing.cast(int, current_user.user_id), order_number, summary_data)
        await db.commit()
    except Exception as e:
        await db.rollback()
        # Clean up the PROCESSING lock if creation failed
        try:
            await redis_client.delete(redis_key)
        except RedisError as redis_err:
            logger.error(f"Failed to delete Idempotency lock from Redis after DB failure: {str(redis_err)}")
        raise e
    
    # 5. Store Idempotency Key in Redis with actual Order ID
    try:
        await redis_client.set(redis_key, str(new_order.order_id), ex=86400)
    except RedisError as e:
        # If we fail to update the key, log it. The order is persisted.
        logger.warning(f"Failed to update Idempotency key to order ID after creation: {str(e)}")
        
    return new_order

async def get_user_orders(db: AsyncSession, current_user: User):
    uid = typing.cast(int, current_user.user_id)
    return await crud.get_user_orders(db, uid)

async def get_order(db: AsyncSession, order_id: int, current_user: User):
    uid = typing.cast(int, current_user.user_id)
    return await crud.get_order_by_id(db, order_id, uid)

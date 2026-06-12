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
from app.features.orders.models import Order
from app.features.products.models import Product
from app.features.products.crud import get_product_by_id
from app.features.cart import services as cart_services
from app.features.cart import schemas as cart_schemas
from app.features.orders import schemas as order_schemas
from sqlalchemy import select
from sqlalchemy.orm import selectinload

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
    summary_data = await process_checkout_preview(db, typing.cast(int, current_user.user_id), checkout_req)
    
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

async def process_buy_again(db: AsyncSession, order_id: int, current_user: User) -> order_schemas.BuyAgainResponse:
    uid = typing.cast(int, current_user.user_id)
    logger.info(f"Buy Again request received for user_id={uid}, order_id={order_id}")

    # 1. Ownership & Status Validation
    query = select(Order).options(selectinload(Order.items)).where(Order.order_id == order_id)
    result = await db.execute(query)
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
    
    if order.user_id != uid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Order belongs to another user.")
        
    if order.order_status != "Delivered":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order is not eligible for Buy Again because it is not Delivered.")

    added_items = []
    unavailable_items = []

    # 2. Fetch all products in one query to avoid N+1
    product_ids = [typing.cast(int, item.product_id) for item in order.items]
    products_query = select(Product).where(Product.product_id.in_(product_ids))
    products_result = await db.execute(products_query)
    products_map = {typing.cast(int, p.product_id): p for p in products_result.scalars().all()}

    # 3. Iterate items & Validation
    for order_item in order.items:
        oid = typing.cast(int, order_item.product_id)
        product = products_map.get(oid)
        
        if not product:
            unavailable_items.append(order_schemas.UnavailableItem(
                product_id=oid,
                product_name="Unknown Product",
                reason="Product no longer exists."
            ))
            continue
            
        pid = typing.cast(int, product.product_id)
        pname = typing.cast(str, product.product_name)
        qty = typing.cast(int, order_item.quantity)
        
        if product.product_status != "Active":
            unavailable_items.append(order_schemas.UnavailableItem(
                product_id=pid,
                product_name=pname,
                reason="Product is currently unavailable."
            ))
            continue
            
        if typing.cast(int, product.product_stock) < qty:
            unavailable_items.append(order_schemas.UnavailableItem(
                product_id=pid,
                product_name=pname,
                reason="Insufficient stock."
            ))
            continue
            
        # 3. Add to Cart / Merge Quantities
        # Use existing cart service which inherently merges if it exists
        cart_item_in = cart_schemas.CartItemCreate(
            product_id=pid,
            quantity=qty
        )
        try:
            # add_item_to_cart inherently sums quantities and checks total against stock
            await cart_services.add_item_to_cart(db, uid, cart_item_in, commit=False)
            
            p_price = product.product_price
            o_price = order_item.product_price
            price_changed = p_price != o_price
            
            added_items.append(order_schemas.AddedItem(
                product_id=pid,
                product_name=pname,
                quantity_added=qty,
                current_price=p_price, # type: ignore
                price_changed=price_changed
            ))
        except HTTPException as e:
            # If add_item_to_cart throws error (e.g. total quantity > stock)
            unavailable_items.append(order_schemas.UnavailableItem(
                product_id=pid,
                product_name=pname,
                reason=e.detail if isinstance(e.detail, str) else "Failed to add to cart."
            ))

    if added_items:
        try:
            await db.commit()
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail="Database error occurred while processing Buy Again request.")

    # Retrieve current cart total items
    cart_resp = await cart_services.get_user_cart(db, uid)
    cart_total_items = sum(item.quantity for item in cart_resp.items) if cart_resp and cart_resp.items else 0

    if not added_items:
        return order_schemas.BuyAgainResponse(
            message="No products could be added to the cart.",
            added_items=[],
            unavailable_items=unavailable_items,
            cart_total_items=cart_total_items
        )
        
    return order_schemas.BuyAgainResponse(
        message=f"Successfully added {len(added_items)} item(s) to your cart.",
        added_items=added_items,
        unavailable_items=unavailable_items,
        cart_total_items=cart_total_items
    )

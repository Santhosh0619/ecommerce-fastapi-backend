from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.features.payments.models import Payment
from app.features.orders.models import Order
from app.features.products.models import Product
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

async def create_payment(
    db: AsyncSession, 
    order_id: int, 
    gateway_provider: str,
    payment_method: str,
    payment_amount: Decimal,
    transaction_reference: str,
    stripe_payment_intent_id: str = None
) -> Payment:
    payment = Payment(
        order_id=order_id,
        gateway_provider=gateway_provider,
        payment_method=payment_method,
        payment_amount=payment_amount,
        payment_status='Pending',
        transaction_reference=transaction_reference,
        stripe_payment_intent_id=stripe_payment_intent_id
    )
    db.add(payment)
    await db.flush()
    return payment

async def get_payment_by_intent(db: AsyncSession, intent_id: str) -> Payment:
    query = select(Payment).where(Payment.stripe_payment_intent_id == intent_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def get_pending_payment_for_order(db: AsyncSession, order_id: int) -> Payment:
    query = select(Payment).where(Payment.order_id == order_id, Payment.payment_status == 'Pending')
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def confirm_order_transaction(db: AsyncSession, payment: Payment, mark_payment_success: bool = True):
    # This is a critical transaction
    if mark_payment_success:
        payment.payment_status = 'Success'
    
    query = select(Order).options(selectinload(Order.items)).where(Order.order_id == payment.order_id)
    result = await db.execute(query)
    order = result.scalar_one()
    
    # Synchronize order.payment_status
    order.payment_status = payment.payment_status
    
    out_of_stock_detected = False
    products_to_update = []
    
    # 1. Fetch products with FOR UPDATE locks to prevent concurrent modification
    for item in order.items:
        prod_query = select(Product).where(Product.product_id == item.product_id).with_for_update()
        prod_result = await db.execute(prod_query)
        product = prod_result.scalar_one()
        
        if product.product_stock < item.quantity:
            out_of_stock_detected = True
            break
        products_to_update.append((product, item.quantity))
            
    # 2. Stock Conflict Resolution
    if out_of_stock_detected:
        order.order_status = 'Cancelled'
        logger.error(f"Stock conflict for order {order.order_id}. Payment {payment.payment_id} succeeded but items out of stock. Refund required.")
        # Future: Trigger Admin Notification & Automatic Refund Workflow
    else:
        # 3. Deduct stock safely since we hold the row locks
        for product, quantity in products_to_update:
            product.product_stock -= quantity
        order.order_status = 'Confirmed'
        logger.info(f"Order {order.order_id} Confirmed and stock deducted securely.")
        
    await db.flush()
    return order

async def mark_payment_failed(db: AsyncSession, payment: Payment):
    payment.payment_status = 'Failed'
    query = select(Order).where(Order.order_id == payment.order_id)
    result = await db.execute(query)
    order = result.scalar_one()
    order.payment_status = 'Failed'
    await db.flush()

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from app.features.orders.models import Order, OrderItem
from app.features.checkout.schemas import CheckoutSummaryResponse

async def create_order(
    db: AsyncSession, 
    user_id: int, 
    order_number: str,
    summary_data: CheckoutSummaryResponse
) -> Order:
    # Create the order WITHOUT reducing stock.
    new_order = Order(
        order_number=order_number,
        user_id=user_id,
        address_id=summary_data.delivery_address.address_id,
        order_status='Pending',
        payment_status='Pending',
        total_amount=summary_data.financial_summary.total_to_pay,
        expected_delivery_date=summary_data.expected_delivery_date
    )
    
    db.add(new_order)
    await db.flush() # Flush to get new_order.order_id
    
    order_items = []
    for item in summary_data.items:
        order_items.append(
            OrderItem(
                order_id=new_order.order_id,
                product_id=item.product_id,
                quantity=item.quantity,
                product_price=item.price
            )
        )
        
    db.add_all(order_items)
    await db.flush() # Let the service layer handle the commit
    
    # Eager load items before returning
    query = select(Order).options(selectinload(Order.items)).where(Order.order_id == new_order.order_id)
    result = await db.execute(query)
    return result.scalar_one()

async def get_user_orders(db: AsyncSession, user_id: int) -> list[Order]:
    query = select(Order).options(selectinload(Order.items)).where(Order.user_id == user_id).order_by(Order.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())

async def get_order_by_id(db: AsyncSession, order_id: int, user_id: int) -> Order:
    query = select(Order).options(selectinload(Order.items)).where(Order.order_id == order_id, Order.user_id == user_id)
    result = await db.execute(query)
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order

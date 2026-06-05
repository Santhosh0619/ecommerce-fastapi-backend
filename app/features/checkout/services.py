from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from datetime import datetime, timedelta

from app.features.addresses.crud import get_address
from app.features.checkout.schemas import CheckoutPreviewRequest, CheckoutSummaryResponse, CheckoutItem, FinancialSummary
from app.features.cart.crud import get_cart_by_user_id
from app.features.products.crud import get_product_by_id
from app.core.config import settings

def calculate_expected_delivery() -> str:
    # Processing time: 1 day, Transit time: 3-5 days
    # Total: 4 to 6 business days. Let's make a simple loop to add business days.
    
    def add_business_days(start_date: datetime, days_to_add: int) -> datetime:
        current_date = start_date
        while days_to_add > 0:
            current_date += timedelta(days=1)
            # 5 = Saturday, 6 = Sunday
            if current_date.weekday() < 5:
                days_to_add -= 1
        return current_date

    now = datetime.utcnow()
    min_date = add_business_days(now, 4)
    max_date = add_business_days(now, 6)
    
    # Format: June 8, 2026 - June 10, 2026 (Handling leading zeros safely for Windows)
    min_str = min_date.strftime('%B %d, %Y').replace(' 0', ' ')
    max_str = max_date.strftime('%B %d, %Y').replace(' 0', ' ')
    return f"{min_str} - {max_str}"

async def process_checkout_preview(db: AsyncSession, user_id: int, request: CheckoutPreviewRequest) -> CheckoutSummaryResponse:
    # 1. Validate Address
    address = await get_address(db, request.address_id)
    if not address or address.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A valid delivery address is required for checkout")

    items = []
    subtotal = 0.0

    # 2. Process Items based on Checkout Type
    if request.checkout_type == "buy_now":
        product = await get_product_by_id(db, request.product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        
        if product.product_status != "Active":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Product '{product.product_name}' is {product.product_status} and cannot be purchased")
        
        if product.product_stock < request.quantity:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Product '{product.product_name}' has insufficient stock (Requested: {request.quantity}, Available: {product.product_stock})")
        
        line_total = float(product.product_price) * request.quantity
        subtotal += line_total
        items.append(CheckoutItem(
            product_id=product.product_id,
            product_name=product.product_name,
            quantity=request.quantity,
            unit_price=product.product_price,
            line_total=line_total
        ))

    elif request.checkout_type == "cart":
        cart = await get_cart_by_user_id(db, user_id)
        if not cart:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cart is empty")

        selected_items = [item for item in cart.items if item.is_selected]
        
        if not selected_items:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No items selected in cart for checkout")

        for item in selected_items:
            product = item.product
            if product.product_status != "Active":
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Product '{product.product_name}' is {product.product_status} and cannot be purchased")
            
            if product.product_stock < item.quantity:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Product '{product.product_name}' has insufficient stock (Requested: {item.quantity}, Available: {product.product_stock})")
            
            line_total = float(product.product_price) * item.quantity
            subtotal += line_total
            items.append(CheckoutItem(
                product_id=product.product_id,
                product_name=product.product_name,
                quantity=item.quantity,
                unit_price=product.product_price,
                line_total=line_total
            ))

    # 3. Calculate Financials
    delivery_fee = settings.CHECKOUT_DELIVERY_FEE
    grand_total = subtotal + delivery_fee
    financials = FinancialSummary(
        subtotal=subtotal,
        delivery_fee=delivery_fee,
        grand_total=grand_total
    )

    # 4. Generate Response
    return CheckoutSummaryResponse(
        checkout_type=request.checkout_type,
        delivery_address=address,
        items=items,
        financial_summary=financials,
        expected_delivery_date=calculate_expected_delivery()
    )

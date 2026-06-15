from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.features.cart import crud, schemas
from app.features.products.crud import get_product_by_id
from app.features.roles.crud import get_user_roles_names
import typing

async def get_or_create_cart(db: AsyncSession, user_id: int, commit: bool = True):
    cart = await crud.get_cart_by_user_id(db, user_id)
    if not cart:
        cart = await crud.create_cart(db, user_id, commit=commit)
    return cart

def _format_cart_response(cart):
    if not cart:
        return None
        
    items_response = []
    selected_item_count = 0
    selected_subtotal = 0.0
    
    for item in cart.items:
        # Determine primary image URL
        primary_image = None
        for img in item.product.images:
            if img.is_primary:
                primary_image = img.image_url
                break
        
        # Calculate dynamic fields
        product_unavailable = False
        stock_warning = False
        
        if item.product.product_status != "Active":
            product_unavailable = True
        
        if item.quantity > item.product.product_stock:
            stock_warning = True
            
        if item.is_selected:
            selected_item_count += 1
            selected_subtotal += float(item.product.product_price) * item.quantity
            
        items_response.append({
            "cart_item_id": item.cart_item_id,
            "cart_id": item.cart_id,
            "product_id": item.product_id,
            "quantity": item.quantity,
            "is_selected": item.is_selected,
            "created_at": item.created_at,
            "updated_at": item.updated_at,
            "product_name": item.product.product_name,
            "product_price": float(item.product.product_price),
            "product_stock": item.product.product_stock,
            "product_slug": item.product.product_slug,
            "primary_image_url": primary_image,
            "stock_warning": stock_warning,
            "product_unavailable": product_unavailable
        })
        
    return schemas.CartResponse(
        cart_id=cart.cart_id,
        user_id=cart.user_id,
        created_at=cart.created_at,
        updated_at=cart.updated_at,
        items=items_response,
        selected_item_count=selected_item_count,
        selected_subtotal=selected_subtotal
    )

async def get_user_cart(db: AsyncSession, user_id: int):
    cart = await get_or_create_cart(db, user_id)
    # Refresh to load relationships properly if just created
    cart_with_items = await crud.get_cart_by_user_id(db, user_id)
    return _format_cart_response(cart_with_items)

async def add_item_to_cart(db: AsyncSession, user_id: int, item_in: schemas.CartItemCreate, commit: bool = True):
    # Verify Product
    product = await get_product_by_id(db, item_in.product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        
    if product.product_status != "Active":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot add inactive or archived product to cart")
        
    cart = await get_or_create_cart(db, user_id, commit=commit)
    
    # Check if item exists
    existing_item = await crud.get_cart_item(db, typing.cast(int, cart.cart_id), item_in.product_id)
    
    if existing_item:
        new_quantity = existing_item.quantity + item_in.quantity
        if new_quantity > product.product_stock:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quantity exceeds available product stock")
        existing_item.quantity = new_quantity
        await crud.update_cart_item(db, existing_item, commit=commit)
    else:
        if item_in.quantity > product.product_stock:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quantity exceeds available product stock")
        await crud.add_cart_item(db, typing.cast(int, cart.cart_id), product.product_id, item_in.quantity, is_selected=True, commit=commit)
        
    return await get_user_cart(db, user_id)

async def update_cart_item(db: AsyncSession, user_id: int, cart_item_id: int, item_in: schemas.CartItemUpdate):
    cart = await crud.get_cart_by_user_id(db, user_id)
    if not cart:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")
        
    db_item = await crud.get_cart_item_by_id(db, cart_item_id)
    if not db_item or db_item.cart_id != cart.cart_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")
        
    product = await get_product_by_id(db, typing.cast(int, db_item.product_id))
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    
    if item_in.quantity is not None:
        if item_in.quantity > product.product_stock:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quantity exceeds available product stock")
        db_item.quantity = item_in.quantity
        
    if item_in.is_selected is not None:
        db_item.is_selected = item_in.is_selected
        
    await crud.update_cart_item(db, db_item)
    return await get_user_cart(db, user_id)

async def delete_cart_item(db: AsyncSession, user_id: int, cart_item_id: int):
    cart = await crud.get_cart_by_user_id(db, user_id)
    if not cart:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")
        
    db_item = await crud.get_cart_item_by_id(db, cart_item_id)
    if not db_item or db_item.cart_id != cart.cart_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")
        
    await crud.delete_cart_item(db, db_item)
    return None

async def empty_cart(db: AsyncSession, user_id: int):
    cart = await crud.get_cart_by_user_id(db, user_id)
    if not cart:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")
        
    await crud.empty_cart(db, typing.cast(int, cart.cart_id))
    return None

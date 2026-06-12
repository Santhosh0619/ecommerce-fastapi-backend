from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.features.cart.models import Cart, CartItem
from app.features.products.models import Product

async def get_cart_by_user_id(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(Cart)
        .options(selectinload(Cart.items).selectinload(CartItem.product).selectinload(Product.images))
        .filter(Cart.user_id == user_id)
        .execution_options(populate_existing=True)
    )
    return result.scalars().first()

async def create_cart(db: AsyncSession, user_id: int, commit: bool = True):
    db_cart = Cart(user_id=user_id)
    db.add(db_cart)
    if commit:
        await db.commit()
        await db.refresh(db_cart)
    else:
        await db.flush()
    return db_cart

async def get_cart_item(db: AsyncSession, cart_id: int, product_id: int):
    result = await db.execute(
        select(CartItem).filter(CartItem.cart_id == cart_id, CartItem.product_id == product_id)
    )
    return result.scalars().first()

async def get_cart_item_by_id(db: AsyncSession, cart_item_id: int):
    result = await db.execute(
        select(CartItem)
        .options(selectinload(CartItem.cart))
        .filter(CartItem.cart_item_id == cart_item_id)
    )
    return result.scalars().first()

async def add_cart_item(db: AsyncSession, cart_id: int, product_id: int, quantity: int, is_selected: bool = True, commit: bool = True):
    db_item = CartItem(cart_id=cart_id, product_id=product_id, quantity=quantity, is_selected=is_selected)
    db.add(db_item)
    if commit:
        await db.commit()
        await db.refresh(db_item)
    else:
        await db.flush()
    return db_item

async def update_cart_item(db: AsyncSession, db_item: CartItem, commit: bool = True):
    # Changes to db_item (like quantity or is_selected) are already mapped, just commit
    if commit:
        await db.commit()
        await db.refresh(db_item)
    else:
        await db.flush()
    return db_item

async def delete_cart_item(db: AsyncSession, db_item: CartItem):
    await db.delete(db_item)
    await db.commit()

async def empty_cart(db: AsyncSession, cart_id: int):
    # Delete all items where cart_id == cart_id
    result = await db.execute(select(CartItem).filter(CartItem.cart_id == cart_id))
    items = result.scalars().all()
    for item in items:
        await db.delete(item)
    await db.commit()

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, and_, desc
from sqlalchemy.orm import selectinload

from app.features.products.models import Product, ProductImage
from app.features.products.schemas import ProductCreate, ProductUpdate

async def get_product_by_id(db: AsyncSession, product_id: int):
    result = await db.execute(
        select(Product)
        .options(selectinload(Product.images))
        .filter(Product.product_id == product_id)
    )
    return result.scalars().first()

async def get_product_by_slug(db: AsyncSession, slug: str):
    result = await db.execute(
        select(Product)
        .options(selectinload(Product.images))
        .filter(Product.product_slug == slug)
    )
    return result.scalars().first()

async def get_product_by_exact_name(db: AsyncSession, name: str):
    # Helpful for slug generation fallback
    result = await db.execute(select(Product).filter(Product.product_name == name))
    return result.scalars().first()

async def get_products(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    keyword: str = None,
    category_id: int = None,
    is_featured: bool = None,
    status_filter: list[str] = None,
    vendor_filter: int = None,
    sort: str = "newest"
):
    query = select(Product).options(selectinload(Product.images))
    
    if keyword:
        query = query.filter(or_(
            Product.product_name.ilike(f"%{keyword}%"),
            Product.product_description.ilike(f"%{keyword}%")
        ))
        
    if category_id is not None:
        query = query.filter(Product.category_id == category_id)
        
    if is_featured is not None:
        query = query.filter(Product.is_featured == is_featured)
        
    # Advanced RBAC status filter
    if status_filter:
        query = query.filter(Product.product_status.in_(status_filter))
        
    # For Vendor viewing their own Inactive/Archived products (Usually handled by combining filters in service)
    # Actually, service layer will build a specific SQLAlchemy condition if needed, but we can pass an explicit vendor_id
    if vendor_filter is not None:
        query = query.filter(Product.vendor_id == vendor_filter)
        
    if sort == "newest":
        query = query.order_by(desc(Product.created_at))
    elif sort == "price_asc":
        query = query.order_by(Product.product_price.asc())
    elif sort == "price_desc":
        query = query.order_by(Product.product_price.desc())
        
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

async def get_products_with_custom_filter(db: AsyncSession, filter_condition, skip: int = 0, limit: int = 100, sort: str = "newest"):
    query = select(Product).options(selectinload(Product.images)).filter(filter_condition)
    
    if sort == "newest":
        query = query.order_by(desc(Product.created_at))
    elif sort == "price_asc":
        query = query.order_by(Product.product_price.asc())
    elif sort == "price_desc":
        query = query.order_by(Product.product_price.desc())
        
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def create_product(db: AsyncSession, product_in: ProductCreate, vendor_id: int, product_slug: str):
    db_product = Product(
        vendor_id=vendor_id,
        category_id=product_in.category_id,
        product_name=product_in.product_name,
        product_slug=product_slug,
        product_description=product_in.product_description,
        product_price=product_in.product_price,
        product_stock=product_in.product_stock,
        product_status=product_in.product_status
    )
    db.add(db_product)
    await db.commit()
    return await get_product_by_id(db, db_product.product_id)

async def update_product(db: AsyncSession, db_product: Product, update_data: ProductUpdate):
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(db_product, field, value)
    
    await db.commit()
    return await get_product_by_id(db, db_product.product_id)

async def delete_product_soft(db: AsyncSession, db_product: Product):
    db_product.product_status = 'Archived'
    await db.commit()
    return await get_product_by_id(db, db_product.product_id)

# --- Image Management ---

async def add_product_image(db: AsyncSession, product_id: int, image_url: str, is_primary: bool = False):
    img = ProductImage(product_id=product_id, image_url=image_url, is_primary=is_primary)
    db.add(img)
    await db.commit()
    await db.refresh(img)
    return img

async def get_product_image(db: AsyncSession, image_id: int):
    result = await db.execute(select(ProductImage).filter(ProductImage.product_image_id == image_id))
    return result.scalars().first()

async def get_primary_image(db: AsyncSession, product_id: int):
    result = await db.execute(select(ProductImage).filter(ProductImage.product_id == product_id, ProductImage.is_primary == True))
    return result.scalars().first()

async def get_first_product_image(db: AsyncSession, product_id: int):
    result = await db.execute(select(ProductImage).filter(ProductImage.product_id == product_id).limit(1))
    return result.scalars().first()

async def clear_primary_flag_for_product(db: AsyncSession, product_id: int):
    primary_img = await get_primary_image(db, product_id)
    if primary_img:
        primary_img.is_primary = False
        await db.commit()

async def delete_product_image(db: AsyncSession, db_image: ProductImage):
    await db.delete(db_image)
    await db.commit()

async def set_primary_image(db: AsyncSession, product_id: int, image_id: int):
    await clear_primary_flag_for_product(db, product_id)
    img = await get_product_image(db, image_id)
    if img:
        img.is_primary = True
        await db.commit()
    return img

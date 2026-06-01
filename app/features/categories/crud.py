from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func
from app.features.categories.models import Category
from app.features.categories.schemas import CategoryCreate, CategoryUpdate

async def get_category_by_name_and_parent(db: AsyncSession, name: str, parent_id: int | None):
    """Fetch a category by name and parent_id (case-insensitive) for duplicate checks."""
    stmt = select(Category).filter(func.lower(Category.category_name) == func.lower(name))
    if parent_id is None:
        stmt = stmt.filter(Category.parent_category_id.is_(None))
    else:
        stmt = stmt.filter(Category.parent_category_id == parent_id)
        
    result = await db.execute(stmt)
    return result.scalars().first()

async def get_category_by_id(db: AsyncSession, category_id: int):
    """Fetch a single category by ID, eager loading immediate subcategories."""
    stmt = select(Category).options(selectinload(Category.subcategories)).filter(Category.category_id == category_id)
    result = await db.execute(stmt)
    return result.scalars().first()

async def get_root_categories(db: AsyncSession, skip: int = 0, limit: int = 100):
    """Fetch root categories (no parent), eager loading their immediate subcategories."""
    stmt = (
        select(Category)
        .options(selectinload(Category.subcategories))
        .filter(Category.parent_category_id.is_(None))
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()

async def create_category(db: AsyncSession, category_in: CategoryCreate):
    db_category = Category(
        category_name=category_in.category_name,
        category_status=category_in.category_status,
        parent_category_id=category_in.parent_category_id
    )
    db.add(db_category)
    await db.commit()
    return await get_category_by_id(db, db_category.category_id)

async def update_category(db: AsyncSession, db_category: Category, category_in: CategoryUpdate):
    update_data = category_in.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_category, field, value)
        
    await db.commit()
    return await get_category_by_id(db, db_category.category_id)

async def delete_category(db: AsyncSession, db_category: Category):
    await db.delete(db_category)
    await db.commit()

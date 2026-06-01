from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.features.categories import crud, schemas

async def get_all_root_categories(db: AsyncSession, skip: int = 0, limit: int = 100):
    return await crud.get_root_categories(db, skip=skip, limit=limit)

async def get_category(db: AsyncSession, category_id: int):
    category = await crud.get_category_by_id(db, category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category

async def create_category(db: AsyncSession, category_in: schemas.CategoryCreate):
    # 1. Check parent exists if specified
    if category_in.parent_category_id:
        parent = await crud.get_category_by_id(db, category_in.parent_category_id)
        if not parent:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent category not found")

    # 2. Check for duplicates
    existing = await crud.get_category_by_name_and_parent(db, category_in.category_name, category_in.parent_category_id)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A category with this name already exists under the specified parent")

    return await crud.create_category(db, category_in)

async def update_category(db: AsyncSession, category_id: int, category_in: schemas.CategoryUpdate):
    category = await crud.get_category_by_id(db, category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    # Check for duplicates if name or parent changes
    new_name = category_in.category_name if category_in.category_name is not None else category.category_name
    
    # Notice we check if the field was actually provided in the request
    # If parent_category_id was not provided, it keeps the old one.
    if category_in.parent_category_id is not Ellipsis: # We don't have Unset type, check if passed
        new_parent_id = category_in.parent_category_id
    else:
        new_parent_id = category.parent_category_id

    # Wait, in Pydantic, unset fields are None if Optional is used, but we need to know if it was explicitly sent as None
    update_data = category_in.model_dump(exclude_unset=True)
    if "parent_category_id" in update_data:
        new_parent_id = update_data["parent_category_id"]
    else:
        new_parent_id = category.parent_category_id
        
    if "category_name" in update_data or "parent_category_id" in update_data:
        existing = await crud.get_category_by_name_and_parent(db, new_name, new_parent_id)
        if existing and existing.category_id != category_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A category with this name already exists under the specified parent")

    # Circular dependency check
    if "parent_category_id" in update_data and new_parent_id is not None:
        if new_parent_id == category_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A category cannot be its own parent")
            
        # Check upward traversal to prevent deep circular refs
        curr_parent_id = new_parent_id
        while curr_parent_id:
            curr_parent = await crud.get_category_by_id(db, curr_parent_id)
            if not curr_parent:
                break
            if curr_parent.category_id == category_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Circular reference detected: Cannot set a descendant as a parent")
            curr_parent_id = curr_parent.parent_category_id

    return await crud.update_category(db, category, category_in)

async def delete_category(db: AsyncSession, category_id: int):
    category = await crud.get_category_by_id(db, category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        
    if category.subcategories and len(category.subcategories) > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Cannot delete category because it has subcategories. Move or delete them first."
        )
        
    await crud.delete_category(db, category)
    return {"message": "Category deleted successfully"}

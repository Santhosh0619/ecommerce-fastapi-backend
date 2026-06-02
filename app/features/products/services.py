import os
import uuid
import re
from fastapi import HTTPException, status, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_, and_
from sqlalchemy.exc import IntegrityError

from app.features.products import crud, schemas
from app.features.categories import crud as category_crud
from app.features.roles.crud import get_user_roles_names

# Slug generation
def generate_slug(name: str) -> str:
    # Lowercase, replace non-alphanumeric with hyphens
    slug_base = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    # Append short uuid (6 chars)
    short_uuid = str(uuid.uuid4())[:6]
    return f"{slug_base}-{short_uuid}"

async def get_products_with_rbac(
    db: AsyncSession, 
    user_id: int | None, 
    skip: int, limit: int, 
    keyword: str, category_id: int, is_featured: bool, sort: str
):
    """Handles visibility rules based on the user's role."""
    
    # 1. Base query condition list
    conditions = []
    
    if keyword:
        conditions.append(
            or_(
                crud.Product.product_name.ilike(f"%{keyword}%"),
                crud.Product.product_description.ilike(f"%{keyword}%")
            )
        )
    if category_id is not None:
        conditions.append(crud.Product.category_id == category_id)
    if is_featured is not None:
        conditions.append(crud.Product.is_featured == is_featured)
        
    # 2. RBAC Visibility Condition
    if user_id is None:
        # Unauthenticated: Only Active
        conditions.append(crud.Product.product_status == 'Active')
    else:
        roles = await get_user_roles_names(db, user_id)
        if "Admin" in roles:
            # Admins see everything. No status filter added.
            pass
        elif "Vendor" in roles:
            # Vendor sees globally Active, PLUS their own Inactive/Archived
            conditions.append(
                or_(
                    crud.Product.product_status == 'Active',
                    crud.Product.vendor_id == user_id
                )
            )
        else:
            # Customer sees only Active
            conditions.append(crud.Product.product_status == 'Active')
            
    final_condition = and_(*conditions) if conditions else and_(True)
    
    return await crud.get_products_with_custom_filter(
        db, 
        filter_condition=final_condition, 
        skip=skip, 
        limit=limit, 
        sort=sort
    )

async def get_product_by_slug_with_rbac(db: AsyncSession, slug: str, user_id: int | None):
    product = await crud.get_product_by_slug(db, slug)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        
    # Visibility checks
    if product.product_status != 'Active':
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
            
        roles = await get_user_roles_names(db, user_id)
        if "Admin" not in roles and product.vendor_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
            
    return product

async def create_product(db: AsyncSession, product_in: schemas.ProductCreate, vendor_id: int):
    # Verify category exists
    category = await category_crud.get_category_by_id(db, product_in.category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        
    for attempt in range(3):
        slug = generate_slug(product_in.product_name)
        try:
            return await crud.create_product(db, product_in, vendor_id, slug)
        except IntegrityError:
            await db.rollback()
            if attempt == 2:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Could not generate unique product slug. Please try again.")

async def update_product(db: AsyncSession, product_id: int, update_data: schemas.ProductUpdate, user_id: int):
    product = await crud.get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        
    # Check Ownership
    roles = await get_user_roles_names(db, user_id)
    if "Admin" not in roles and product.vendor_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only modify your own products")
        
    if update_data.category_id is not None:
        cat = await category_crud.get_category_by_id(db, update_data.category_id)
        if not cat:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
            
    # Admin only field: is_featured
    if update_data.is_featured is not None and "Admin" not in roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only Admins can feature products")
        
    return await crud.update_product(db, product, update_data)

async def delete_product(db: AsyncSession, product_id: int, user_id: int):
    product = await crud.get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        
    roles = await get_user_roles_names(db, user_id)
    if "Admin" not in roles and product.vendor_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only delete your own products")
        
    return await crud.delete_product_soft(db, product)

# --- Images ---
UPLOAD_DIR = "uploads/products"
MAX_FILE_SIZE = 5 * 1024 * 1024 # 5MB
ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"]

async def upload_product_image(db: AsyncSession, product_id: int, file: UploadFile, is_primary: bool, user_id: int):
    product = await crud.get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        
    roles = await get_user_roles_names(db, user_id)
    if "Admin" not in roles and product.vendor_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only modify your own products")
        
    # File Validation
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file type. Only JPEG, PNG, and WebP are allowed.")
        
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File too large. Maximum size is 5MB.")
        
    # Ensure directory exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    # Generate unique filename
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    filename = f"{uuid.uuid4().hex}.{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    # Save physical file
    with open(file_path, "wb") as f:
        f.write(content)
        
    image_url = f"/static/uploads/products/{filename}"
    
    # Handle primary flag
    if is_primary:
        await crud.clear_primary_flag_for_product(db, product_id)
    else:
        # If no primary image exists, make this one primary automatically
        existing_primary = await crud.get_primary_image(db, product_id)
        if not existing_primary:
            is_primary = True
            
    return await crud.add_product_image(db, product_id, image_url, is_primary)

async def delete_product_image(db: AsyncSession, product_id: int, image_id: int, user_id: int):
    product = await crud.get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        
    roles = await get_user_roles_names(db, user_id)
    if "Admin" not in roles and product.vendor_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only modify your own products")
        
    image = await crud.get_product_image(db, image_id)
    if not image or image.product_id != product_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
        
    # Physical File Cleanup
    # image_url is like "/static/uploads/products/123.jpg", we need to map it back to local path "uploads/products/123.jpg"
    local_path = image.image_url.replace("/static/", "")
    if os.path.exists(local_path):
        os.remove(local_path)
        
    # DB Delete
    await crud.delete_product_image(db, image)
    
    # If we deleted the primary image, randomly assign a new primary if there are remaining images
    if image.is_primary:
        next_image = await crud.get_first_product_image(db, product_id)
        if next_image:
            next_image.is_primary = True
            await db.commit()
            
    return None

async def set_product_primary_image(db: AsyncSession, product_id: int, image_id: int, user_id: int):
    product = await crud.get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        
    roles = await get_user_roles_names(db, user_id)
    if "Admin" not in roles and product.vendor_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only modify your own products")
        
    img = await crud.get_product_image(db, image_id)
    if not img or img.product_id != product_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
        
    await crud.set_primary_image(db, product_id, image_id)
    return {"message": "Primary image updated successfully"}

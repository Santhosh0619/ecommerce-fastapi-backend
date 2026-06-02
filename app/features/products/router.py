from fastapi import APIRouter, Depends, status, Query, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database.session import get_db
from app.features.products import schemas, services
from app.features.auth.dependencies import get_current_user, get_optional_current_user, RequireRole
from app.features.users.models import User
from app.features.auth.dependencies import RequireRole

router = APIRouter(prefix="/products", tags=["Products"])

# Dependency instances
allow_vendor_admin = RequireRole(["Vendor", "Admin"])

@router.get("/", response_model=list[schemas.ProductResponse])
async def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    keyword: Optional[str] = Query(None, description="Search name or description"),
    category_id: Optional[int] = Query(None, description="Filter by category"),
    is_featured: Optional[bool] = Query(None, description="Filter featured products"),
    sort: str = Query("newest", description="Sort by: newest, price_asc, price_desc"),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user)
):
    """
    List products with advanced filters.
    Visibility depends on user role (Customers see Active, Vendors see own + Active, Admins see all).
    """
    user_id = current_user.user_id if current_user else None
    return await services.get_products_with_rbac(
        db, user_id, skip, limit, keyword, category_id, is_featured, sort
    )

@router.get("/{slug}", response_model=schemas.ProductResponse)
async def get_product(
    slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user)
):
    """Get single product by SEO slug."""
    user_id = current_user.user_id if current_user else None
    return await services.get_product_by_slug_with_rbac(db, slug, user_id)

@router.post("/", response_model=schemas.ProductResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(allow_vendor_admin)])
async def create_product(
    product_in: schemas.ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Vendor or Admin can create a new product."""
    return await services.create_product(db, product_in, vendor_id=current_user.user_id)

@router.put("/{product_id}", response_model=schemas.ProductResponse, dependencies=[Depends(allow_vendor_admin)])
async def update_product(
    product_id: int,
    update_data: schemas.ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Vendor (own) or Admin can update a product."""
    return await services.update_product(db, product_id, update_data, current_user.user_id)

@router.delete("/{product_id}", response_model=schemas.ProductResponse, dependencies=[Depends(allow_vendor_admin)])
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Vendor (own) or Admin can soft delete a product."""
    return await services.delete_product(db, product_id, current_user.user_id)

# --- Images ---

@router.post("/{product_id}/images", response_model=schemas.ProductImageResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(allow_vendor_admin)])
async def upload_product_image(
    product_id: int,
    file: UploadFile = File(...),
    is_primary: bool = Form(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload a multipart/form-data image for a product."""
    return await services.upload_product_image(db, product_id, file, is_primary, current_user.user_id)

@router.delete("/{product_id}/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(allow_vendor_admin)])
async def delete_product_image(
    product_id: int,
    image_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a product image (also removes physical file)."""
    await services.delete_product_image(db, product_id, image_id, current_user.user_id)

@router.put("/{product_id}/images/{image_id}/primary", dependencies=[Depends(allow_vendor_admin)])
async def set_product_primary_image(
    product_id: int,
    image_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Set an existing image as the primary image for the product."""
    return await services.set_product_primary_image(db, product_id, image_id, current_user.user_id)

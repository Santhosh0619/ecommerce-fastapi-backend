from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database.session import get_db
from app.features.vendors import schemas, services
from app.features.auth.dependencies import get_current_user, RequireRole
from app.features.users.models import User

router = APIRouter(prefix="/vendors", tags=["Vendors"])

@router.post("/apply", response_model=schemas.VendorApplicationResponse, status_code=status.HTTP_201_CREATED)
async def submit_vendor_application(app_data: schemas.VendorApplicationCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Customer submits an application to become a vendor."""
    return await services.apply_for_vendor(db, current_user.user_id, app_data)

@router.get("/applications", response_model=List[schemas.VendorApplicationResponse], dependencies=[Depends(RequireRole(["Admin"]))])
async def list_vendor_applications(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """Admin views all pending or past applications."""
    from app.features.vendors import crud
    return await crud.get_all_applications(db, skip=skip, limit=limit)

@router.put("/applications/{application_id}/status", response_model=schemas.VendorApplicationResponse)
async def review_application(application_id: int, review_data: schemas.VendorApplicationUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(RequireRole(["Admin"]))):
    """Admin approves or rejects an application."""
    return await services.review_vendor_application(db, application_id, current_user.user_id, review_data)

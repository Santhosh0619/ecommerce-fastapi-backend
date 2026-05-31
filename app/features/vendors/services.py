from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.features.vendors import crud, schemas
from app.features.roles import crud as roles_crud

async def apply_for_vendor(db: AsyncSession, user_id: int, app_data: schemas.VendorApplicationCreate):
    return await crud.create_application(db, user_id, app_data)

async def review_vendor_application(db: AsyncSession, application_id: int, admin_user_id: int, review_data: schemas.VendorApplicationUpdate):
    if review_data.status not in ["approved", "rejected"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Status must be 'approved' or 'rejected'")
    
    app = await crud.get_application(db, application_id)
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
        
    updated_app = await crud.update_application_status(db, application_id, review_data.status, admin_user_id, review_data.rejection_reason)
    
    if review_data.status == "approved":
        # Get the Vendor role ID
        vendor_role = await roles_crud.get_role_by_name(db, "Vendor")
        if vendor_role:
            # Import users crud locally to avoid circular imports
            from app.features.users import crud as users_crud
            # Assign Vendor role to the user who applied
            await users_crud.assign_role_to_user(db, user_id=updated_app.user_id, role_id=vendor_role.role_id)
            
    return updated_app

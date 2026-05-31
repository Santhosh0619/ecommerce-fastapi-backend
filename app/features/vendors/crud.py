from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timezone
from app.features.vendors.models import VendorApplication
from app.features.vendors.schemas import VendorApplicationCreate

async def create_application(db: AsyncSession, user_id: int, app_data: VendorApplicationCreate):
    db_app = VendorApplication(
        user_id=user_id,
        store_name=app_data.store_name,
        business_details=app_data.business_details,
        status="pending"
    )
    db.add(db_app)
    await db.commit()
    await db.refresh(db_app)
    return db_app

async def get_application(db: AsyncSession, application_id: int):
    result = await db.execute(select(VendorApplication).filter(VendorApplication.application_id == application_id))
    return result.scalars().first()

async def get_all_applications(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(VendorApplication).offset(skip).limit(limit))
    return result.scalars().all()

async def update_application_status(db: AsyncSession, application_id: int, status: str, admin_user_id: int, rejection_reason: str = None):
    app = await get_application(db, application_id)
    if app:
        app.status = status
        app.reviewed_by = admin_user_id
        app.reviewed_at = datetime.now(timezone.utc)
        if rejection_reason:
            app.rejection_reason = rejection_reason
        await db.commit()
        await db.refresh(app)
    return app

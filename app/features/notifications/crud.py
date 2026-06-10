from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Optional, Sequence
from .models import Notification

async def get_user_notifications(db: AsyncSession, user_id: int, skip: int = 0, limit: int = 50) -> Sequence[Notification]:
    """Fetch notifications for a user, ordered by newest first."""
    stmt = (
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_notification_by_id(db: AsyncSession, notification_id: int, user_id: Optional[int] = None) -> Optional[Notification]:
    """Fetch a specific notification by its ID."""
    stmt = select(Notification).where(Notification.notification_id == notification_id)
    if user_id is not None:
        stmt = stmt.where(Notification.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalars().first()

async def mark_notification_as_read(db: AsyncSession, notification_id: int, user_id: int) -> Optional[Notification]:
    """Mark a notification as read, ensuring it belongs to the requesting user."""
    stmt = (
        update(Notification)
        .where(Notification.notification_id == notification_id)
        .where(Notification.user_id == user_id)
        .values(is_read=True)
    )
    await db.execute(stmt)
    await db.commit()
    
    # Return updated notification, ensuring we only return it if it belongs to the user
    return await get_notification_by_id(db, notification_id, user_id)

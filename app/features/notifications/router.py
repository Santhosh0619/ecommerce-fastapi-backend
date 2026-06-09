from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Sequence
import typing

from app.database.session import get_db
from app.features.auth.dependencies import get_current_user
from app.features.users.models import User
from . import crud
from .schemas import NotificationResponse

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("/", response_model=list[NotificationResponse])
async def get_my_notifications(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fetch the notification history for the currently authenticated user (Customer/Vendor/Admin).
    Ordered by newest first.
    """
    uid = typing.cast(int, current_user.user_id)
    return await crud.get_user_notifications(db=db, user_id=uid, skip=skip, limit=limit)

@router.put("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mark a specific notification as read.
    """
    uid = typing.cast(int, current_user.user_id)
    notification = await crud.mark_notification_as_read(db=db, notification_id=notification_id, user_id=uid)
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found or does not belong to the user"
        )
    return notification

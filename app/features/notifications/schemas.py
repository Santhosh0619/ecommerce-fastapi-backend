from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
from .models import NotificationType, DeliveryStatus

class NotificationResponse(BaseModel):
    notification_id: int
    notification_type: NotificationType
    user_id: int
    title: str
    message: str
    metadata_json: Optional[Dict[str, Any]] = None
    is_read: bool
    delivery_status: DeliveryStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

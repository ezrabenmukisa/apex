import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.core.dependencies import get_current_user
from app.schemas.notification import (
    DeviceTokenCreate,
    DeviceTokenResponse,
    NotificationUpdate,
    NotificationResponse,
    NotificationListResponse,
)
from app.services.notification import (
    upsert_device_token,
    get_user_notifications,
    update_notification_read_status,
)

router = APIRouter(tags=["Notifications & Devices"])


@router.put("/devices/push-token", response_model=DeviceTokenResponse, summary="Register or update FCM push token")
def register_push_token(
    payload: DeviceTokenCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    upsert_device_token(db=db, user_id=current_user.user_id, payload=payload)
    return DeviceTokenResponse(message="Push token successfully registered.", fcm_token=payload.fcm_token)


@router.get("/notifications", response_model=NotificationListResponse, summary="List user notifications")
def list_notifications(
    unread_only: bool = Query(False, description="Filter for unread notifications only"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = get_user_notifications(db=db, user_id=current_user.user_id, unread_only=unread_only)
    return NotificationListResponse(items=[NotificationResponse.model_validate(n) for n in rows])


@router.patch("/notifications/{notification_id}", response_model=NotificationResponse, summary="Mark notification read state")
def update_notification_status(
    notification_id: uuid.UUID,
    payload: NotificationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notification = update_notification_read_status(
        db=db, notification_id=notification_id, user_id=current_user.user_id, payload=payload
    )
    if not notification:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Notification not found.")
    return notification

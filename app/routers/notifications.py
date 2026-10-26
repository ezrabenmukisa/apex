import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.core.dependencies import get_current_user
from app.schemas import (
    DeviceTokenCreate,
    DeviceTokenResponse,
    NotificationUpdate,
    NotificationResponse
)
from app.services.notification import (
    upsert_device_token,
    get_user_notifications,
    update_notification_read_status
)

router = APIRouter(tags=["Notifications & Devices"])


@router.put("/devices/push-token", response_model=DeviceTokenResponse, status_code=status.HTTP_200_OK, summary="Register or update FCM push token")
def register_push_token(
    payload: DeviceTokenCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    upsert_device_token(db=db, user_id=current_user.user_id, payload=payload)
    return DeviceTokenResponse(
        message="Push token successfully registered.",
        fcm_token=payload.fcm_token
    )


@router.get("/notifications", response_model=list[NotificationResponse], status_code=status.HTTP_200_OK, summary="List user notifications")
def list_notifications(
    unread_only: bool = Query(False, description="Filter for unread notifications only"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_user_notifications(db=db, user_id=current_user.user_id, unread_only=unread_only)


@router.patch("/notifications/{notification_id}", response_model=NotificationResponse, status_code=status.HTTP_200_OK, summary="Mark notification read state")
def update_notification_status(
    notification_id: uuid.UUID,
    payload: NotificationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notification = update_notification_read_status(
        db=db,
        notification_id=notification_id,
        user_id=current_user.user_id,
        payload=payload
    )

    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")

    return notification
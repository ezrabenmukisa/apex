import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.models.notification import DevicePlatform


class DeviceTokenCreate(BaseModel):
    fcm_token: str = Field(..., min_length=1, description="Firebase Cloud Messaging device token")
    platform: DevicePlatform


class DeviceTokenResponse(BaseModel):
    message: str
    fcm_token: str

    model_config = ConfigDict(from_attributes=True)


class NotificationUpdate(BaseModel):
    is_read: bool


class NotificationResponse(BaseModel):
    notification_id: uuid.UUID
    title: str
    body: str
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
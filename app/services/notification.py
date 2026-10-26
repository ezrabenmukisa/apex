import uuid
from sqlalchemy.orm import Session
from firebase_admin import messaging, exceptions

from app.models.notification import DeviceToken, Notification
from app.schemas.notification import DeviceTokenCreate, NotificationUpdate


def upsert_device_token(db: Session, user_id: uuid.UUID, payload: DeviceTokenCreate) -> DeviceToken:
    existing_token = db.query(DeviceToken).filter(DeviceToken.fcm_token == payload.fcm_token).first()

    if existing_token:
        existing_token.user_id = user_id
        existing_token.platform = payload.platform
        db.commit()
        db.refresh(existing_token)
        return existing_token
    else:
        new_token = DeviceToken(
            user_id=user_id,
            fcm_token=payload.fcm_token,
            platform=payload.platform
        )
        db.add(new_token)
        db.commit()
        db.refresh(new_token)
        return new_token


def create_and_send_notification(
    db: Session, 
    user_id: uuid.UUID, 
    title: str, 
    body: str
) -> Notification:
    # 1. Save notification to the database for the in-app notification list
    notification = Notification(
        user_id=user_id,
        title=title,
        body=body,
        is_read=False
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)

    # 2. Fetch the user's active device token(s) to push the alert
    device_tokens = db.query(DeviceToken).filter(DeviceToken.user_id == user_id).all()

    for device in device_tokens:
        try:
            message = messaging.Message(
                notification=messaging.Notification(title=title, body=body),
                token=device.fcm_token,
            )
            messaging.send(message)
        except exceptions.InvalidArgumentError:
            # Token is invalid or expired; you can optionally clean it up here
            pass
        except Exception as e:
            # Log failure silently so it doesn't break the main API transaction
            print(f"FCM push failed for token {device.fcm_token}: {e}")

    return notification


def get_user_notifications(db: Session, user_id: uuid.UUID, unread_only: bool = False) -> list[Notification]:
    query = db.query(Notification).filter(Notification.user_id == user_id)
    
    if unread_only:
        query = query.filter(Notification.is_read == False)

    return query.order_by(Notification.created_at.desc()).all()


def update_notification_read_status(
    db: Session, 
    notification_id: uuid.UUID, 
    user_id: uuid.UUID, 
    payload: NotificationUpdate
) -> Notification | None:
    notification = db.query(Notification).filter(
        Notification.notification_id == notification_id,
        Notification.user_id == user_id
    ).first()

    if not notification:
        return None

    notification.is_read = payload.is_read
    db.commit()
    db.refresh(notification)
    return notification
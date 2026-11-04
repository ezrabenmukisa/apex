import uuid
import logging
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session
from firebase_admin import messaging

from app.database import SessionLocal
from app.models.notification import DeviceToken, Notification
from app.schemas.notification import DeviceTokenCreate, NotificationUpdate

logger = logging.getLogger(__name__)


def upsert_device_token(db: Session, user_id: uuid.UUID, payload: DeviceTokenCreate) -> DeviceToken:
    existing_token = db.query(DeviceToken).filter(DeviceToken.fcm_token == payload.fcm_token).first()

    if existing_token:
        existing_token.user_id = user_id          # token moves to whoever signed in on this device last
        existing_token.platform = payload.platform
        db.commit()
        db.refresh(existing_token)
        return existing_token

    new_token = DeviceToken(user_id=user_id, fcm_token=payload.fcm_token, platform=payload.platform)
    db.add(new_token)
    db.commit()
    db.refresh(new_token)
    return new_token


def _delete_dead_tokens(tokens: list[str]) -> None:
    with SessionLocal() as db:
        db.query(DeviceToken).filter(DeviceToken.fcm_token.in_(tokens)).delete(synchronize_session=False)
        db.commit()


def send_push(tokens: list[str], title: str, body: str) -> None:
    """Runs AFTER the response is sent (BackgroundTasks), so FCM latency never blocks the API call."""
    dead = []
    for token in tokens:
        try:
            messaging.send(messaging.Message(notification=messaging.Notification(title=title, body=body), token=token))
        except messaging.UnregisteredError:
            dead.append(token)               # app uninstalled / token expired
        except Exception:
            logger.exception("FCM push failed")
    if dead:
        _delete_dead_tokens(dead)


def notify_users(
    db: Session,
    background_tasks: BackgroundTasks,
    user_ids: list[uuid.UUID],
    title: str,
    body: str,
) -> None:
    """Saves an in-app notification row per user now; pushes to their devices in the background."""
    unique_ids = list(set(user_ids))
    if not unique_ids:
        return

    db.add_all([Notification(user_id=uid, title=title, body=body, is_read=False) for uid in unique_ids])
    db.commit()

    tokens = [t for (t,) in db.query(DeviceToken.fcm_token).filter(DeviceToken.user_id.in_(unique_ids)).all()]
    if tokens:
        background_tasks.add_task(send_push, tokens, title, body)


def get_user_notifications(db: Session, user_id: uuid.UUID, unread_only: bool = False) -> list[Notification]:
    query = db.query(Notification).filter(Notification.user_id == user_id)
    if unread_only:
        query = query.filter(Notification.is_read.is_(False))
    return query.order_by(Notification.created_at.desc()).all()


def update_notification_read_status(
    db: Session,
    notification_id: uuid.UUID,
    user_id: uuid.UUID,
    payload: NotificationUpdate,
) -> Notification | None:
    notification = db.query(Notification).filter(
        Notification.notification_id == notification_id,
        Notification.user_id == user_id,
    ).first()
    if not notification:
        return None

    notification.is_read = payload.is_read
    db.commit()
    db.refresh(notification)
    return notification

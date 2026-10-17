import uuid
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserProfileUpdate


def get_user_by_id(db: Session, user_id: uuid.UUID) -> User | None:
    return db.query(User).filter(User.user_id == user_id).first()


def get_user_by_firebase_uid(db: Session, firebase_uid: str) -> User | None:
    return db.query(User).filter(User.firebase_uid == firebase_uid).first()


def create_user_from_firebase(
    db: Session,
    firebase_uid: str,
    contact_phone: str | None = None,
    contact_email: str | None = None
) -> User:
    user = User(
        firebase_uid=firebase_uid,
        first_name="",
        middle_name=None,
        last_name="",
        contact_email=contact_email,
        contact_phone=contact_phone,
        profile_complete=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user_profile(
    db: Session,
    user: User,
    profile_data: UserProfileUpdate
) -> User:
    if profile_data.first_name is not None:
        user.first_name = profile_data.first_name
    if profile_data.middle_name is not None:
        user.middle_name = profile_data.middle_name
    if profile_data.last_name is not None:
        user.last_name = profile_data.last_name
    if profile_data.contact_email is not None:
        user.contact_email = profile_data.contact_email
    if profile_data.contact_phone is not None:
        user.contact_phone = profile_data.contact_phone

    user.profile_complete = bool(user.first_name.strip() and user.last_name.strip())

    db.commit()
    db.refresh(user)
    return user
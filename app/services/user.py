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


def update_user_profile(db: Session, user: User, profile_data: UserProfileUpdate) -> User:
    for field, value in profile_data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)

    # contact_email is required, so the profile is not complete without it
    user.profile_complete = bool(
        user.first_name and user.first_name.strip()
        and user.last_name and user.last_name.strip()
        and user.contact_email and user.contact_email.strip()
    )
    db.commit()
    db.refresh(user)
    return user

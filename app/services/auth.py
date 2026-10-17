from sqlalchemy.orm import Session
from app.core.security import verify_firebase_token
from app.services.user import create_user_from_firebase, get_user_by_firebase_uid

def sync_firebase_user(db: Session, id_token: str) -> tuple:
    # 1. Decode & verify token claims from Firebase
    decoded = verify_firebase_token(id_token)
    firebase_uid = decoded["uid"]
    contact_phone = decoded.get("phone_number")
    contact_email = decoded.get("email")

    # 2. Check if user already exists
    user = get_user_by_firebase_uid(db, firebase_uid)

    # 3. Create user if first-time login
    if user is None:
        user = create_user_from_firebase(
            db=db,
            firebase_uid=firebase_uid,
            contact_phone=contact_phone,
            contact_email=contact_email
        )

    # Check profile completion using first_name and last_name fields
    profile_complete = bool(user.first_name and user.first_name.strip() and user.last_name and user.last_name.strip())

    return user, profile_complete
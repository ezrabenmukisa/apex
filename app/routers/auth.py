import logging
from fastapi import APIRouter, Depends, HTTPException, status
from firebase_admin import auth as firebase_auth_admin
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import FirebaseAuthRequest, FirebaseAuthResponse
from app.services.auth import sync_firebase_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/firebase", summary="Authenticate via Firebase ID Token")
def authenticate_firebase(payload: FirebaseAuthRequest, db: Session = Depends(get_db))-> FirebaseAuthResponse:
    try:
        user, profile_complete = sync_firebase_user(db=db, id_token=payload.id_token)
    except (firebase_auth_admin.InvalidIdTokenError, ValueError) as error:
        logger.warning(
            "Firebase token verification failed: %s: %s",
            type(error).__name__,
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Firebase sign-in token."
        ) from error

    return {
        "user_id": user.user_id,
        "profile_complete": profile_complete
    }

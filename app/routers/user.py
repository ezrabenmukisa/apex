from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.core.dependencies import get_current_user
from app.schemas import UserProfileResponse, UserProfileUpdate
from app.services.user import update_user_profile

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", summary="Get signed-in user's profile")
def get_my_profile(current_user: User = Depends(get_current_user)) -> UserProfileResponse:
    return current_user


@router.patch("/me", summary="Update editable profile fields")
def update_my_profile(
    payload: UserProfileUpdate, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> UserProfileResponse:
    updated_user = update_user_profile(db=db, user=current_user, profile_data=payload)
    return updated_user
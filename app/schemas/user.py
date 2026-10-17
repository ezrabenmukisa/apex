import uuid
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserProfileResponse(BaseModel):
    user_id: uuid.UUID
    first_name: str
    middle_name: str | None = None
    last_name: str
    contact_email: str | None = None
    contact_phone: str | None = None

    model_config = ConfigDict(from_attributes=True)


class UserProfileUpdate(BaseModel):
    first_name: str | None = Field(None, min_length=1, max_length=255)
    middle_name: str | None = Field(None, max_length=255)
    last_name: str | None = Field(None, min_length=1, max_length=255)
    contact_email: EmailStr | None = None
    contact_phone: str | None = Field(None, max_length=20)
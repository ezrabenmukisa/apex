import uuid
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, EmailStr, field_validator
from app.models.enums import ProjectStatus, UserRole, InvitationStatus
from app.schemas.common import Money


class ProjectCreate(BaseModel):
    project_name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    location_name: str = Field(..., min_length=1)
    planned_budget: Decimal | None = Field(None, ge=0)
    currency: str | None = None
    target_completion_date: date | None = None


class ProjectUpdate(BaseModel):
    project_name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)
    location_name: str | None = Field(None, min_length=1)
    planned_budget: Decimal | None = Field(None, ge=0)
    currency: str | None = None
    target_completion_date: date | None = None
    status: ProjectStatus | None = None

    @field_validator("project_name", "latitude", "longitude", "location_name", "status")
    @classmethod
    def not_null(cls, v):
        if v is None:
            raise ValueError("cannot be null")
        return v


class ProjectResponse(BaseModel):
    project_id: uuid.UUID
    project_name: str
    description: str | None = None
    latitude: float
    longitude: float
    location_name: str
    planned_budget: Money | None = None
    currency: str | None = None
    target_completion_date: date | None = None
    status: ProjectStatus
    created_at: datetime
    current_user_role: UserRole | None = None

    model_config = ConfigDict(from_attributes=True)


class ProjectListResponse(BaseModel):
    items: list[ProjectResponse]


class ProjectMemberResponse(BaseModel):
    project_id: uuid.UUID
    user_id: uuid.UUID
    user_role: UserRole
    first_name: str
    last_name: str
    contact_email: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ProjectInvitationCreate(BaseModel):
    contact_email: EmailStr
    user_role: UserRole
    message: str = Field(..., min_length=1)


class ProjectInvitationAccept(BaseModel):
    token: str


class ProjectInvitationAcceptResponse(BaseModel):
    message: str
    project_id: uuid.UUID


class ProjectInvitationResponse(BaseModel):
    invitation_id: uuid.UUID
    project_id: uuid.UUID
    email: str
    user_role: UserRole
    status: InvitationStatus
    expires_at: datetime

    model_config = ConfigDict(from_attributes=True)

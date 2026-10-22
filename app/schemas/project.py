import uuid
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, EmailStr
from app.models.enums import ProjectStatus, UserRole, InvitationStatus


class ProjectCreate(BaseModel):
    project_name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    latitude: float
    longitude: float
    location_name: str = Field(..., min_length=1)
    planned_budget: Decimal | None = None
    currency: str | None = None
    target_completion_date: date | None = None


class ProjectUpdate(BaseModel):
    project_name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    location_name: str | None = None
    planned_budget: Decimal | None = None
    currency: str | None = None
    target_completion_date: date | None = None
    status: ProjectStatus | None = None


class ProjectResponse(BaseModel):
    project_id: uuid.UUID
    project_name: str
    description: str | None = None
    latitude: float
    longitude: float
    location_name: str
    planned_budget: Decimal | None = None
    currency: str | None = None
    target_completion_date: date | None = None
    status: ProjectStatus
    created_at: datetime
    current_user_role: UserRole | None = None

    model_config = ConfigDict(from_attributes=True)


class ProjectMemberResponse(BaseModel):
    project_id: uuid.UUID
    user_id: uuid.UUID
    user_role: UserRole

    model_config = ConfigDict(from_attributes=True)


class ProjectInvitationCreate(BaseModel):
    email: EmailStr
    user_role: UserRole

class ProjectInvitationAccept(BaseModel):
    token: str

class ProjectInvitationResponse(BaseModel):
    invitation_id: uuid.UUID
    project_id: uuid.UUID
    email: str
    user_role: UserRole
    status: InvitationStatus
    expires_at: datetime

    model_config = ConfigDict(from_attributes=True)

import uuid
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import MilestoneStatus

class MilestoneCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    sequence: int = Field(..., ge=0)
    description: str | None = None
    start_date: date
    due_date: date | None = None
    planned_budget: Decimal | None = Field(None, ge=0)

class MilestoneUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    sequence: int | None = Field(None, ge=0)
    description: str | None = None
    start_date: date | None = None
    due_date: date | None = None
    planned_budget: Decimal | None = Field(None, ge=0)
    status: MilestoneStatus | None = None

class MilestoneResponse(BaseModel):
    milestone_id: uuid.UUID
    project_id: uuid.UUID
    title: str
    sequence: int
    description: str | None = None
    start_date: date
    due_date: date | None = None
    planned_budget: Decimal | None = None
    status: MilestoneStatus

    model_config = ConfigDict(from_attributes=True)
import uuid
from datetime import date
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from app.models.enums import MilestoneStatus
from app.schemas.common import Money


class MilestoneCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    sequence: int = Field(..., ge=0)
    description: str | None = None
    start_date: date
    due_date: date | None = None
    planned_budget: Decimal | None = Field(None, ge=0)

    @model_validator(mode="after")
    def due_not_before_start(self):
        if self.due_date and self.due_date < self.start_date:
            raise ValueError("due_date cannot be before start_date")
        return self


class MilestoneUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    sequence: int | None = Field(None, ge=0)
    description: str | None = None
    start_date: date | None = None
    due_date: date | None = None
    planned_budget: Decimal | None = Field(None, ge=0)
    status: MilestoneStatus | None = None

    @field_validator("title", "sequence", "start_date", "status")
    @classmethod
    def not_null(cls, v):
        if v is None:
            raise ValueError("cannot be null")
        return v


class MilestoneResponse(BaseModel):
    milestone_id: uuid.UUID
    project_id: uuid.UUID
    title: str
    sequence: int
    description: str | None = None
    start_date: date
    due_date: date | None = None
    planned_budget: Money | None = None
    status: MilestoneStatus

    model_config = ConfigDict(from_attributes=True)


class MilestoneListResponse(BaseModel):
    items: list[MilestoneResponse]

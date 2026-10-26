import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field
from app.models.enums import EvidenceStatus, ReviewDecision


class EvidenceCreate(BaseModel):
    description: str = Field(..., min_length=1)
    captured_latitude: Decimal
    captured_longitude: Decimal
    captured_at: datetime
    expenditure_notes: str | None = None
    total_cost_spent: Decimal | None = None


class EvidenceResponse(BaseModel):
    evidence_id: uuid.UUID
    milestone_id: uuid.UUID
    description: str
    captured_latitude: Decimal
    captured_longitude: Decimal
    captured_at: datetime
    site_media_urls: list[str]
    expenditure_notes: str | None = None
    total_cost_spent: Decimal | None = None
    receipt_media_urls: list[str] | None = None
    status: EvidenceStatus
    submitted_at: datetime

    class Config:
        from_attributes = True


class EvidenceReviewCreate(BaseModel):
    decision: ReviewDecision
    comment: str = Field(..., min_length=1)


class EvidenceReviewResponse(BaseModel):
    evidence_id: uuid.UUID
    decision: ReviewDecision
    comment: str
    message: str

    class Config:
        from_attributes = True
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.models.enums import EvidenceStatus, ReviewDecision
from app.schemas.common import Money


class EvidenceUploadRequest(BaseModel):
    filenames: list[Annotated[str, Field(min_length=1, max_length=255)]] = Field(..., min_length=1, max_length=20)
    folder: Literal["site_media", "receipt_media"] = "site_media"


class EvidenceUploadResponse(BaseModel):
    file_key: str
    upload_url: str


class EvidenceCreate(BaseModel):
    description: str = Field(..., min_length=1)
    captured_latitude: Decimal = Field(..., ge=-90, le=90)
    captured_longitude: Decimal = Field(..., ge=-180, le=180)
    captured_at: datetime
    site_media_keys: list[str] = Field(..., min_length=1, max_length=20, description="S3 keys of pre-uploaded site media")
    expenditure_notes: str | None = None
    total_cost_spent: Decimal | None = Field(None, ge=0)
    receipt_media_keys: list[str] | None = Field(None, max_length=20, description="S3 keys of pre-uploaded receipt media")

    @field_validator("captured_at")
    @classmethod
    def must_have_timezone(cls, v: datetime):
        if v.tzinfo is None or v.utcoffset() is None:
            raise ValueError("captured_at must include a timezone offset (send DateTime.toUtc().toIso8601String())")
        return v


class EvidenceResponse(BaseModel):
    evidence_id: uuid.UUID
    milestone_id: uuid.UUID
    description: str
    captured_latitude: Money
    captured_longitude: Money
    captured_at: datetime
    site_media_urls: list[str]
    expenditure_notes: str | None = None
    total_cost_spent: Money | None = None
    receipt_media_urls: list[str] = []
    status: EvidenceStatus
    submitted_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EvidenceReviewCreate(BaseModel):
    decision: ReviewDecision
    comment: str = Field(..., min_length=1)


class EvidenceReviewResponse(BaseModel):
    evidence_id: uuid.UUID
    decision: ReviewDecision
    comment: str
    message: str

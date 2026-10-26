import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field
from app.models.enums import EvidenceStatus, ReviewDecision


class EvidenceUploadRequest(BaseModel):
    filenames: list[str] = Field(..., min_length=1, description="List of filenames to generate upload links for")
    folder: str = Field("site_media", description="Target folder: 'site_media' or 'receipt_media'")


class EvidenceUploadResponse(BaseModel):
    file_key: str
    upload_url: str


class EvidenceCreate(BaseModel):
    description: str = Field(..., min_length=1)
    captured_latitude: Decimal
    captured_longitude: Decimal
    captured_at: datetime
    site_media_keys: list[str] = Field(..., min_length=1, description="S3 keys of pre-uploaded site media")
    expenditure_notes: str | None = None
    total_cost_spent: Decimal | None = None
    receipt_media_keys: list[str] | None = Field(None, description="S3 keys of pre-uploaded receipt media")


class EvidenceResponse(BaseModel):
    evidence_id: uuid.UUID
    milestone_id: uuid.UUID
    description: str
    captured_latitude: Decimal
    captured_longitude: Decimal
    captured_at: datetime
    site_media_urls: list[str]  # Returns presigned view URLs when fetched
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
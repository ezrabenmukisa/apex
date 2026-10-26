import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Uuid, String, Numeric, DateTime, Text, Enum as SqlEnum, ForeignKey, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin
from app.models.enums import EvidenceStatus, ReviewDecision


class ProgressEvidence(Base, TimestampMixin):
    __tablename__ = "progress_evidence"

    evidence_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    milestone_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("milestones.milestone_id", ondelete="CASCADE"), nullable=False, unique=True)
    
    description: Mapped[str] = mapped_column(Text, nullable=False)
    captured_latitude: Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=8), nullable=False)
    captured_longitude: Mapped[Decimal] = mapped_column(Numeric(precision=11, scale=8), nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    site_media_urls: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    
    expenditure_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_cost_spent: Mapped[Decimal | None] = mapped_column(Numeric(precision=12, scale=2), nullable=True)
    receipt_media_urls: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    
    status: Mapped[EvidenceStatus] = mapped_column(SqlEnum(EvidenceStatus), default=EvidenceStatus.SUBMITTED, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    milestone = relationship("Milestone", back_populates="evidence")
    reviews = relationship("EvidenceReview", back_populates="evidence", cascade="all, delete-orphan")


class EvidenceReview(Base, TimestampMixin):
    __tablename__ = "evidence_reviews"

    review_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    evidence_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("progress_evidence.evidence_id", ondelete="CASCADE"), nullable=False)
    
    decision: Mapped[ReviewDecision] = mapped_column(SqlEnum(ReviewDecision), nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    evidence = relationship("ProgressEvidence", back_populates="reviews")
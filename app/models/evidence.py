import uuid
from typing import TYPE_CHECKING
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import Uuid, String, Numeric, DateTime, Text, Enum as SqlEnum, ForeignKey, ARRAY, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin
from app.models.enums import EvidenceStatus, ReviewDecision

if TYPE_CHECKING:
    from app.models.milestone import Milestone


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ProgressEvidence(Base, TimestampMixin):
    __tablename__ = "progress_evidence"
    __table_args__ = (
        # Exactly one "live" submission per milestone. A REQUEST_CHANGES submission is
        # closed out, so the manager can submit a new one; DB-level guard against double submits.
        Index(
            "uq_active_evidence_per_milestone",
            "milestone_id",
            unique=True,
            postgresql_where=text("status <> 'REQUEST_CHANGES'"),
        ),
    )

    evidence_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    milestone_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("milestones.milestone_id", ondelete="CASCADE"), nullable=False, index=True
    )
    submitted_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True
    )

    description: Mapped[str] = mapped_column(Text, nullable=False)
    captured_latitude: Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=8), nullable=False)
    captured_longitude: Mapped[Decimal] = mapped_column(Numeric(precision=11, scale=8), nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # These hold raw S3 KEYS (not URLs). Never assign presigned URLs to them.
    site_media_urls: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)

    expenditure_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_cost_spent: Mapped[Decimal | None] = mapped_column(Numeric(precision=12, scale=2), nullable=True)
    receipt_media_urls: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)

    status: Mapped[EvidenceStatus] = mapped_column(SqlEnum(EvidenceStatus), default=EvidenceStatus.SUBMITTED, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    milestone: Mapped["Milestone"] = relationship(back_populates="evidence")
    reviews: Mapped[list["EvidenceReview"]] = relationship(back_populates="evidence", cascade="all, delete-orphan")


class EvidenceReview(Base, TimestampMixin):
    __tablename__ = "evidence_reviews"

    review_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    evidence_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("progress_evidence.evidence_id", ondelete="CASCADE"), nullable=False)

    decision: Mapped[ReviewDecision] = mapped_column(SqlEnum(ReviewDecision), nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=False)

    evidence: Mapped["ProgressEvidence"] = relationship(back_populates="reviews")

import uuid
from datetime import date
from decimal import Decimal
from sqlalchemy import Uuid, String, Integer, Numeric, Date, Enum as SqlEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.project import Project
from app.models.base import TimestampMixin
from app.models.enums import MilestoneStatus


class Milestone(Base, TimestampMixin):
    __tablename__ = "milestones"

    milestone_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    planned_budget: Mapped[Decimal | None] = mapped_column(Numeric(precision=12, scale=2), nullable=True)
    status: Mapped[MilestoneStatus] = mapped_column(SqlEnum(MilestoneStatus), default=MilestoneStatus.PENDING, nullable=False)

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="milestones")
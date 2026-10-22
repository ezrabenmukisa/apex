import uuid
from datetime import date, datetime
from sqlalchemy import Uuid, String, Numeric, Date, DateTime, Enum as SqlEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin
from app.models.enums import UserRole, ProjectStatus, InvitationStatus


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    project_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    project_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    latitude: Mapped[float] = mapped_column(Numeric(precision=9, scale=6), nullable=False)
    longitude: Mapped[float] = mapped_column(Numeric(precision=9, scale=6), nullable=False)
    location_name: Mapped[str] = mapped_column(String(512), nullable=False)
    planned_budget: Mapped[float | None] = mapped_column(Numeric(precision=12, scale=2), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(10), nullable=True)
    target_completion_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[ProjectStatus] = mapped_column(SqlEnum(ProjectStatus), default=ProjectStatus.ACTIVE, nullable=False)

    # Relationships
    members: Mapped[list["ProjectMember"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    invitations: Mapped[list["ProjectInvitation"]] = relationship(back_populates="project", cascade="all, delete-orphan")


class ProjectMember(Base):
    __tablename__ = "project_members"

    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.project_id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    user_role: Mapped[UserRole] = mapped_column(SqlEnum(UserRole, name="user_role_enum", values_callable=lambda obj: [e.value for e in obj]), nullable=False)


class ProjectInvitation(Base, TimestampMixin):
    __tablename__ = "project_invitations"

    invitation_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    user_role: Mapped[UserRole] = mapped_column(SqlEnum(UserRole, name="user_role_enum"), nullable=False)
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    status: Mapped[InvitationStatus] = mapped_column(SqlEnum(InvitationStatus), default=InvitationStatus.PENDING, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    project: Mapped["Project"] = relationship(back_populates="invitations")
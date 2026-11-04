import uuid
from sqlalchemy import Uuid, String
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from app.models.base import TimestampMixin

class User(Base, TimestampMixin):
    __tablename__ = "users"

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    firebase_uid: Mapped[str] = mapped_column(String(128), unique=True, index=True)

    first_name: Mapped[str] = mapped_column(String(255))
    middle_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str] = mapped_column(String(255))

    # Required by the product, but a brand-new Firebase user (e.g. phone sign-in) has none until onboarding.
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    contact_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)

    profile_complete: Mapped[bool] = mapped_column(default=False)

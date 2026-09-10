import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserPreferences(Base):
    __tablename__ = "user_preferences"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # -------------------------
    # AI preferences
    # -------------------------

    response_style: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="balanced",
    )

    default_expense_period: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="this_month",
    )

    default_report_format: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="pdf",
    )

    confirm_before_actions: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    # -------------------------
    # Automated summaries
    # -------------------------

    weekly_summary: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    monthly_summary: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    # -------------------------
    # Alerts
    # -------------------------

    budget_alerts: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    unusual_spending_alerts: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    # -------------------------
    # Frontend only
    # -------------------------

    theme: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="system",
    )

    # -------------------------
    # Timestamps
    # -------------------------

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

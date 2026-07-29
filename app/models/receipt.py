import uuid

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.db.base import Base


class Receipt(Base):
    __tablename__ = "receipts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # =====================================
    # ImageKit
    # =====================================

    imagekit_file_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    image_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    image_path: Mapped[str | None] = mapped_column(
        Text,
    )

    original_filename: Mapped[str | None] = mapped_column(
        String(255),
    )

    # =====================================
    # Merchant
    # =====================================

    merchant_name: Mapped[str | None] = mapped_column(
        String(255),
    )

    merchant_address: Mapped[str | None] = mapped_column(
        Text,
    )

    merchant_phone: Mapped[str | None] = mapped_column(
        String(50),
    )

    gst_number: Mapped[str | None] = mapped_column(
        String(50),
    )

    # =====================================
    # Receipt
    # =====================================

    purchase_datetime: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    receipt_number: Mapped[str | None] = mapped_column(
        String(100),
    )

    # =====================================
    # Classification
    # =====================================

    expense_type: Mapped[str | None] = mapped_column(
        String(50),
        index=True,
    )

    classification_confidence: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 4),
    )

    # =====================================
    # Money
    # =====================================

    subtotal: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
    )

    tax: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
    )

    discount: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
    )

    total: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
    )

    currency: Mapped[str | None] = mapped_column(
        String(3),
    )

    # =====================================
    # Payment
    # =====================================

    payment_method: Mapped[str | None] = mapped_column(
        String(30),
    )

    payment_last_four: Mapped[str | None] = mapped_column(
        String(4),
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
    )

    # =====================================
    # AI processing
    # =====================================

    processing_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="PROCESSING",
        index=True,
    )

    processing_error: Mapped[str | None] = mapped_column(
        Text,
    )

    validation_status: Mapped[str | None] = mapped_column(
        String(30),
    )

    validation_confidence: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 4),
    )

    # =====================================
    # Timestamps
    # =====================================

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # =====================================
    # Relationships
    # =====================================

    items: Mapped[list["ReceiptItem"]] = relationship(
        back_populates="receipt",
        cascade="all, delete-orphan",
    )

    user: Mapped["User"] = relationship(
        back_populates="receipts",
    )

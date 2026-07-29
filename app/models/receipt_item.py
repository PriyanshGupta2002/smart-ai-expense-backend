import uuid

from decimal import Decimal

from sqlalchemy import (
    ForeignKey,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.db.base import Base


class ReceiptItem(Base):
    __tablename__ = "receipt_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    receipt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "receipts.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    quantity: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 3),
    )

    unit_price: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
    )

    total_price: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
    )

    receipt: Mapped["Receipt"] = relationship(
        back_populates="items",
    )

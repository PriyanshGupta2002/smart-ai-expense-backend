from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
)


class ReceiptItemResponse(BaseModel):
    id: UUID

    name: str

    quantity: Decimal | None
    unit_price: Decimal | None
    total_price: Decimal | None

    model_config = ConfigDict(from_attributes=True)


class ReceiptResponse(BaseModel):
    id: UUID

    merchant_name: str | None
    merchant_address: str | None

    purchase_datetime: datetime | None
    receipt_number: str | None

    expense_type: str | None

    subtotal: Decimal | None
    tax: Decimal | None
    discount: Decimal | None
    total: Decimal | None
    currency: str | None

    payment_method: str | None

    image_url: str

    processing_status: str
    validation_status: str | None

    items: list[ReceiptItemResponse]

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReceiptListItem(BaseModel):
    id: UUID

    merchant_name: str | None
    purchase_datetime: datetime | None

    expense_type: str | None

    total: Decimal | None
    currency: str | None

    payment_method: str | None
    processing_status: str
    image_url: str | None


class ReceiptListResponse(BaseModel):
    items: list[ReceiptListItem]

    page: int
    page_size: int

    total: int
    total_pages: int

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class OCRBlock(BaseModel):

    text: str

    confidence: float

    bbox: list[list[float]]

    page: int = 1


class LayoutBlock(BaseModel):
    text: str
    confidence: float

    x: float
    y: float
    width: float
    height: float


class OCRRow(BaseModel):
    blocks: list[LayoutBlock]


class Merchant(BaseModel):
    name: str | None = Field(
        default=None, description="Merchant, store, clinic, restaurant or seller name."
    )

    address: str | None = None
    phone: str | None = None
    gst_number: str | None = None


class ReceiptItem(BaseModel):
    name: str = Field(
        description=(
            "Complete item name. Multiline names belonging to the same "
            "line item must be combined."
        )
    )

    quantity: float | None = None
    unit_price: float | None = None
    total_price: float | None = None


class Totals(BaseModel):
    subtotal: float | None = None

    tax: float | None = Field(
        default=None, description="Total tax displayed on the receipt."
    )

    tax_inclusive: bool | None = Field(
        default=None,
        description=(
            "True when displayed tax is already included in item prices "
            "or subtotal. False when tax must be added separately."
        ),
    )

    discount: float | None = None

    total: float = Field(description="Final amount payable by the customer.")

    currency: str = Field(description="ISO 4217 currency code such as INR, USD or EUR.")


class Payment(BaseModel):
    method: Literal[
        "cash",
        "upi",
        "credit_card",
        "debit_card",
        "wallet",
        "bank_transfer",
        "unknown",
    ] = "unknown"

    last_four: str | None = None


class ReceiptExtraction(BaseModel):
    merchant: Merchant

    purchase_datetime: datetime | None = None

    receipt_number: str | None = None

    items: list[ReceiptItem] = Field(default_factory=list)

    totals: Totals

    payment: Payment

    notes: str | None = None


class Classification(BaseModel):
    expense_type: Literal[
        "groceries",
        "food_dining",
        "shopping",
        "fuel",
        "travel",
        "medical",
        "electronics",
        "entertainment",
        "utilities",
        "education",
        "home_services",
        "personal_care",
        "transportation",
        "subscriptions",
        "other",
    ]

    subcategory: str | None = Field(
        default=None,
        description=(
            "A concise semantic subcategory describing the "
            "actual expense, such as 'AC service', "
            "'electricity bill', 'medicines', 'cab ride', "
            "'mobile recharge', or 'restaurant dining'."
        ),
    )

    tags: list[str] = Field(
        default_factory=list,
        description=(
            "Short semantic labels useful for finding this "
            "expense from natural-language queries."
        ),
    )

    confidence: float = Field(
        ge=0,
        le=1,
    )


class ValidationResult(BaseModel):
    is_valid: bool

    confidence_score: float = Field(
        ge=0,
        le=1,
    )

    status: Literal[
        "VALID",
        "LOW_CONFIDENCE",
        "NEEDS_REVIEW",
        "INVALID",
    ]

    retry_from: Literal[
        "none",
        "ocr",
        "extraction",
    ] = "none"

    warnings: list[str] = Field(default_factory=list)

    errors: list[str] = Field(default_factory=list)

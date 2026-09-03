from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field


class TransactionType(str, Enum):
    EXPENSE = "expense"
    INCOME = "income"
    TRANSFER = "transfer"
    UNKNOWN = "unknown"


class TransactionCandidate(BaseModel):
    """
    Structured result extracted from a Gmail transaction email.
    """

    is_transaction: bool = Field(
        description="Whether the email represents an actual financial transaction."
    )

    transaction_type: TransactionType = Field(
        description=(
            "Type of financial transaction: " "expense, income, transfer, or unknown."
        )
    )

    amount: Decimal | None = Field(
        default=None,
        description="Transaction amount actually paid or received.",
    )

    currency: str | None = Field(
        default=None,
        description="Currency code such as INR, USD, EUR.",
    )

    merchant_name: str | None = Field(
        default=None,
        description="Merchant, business, service provider, or recipient name.",
    )

    transaction_date: datetime | None = Field(
        default=None,
        description="Date and time when the transaction occurred.",
    )

    payment_method: str | None = Field(
        default=None,
        description="Payment method such as UPI, credit card, debit card, etc.",
    )

    category: str | None = Field(
        default=None,
        description=(
            "Expense category such as food, shopping, "
            "transport, medical, utilities, etc."
        ),
    )

    description: str | None = Field(
        default=None,
        description="Short description of the transaction.",
    )

    confidence: float = Field(
        ge=0,
        le=1,
        description="Confidence in the classification from 0 to 1.",
    )

    reason: str | None = Field(
        default=None,
        description="Brief reason for the classification.",
    )

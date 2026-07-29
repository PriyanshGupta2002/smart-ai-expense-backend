from decimal import Decimal
from pydantic import BaseModel, Field


class PeriodMetrics(BaseModel):
    total_spend: Decimal = Field(description="Total amount spent during this period.")

    transaction_count: int = Field(
        description="Number of completed transactions during this period."
    )

    average_transaction: Decimal = Field(
        description="Average transaction amount during this period."
    )


class CategoryComparison(BaseModel):
    category: str = Field(description="Expense category.")

    current_spend: Decimal = Field(
        description="Amount spent in this category during the current period."
    )

    previous_spend: Decimal = Field(
        description="Amount spent in this category during the comparable previous period."
    )


class MerchantMetric(BaseModel):
    merchant: str = Field(description="Merchant name.")

    amount: Decimal = Field(
        description="Total amount spent at this merchant during the current period."
    )

    transaction_count: int = Field(
        description="Number of transactions at this merchant during the current period."
    )


class TransactionMetric(BaseModel):
    merchant: str | None = None
    category: str | None = None
    amount: Decimal


class AnalyticsSnapshot(BaseModel):
    current_period: PeriodMetrics

    previous_comparable_period: PeriodMetrics

    categories: list[CategoryComparison]

    top_merchants: list[MerchantMetric]

    largest_transactions: list[TransactionMetric]

from pydantic import BaseModel, ConfigDict
from decimal import Decimal
from datetime import date
from typing import Literal


class DashboardSummaryResponse(BaseModel):
    total_spend: Decimal
    transaction_count: int
    current_month_spend: Decimal
    average_transaction: Decimal
    model_config = ConfigDict(from_attributes=True)


class CategorySpendResponse(BaseModel):
    category: str
    amount: Decimal
    transaction_count: int
    percentage: float


class CategoryDistributionResponse(BaseModel):
    categories: list[CategorySpendResponse]


class Merchant(BaseModel):
    merchant: str
    amount: Decimal
    transaction_count: int


class TopMerchantResponse(BaseModel):
    top_merchants: list[Merchant]


class SpendingTrendItem(BaseModel):
    date: date
    amount: Decimal
    transaction_count: int


class SpendingTrendResponse(BaseModel):
    data: list[SpendingTrendItem]


class SpendingChangeInsight(BaseModel):
    type: Literal["spending_change"]
    current_spend: Decimal
    previous_spend: Decimal
    percentage_change: float | None
    direction: Literal["increased", "decreased", "unchanged", "no_comparison"]
    message: str


class TopCategoryInsight(BaseModel):
    type: Literal["top_category"]
    category: str
    amount: Decimal
    percentage_of_total: float
    transaction_count: int
    message: str


class TopMerchantInsight(BaseModel):
    type: Literal["top_merchant"]
    merchant: str
    amount: Decimal
    transaction_count: int
    message: str


class DashboardInsightsResponse(BaseModel):
    spending_change: SpendingChangeInsight
    top_category: TopCategoryInsight | None
    top_merchant: TopMerchantInsight | None

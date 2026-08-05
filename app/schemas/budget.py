from pydantic import BaseModel, ConfigDict
from decimal import Decimal
from datetime import date, datetime
from uuid import UUID


class CurrentBudgetResponse(BaseModel):
    month: date

    amount: Decimal

    amount_spent: Decimal

    remaining: Decimal

    percentage_used: float

    model_config = ConfigDict(from_attributes=True)


class BudgetRequest(BaseModel):
    amount: Decimal

    model_config = ConfigDict(from_attributes=True)

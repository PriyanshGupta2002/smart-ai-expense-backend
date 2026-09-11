from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ResponseStyle(str, Enum):
    CONCISE = "concise"
    BALANCED = "balanced"
    DETAILED = "detailed"


class ExpensePeriod(str, Enum):
    THIS_MONTH = "this_month"
    LAST_MONTH = "last_month"
    THIS_YEAR = "this_year"
    LAST_30_DAYS = "last_30_days"


class ReportFormat(str, Enum):
    PDF = "pdf"
    CSV = "csv"
    XLSX = "xlsx"


class Theme(str, Enum):
    SYSTEM = "system"
    LIGHT = "light"
    DARK = "dark"


class UserPreferencesUpdate(BaseModel):
    response_style: ResponseStyle | None = None

    default_expense_period: ExpensePeriod | None = None

    default_report_format: ReportFormat | None = None

    confirm_before_actions: bool | None = None

    weekly_summary: bool | None = None

    monthly_summary: bool | None = None

    budget_alerts: bool | None = None

    unusual_spending_alerts: bool | None = None

    theme: Theme | None = None


class UserPreferencesResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID

    response_style: ResponseStyle
    default_expense_period: ExpensePeriod
    default_report_format: ReportFormat

    confirm_before_actions: bool

    weekly_summary: bool
    monthly_summary: bool

    budget_alerts: bool
    unusual_spending_alerts: bool

    theme: Theme

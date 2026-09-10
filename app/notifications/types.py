from enum import StrEnum


class NotificationType(StrEnum):
    WEEKLY_SUMMARY = "weekly_summary"
    MONTHLY_SUMMARY = "monthly_summary"
    BUDGET_ALERT = "budget_alert"
    UNUSUAL_SPENDING_ALERT = "unusual_spending_alert"

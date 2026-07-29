from datetime import datetime, timedelta, timezone
from enum import Enum
from calendar import monthrange


class DashboardPeriod(str, Enum):
    THIS_WEEK = "this_week"
    THIS_MONTH = "this_month"
    LAST_MONTH = "last_month"
    LAST_30_DAYS = "last_30_days"
    THIS_YEAR = "this_year"
    ALL_TIME = "all_time"


def get_period_range(
    period: DashboardPeriod,
) -> tuple[datetime | None, datetime]:

    now = datetime.now(timezone.utc)

    if period == DashboardPeriod.THIS_WEEK:
        start = now - timedelta(days=now.weekday())

        start = start.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

    elif period == DashboardPeriod.THIS_MONTH:
        start = datetime(
            now.year,
            now.month,
            1,
            tzinfo=timezone.utc,
        )

    elif period == DashboardPeriod.LAST_MONTH:

        current_month_start = datetime(
            now.year,
            now.month,
            1,
            tzinfo=timezone.utc,
        )

        previous_month_last_day = current_month_start - timedelta(days=1)

        start = datetime(
            previous_month_last_day.year,
            previous_month_last_day.month,
            1,
            tzinfo=timezone.utc,
        )

        # Important:
        # last_month should end at the beginning
        # of the current month.
        return start, current_month_start

    elif period == DashboardPeriod.LAST_30_DAYS:
        start = now - timedelta(days=30)

    elif period == DashboardPeriod.THIS_YEAR:
        start = datetime(
            now.year,
            1,
            1,
            tzinfo=timezone.utc,
        )

    elif period == DashboardPeriod.ALL_TIME:
        return None, now

    else:
        raise ValueError(f"Unsupported period: {period}")

    return start, now


def get_month_comparison_ranges():
    now = datetime.now(timezone.utc)

    # --------------------------------
    # Current month
    # --------------------------------

    current_start = datetime(
        now.year,
        now.month,
        1,
        tzinfo=timezone.utc,
    )

    current_end = now

    # --------------------------------
    # Previous month
    # --------------------------------

    if now.month == 1:
        previous_year = now.year - 1
        previous_month = 12
    else:
        previous_year = now.year
        previous_month = now.month - 1

    previous_start = datetime(
        previous_year,
        previous_month,
        1,
        tzinfo=timezone.utc,
    )

    # Handle months with fewer days
    previous_month_days = monthrange(
        previous_year,
        previous_month,
    )[1]

    comparison_day = min(
        now.day,
        previous_month_days,
    )

    previous_end = datetime(
        previous_year,
        previous_month,
        comparison_day,
        now.hour,
        now.minute,
        now.second,
        now.microsecond,
        tzinfo=timezone.utc,
    )

    return (
        current_start,
        current_end,
        previous_start,
        previous_end,
    )

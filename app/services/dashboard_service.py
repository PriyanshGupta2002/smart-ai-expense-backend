from datetime import datetime, timezone

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.receipt import Receipt
from app.models.user import User
from app.utils.date_range import (
    DashboardPeriod,
    get_period_range,
)

from decimal import Decimal


class DashboardService:

    def __init__(self, db: Session):
        self.db = db

    def _period_filters(
        self,
        user: User,
        period: DashboardPeriod,
    ):
        start_date, end_date = get_period_range(period)

        filters = [
            Receipt.user_id == user.id,
            Receipt.processing_status == "COMPLETED",
        ]

        if start_date is not None:
            filters.append(Receipt.purchase_datetime >= start_date)

        filters.append(Receipt.purchase_datetime < end_date)

        return filters

    def get_dashboard_summary(self, user: User):

        now = datetime.now(timezone.utc)

        current_month_start = datetime(
            year=now.year,
            month=now.month,
            day=1,
            tzinfo=timezone.utc,
        )

        stmt = select(
            # All-time spend
            func.coalesce(
                func.sum(Receipt.total),
                0,
            ).label("total_spend"),
            # Current month spend
            func.coalesce(
                func.sum(
                    case(
                        (
                            Receipt.purchase_datetime >= current_month_start,
                            Receipt.total,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("current_month_spend"),
            # All-time transaction count
            func.count(Receipt.id).label("transaction_count"),
            # All-time average
            func.coalesce(
                func.avg(Receipt.total),
                0,
            ).label("average_transaction"),
        ).where(
            Receipt.user_id == user.id,
            Receipt.processing_status == "COMPLETED",
        )

        result = self.db.execute(stmt).one()

        return {
            "total_spend": result.total_spend,
            "current_month_spend": result.current_month_spend,
            "transaction_count": result.transaction_count,
            "average_transaction": result.average_transaction,
        }

    def get_category_distribution(
        self,
        user: User,
        period: DashboardPeriod,
    ):
        stmt = (
            select(
                Receipt.expense_type.label("category"),
                func.sum(Receipt.total).label("amount"),
                func.count(Receipt.id).label("transaction_count"),
            )
            .where(*self._period_filters(user, period))
            .group_by(Receipt.expense_type)
            .order_by(func.sum(Receipt.total).desc())
        )

        rows = self.db.execute(stmt).all()

        total_spend = sum(row.amount or Decimal("0") for row in rows)

        categories = []

        for row in rows:

            amount = row.amount or Decimal("0")

            percentage = float(amount / total_spend * 100) if total_spend > 0 else 0

            categories.append(
                {
                    "category": row.category or "other",
                    "amount": amount,
                    "transaction_count": row.transaction_count,
                    "percentage": round(percentage, 2),
                }
            )

        return {"categories": categories}

    def top_merchants(self, user: User, period: DashboardPeriod):
        stmt = (
            select(
                Receipt.merchant_name.label("merchant"),
                func.sum(Receipt.total).label("amount"),
                func.count(Receipt.id).label("transaction_count"),
            )
            .where(*self._period_filters(user, period))
            .group_by(Receipt.merchant_name)
            .order_by(func.sum(Receipt.total).desc())
            .limit(5)
        )
        merchants = self.db.execute(stmt).all()
        return {"top_merchants": merchants}

    def get_spending_trend(
        self,
        user: User,
        period: DashboardPeriod,
    ):
        date_bucket = func.date_trunc(
            "day",
            Receipt.purchase_datetime,
        ).label("date")

        stmt = (
            select(
                date_bucket,
                func.sum(Receipt.total).label("amount"),
                func.count(Receipt.id).label("transaction_count"),
            )
            .where(
                *self._period_filters(
                    user,
                    period,
                )
            )
            .group_by(date_bucket)
            .order_by(date_bucket)
        )

        rows = self.db.execute(stmt).all()

        return {
            "data": [
                {
                    "date": row.date.date(),
                    "amount": row.amount,
                    "transaction_count": row.transaction_count,
                }
                for row in rows
            ]
        }

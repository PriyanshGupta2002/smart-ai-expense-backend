from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.receipt import Receipt
from app.models.user import User
from app.utils.date_range import get_month_comparison_ranges
from datetime import datetime
from app.schemas.insight import (
    CategoryComparison,
    AnalyticsSnapshot,
    TransactionMetric,
    PeriodMetrics,
    MerchantMetric,
)
from app.ai.insight.schema import AIInsights
from app.ai.insight.insight_model import get_insight_model_result
from app.services.insight_cache_service import InsightCacheService


class InsightService:

    def __init__(self, db: Session):
        self.db = db

    def _get_largest_transactions(
        self,
        user_id,
        start_date: datetime,
        end_date: datetime,
        limit: int = 5,
    ) -> list[TransactionMetric]:

        stmt = (
            select(
                Receipt.merchant_name,
                Receipt.expense_type,
                Receipt.total,
            )
            .where(
                Receipt.user_id == user_id,
                Receipt.processing_status == "COMPLETED",
                Receipt.purchase_datetime >= start_date,
                Receipt.purchase_datetime < end_date,
            )
            .order_by(Receipt.total.desc())
            .limit(limit)
        )

        rows = self.db.execute(stmt).all()

        return [
            TransactionMetric(
                merchant=row.merchant_name,
                category=row.expense_type,
                amount=row.total,
            )
            for row in rows
        ]

    def _get_period_metrics(
        self,
        user_id,
        start_date: datetime,
        end_date: datetime,
    ) -> PeriodMetrics:

        stmt = select(
            func.coalesce(
                func.sum(Receipt.total),
                0,
            ).label("total_spend"),
            func.count(Receipt.id).label("transaction_count"),
            func.coalesce(
                func.avg(Receipt.total),
                0,
            ).label("average_transaction"),
        ).where(
            Receipt.user_id == user_id,
            Receipt.processing_status == "COMPLETED",
            Receipt.purchase_datetime >= start_date,
            Receipt.purchase_datetime < end_date,
        )

        result = self.db.execute(stmt).one()

        return PeriodMetrics(
            total_spend=result.total_spend,
            transaction_count=result.transaction_count,
            average_transaction=result.average_transaction,
        )

    def _get_category_spending(
        self,
        user_id,
        start_date: datetime,
        end_date: datetime,
    ) -> dict[str, Decimal]:

        stmt = (
            select(
                Receipt.expense_type,
                func.sum(Receipt.total).label("amount"),
            )
            .where(
                Receipt.user_id == user_id,
                Receipt.processing_status == "COMPLETED",
                Receipt.purchase_datetime >= start_date,
                Receipt.purchase_datetime < end_date,
                Receipt.expense_type.is_not(None),
            )
            .group_by(Receipt.expense_type)
        )

        rows = self.db.execute(stmt).all()

        return {row.expense_type: row.amount for row in rows}

    def _get_category_comparison(
        self,
        user_id,
        current_start,
        current_end,
        previous_start,
        previous_end,
    ) -> list[CategoryComparison]:

        current = self._get_category_spending(
            user_id,
            current_start,
            current_end,
        )

        previous = self._get_category_spending(
            user_id,
            previous_start,
            previous_end,
        )

        categories = set(current.keys()) | set(previous.keys())

        result = []

        for category in categories:

            result.append(
                CategoryComparison(
                    category=category,
                    current_spend=current.get(
                        category,
                        Decimal("0"),
                    ),
                    previous_spend=previous.get(
                        category,
                        Decimal("0"),
                    ),
                )
            )

        return result

    def _get_spending_comparison(
        self,
        user: User,
    ):
        (
            current_start,
            current_end,
            previous_start,
            previous_end,
        ) = get_month_comparison_ranges()

        current_spend = self.db.scalar(
            select(
                func.coalesce(
                    func.sum(Receipt.total),
                    0,
                )
            ).where(
                Receipt.user_id == user.id,
                Receipt.processing_status == "COMPLETED",
                Receipt.purchase_datetime >= current_start,
                Receipt.purchase_datetime < current_end,
            )
        )

        previous_spend = self.db.scalar(
            select(
                func.coalesce(
                    func.sum(Receipt.total),
                    0,
                )
            ).where(
                Receipt.user_id == user.id,
                Receipt.processing_status == "COMPLETED",
                Receipt.purchase_datetime >= previous_start,
                Receipt.purchase_datetime < previous_end,
            )
        )

        return {
            "current": current_spend,
            "previous": previous_spend,
        }

    def _get_top_category(
        self,
        user: User,
    ):
        (
            current_start,
            current_end,
            _,
            _,
        ) = get_month_comparison_ranges()

        stmt = (
            select(
                Receipt.expense_type.label("category"),
                func.sum(Receipt.total).label("amount"),
                func.count(Receipt.id).label("transaction_count"),
            )
            .where(
                Receipt.user_id == user.id,
                Receipt.processing_status == "COMPLETED",
                Receipt.purchase_datetime >= current_start,
                Receipt.purchase_datetime < current_end,
                Receipt.expense_type.is_not(None),
            )
            .group_by(Receipt.expense_type)
            .order_by(func.sum(Receipt.total).desc())
            .limit(1)
        )

        return self.db.execute(stmt).one_or_none()

    def _get_top_merchant(
        self,
        user_id,
        start_date: datetime,
        end_date: datetime,
        limit: int = 5,
    ) -> list[MerchantMetric]:

        stmt = (
            select(
                Receipt.merchant_name.label("merchant"),
                func.sum(Receipt.total).label("amount"),
                func.count(Receipt.id).label("transaction_count"),
            )
            .where(
                Receipt.user_id == user_id,
                Receipt.processing_status == "COMPLETED",
                Receipt.purchase_datetime >= start_date,
                Receipt.purchase_datetime < end_date,
                Receipt.merchant_name.is_not(None),
            )
            .group_by(Receipt.merchant_name)
            .order_by(func.sum(Receipt.total).desc())
            .limit(limit)
        )

        rows = self.db.execute(stmt).all()

        return [
            MerchantMetric(
                merchant=row.merchant,
                amount=row.amount,
                transaction_count=row.transaction_count,
            )
            for row in rows
        ]

    def generate_insights(
        self,
        user: User,
    ):
        spending = self._get_spending_comparison(user)
        top_category = self._get_top_category(user)
        top_merchant = self._get_top_merchant(user)

        current_spend = spending["current"]
        previous_spend = spending["previous"]

        # ---------------------------------
        # Spending change
        # ---------------------------------

        if previous_spend > 0:

            percentage_change = float(
                (current_spend - previous_spend) / previous_spend * 100
            )

            if percentage_change > 0:
                direction = "increased"

                message = (
                    f"Your spending has increased by "
                    f"{abs(percentage_change):.1f}% "
                    f"compared with the same period last month."
                )

            elif percentage_change < 0:
                direction = "decreased"

                message = (
                    f"Your spending has decreased by "
                    f"{abs(percentage_change):.1f}% "
                    f"compared with the same period last month."
                )

            else:
                direction = "unchanged"

                message = (
                    "Your spending is unchanged compared "
                    "with the same period last month."
                )

        else:
            percentage_change = None
            direction = "no_comparison"

            message = (
                "There isn't enough spending data from " "last month to compare yet."
            )

        spending_change = {
            "type": "spending_change",
            "current_spend": current_spend,
            "previous_spend": previous_spend,
            "percentage_change": percentage_change,
            "direction": direction,
            "message": message,
        }
        # ---------------------------------
        # Top category
        # ---------------------------------

        category_insight = None

        if top_category:

            category_amount = top_category.amount or Decimal("0")

            if current_spend > 0:
                percentage_of_total = float(category_amount / current_spend * 100)
            else:
                percentage_of_total = 0.0

            category_insight = {
                "type": "top_category",
                "category": top_category.category,
                "amount": category_amount,
                "percentage_of_total": round(percentage_of_total, 2),
                "transaction_count": top_category.transaction_count,
                "message": (
                    f"{top_category.category.title()} is "
                    f"your biggest spending category this "
                    f"month, accounting for "
                    f"{percentage_of_total:.1f}% "
                    f"of your spending."
                ),
            }

            # ---------------------------------
        # Top merchant
        # ---------------------------------

        merchant_insight = None

        if top_merchant:

            merchant_insight = {
                "type": "top_merchant",
                "merchant": top_merchant.merchant,
                "amount": top_merchant.amount,
                "transaction_count": top_merchant.transaction_count,
                "message": (
                    f"{top_merchant.merchant} is your "
                    f"highest-spend merchant this month "
                    f"with {top_merchant.transaction_count} "
                    f"transactions."
                ),
            }
        return {
            "spending_change": spending_change,
            "top_category": category_insight,
            "top_merchant": merchant_insight,
        }

    def build_snapshot(
        self,
        user: User,
    ) -> AnalyticsSnapshot:

        (
            current_start,
            current_end,
            previous_start,
            previous_end,
        ) = get_month_comparison_ranges()

        current_metrics = self._get_period_metrics(
            user.id,
            current_start,
            current_end,
        )

        previous_metrics = self._get_period_metrics(
            user.id,
            previous_start,
            previous_end,
        )

        categories = self._get_category_comparison(
            user.id,
            current_start,
            current_end,
            previous_start,
            previous_end,
        )

        top_merchants = self._get_top_merchant(
            user.id,
            current_start,
            current_end,
        )

        largest_transactions = self._get_largest_transactions(
            user.id,
            current_start,
            current_end,
        )

        return AnalyticsSnapshot(
            current_period=current_metrics,
            previous_comparable_period=previous_metrics,
            categories=categories,
            top_merchants=top_merchants,
            largest_transactions=largest_transactions,
        )

    def generate_ai_insights(self, user: User) -> AIInsights:
        cached = InsightCacheService.get(user.id)
        if cached is not None:
            return cached

        snapshot = self.build_snapshot(user=user)

        insights = get_insight_model_result(
            human_content=snapshot.model_dump_json(indent=2)
        )
        InsightCacheService.set(
            user.id,
            insights,
        )
        return insights

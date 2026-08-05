from sqlalchemy.orm import Session
from app.models.user import User
from app.models.budget import Budget
from app.models.receipt import Receipt
from datetime import date
from app.services.dashboard_service import DashboardService
from sqlalchemy import func
from decimal import Decimal
from app.schemas.budget import CurrentBudgetResponse


class BudgetService:

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _current_month() -> date:
        return date.today().replace(day=1)

    def _get_current_budget(
        self,
        user: User,
    ) -> Budget | None:
        return (
            self.db.query(Budget)
            .filter_by(
                user_id=user.id,
                month=self._current_month(),
            )
            .first()
        )

    def get_current_budget(
        self,
        user: User,
    ) -> CurrentBudgetResponse | None:

        month = self._current_month()

        budget = (
            self.db.query(Budget)
            .filter_by(
                user_id=user.id,
                month=month,
            )
            .first()
        )

        if budget is None:
            return None

        amount_spent = (
            self.db.query(
                func.coalesce(
                    func.sum(Receipt.total),
                    0,
                )
            )
            .filter(
                Receipt.user_id == user.id,
                func.date_trunc("month", Receipt.purchase_datetime) == month,
            )
            .scalar()
        )

        remaining = max(
            Decimal(budget.amount) - Decimal(amount_spent),
            Decimal("0"),
        )

        percentage_used = (
            float(Decimal(amount_spent) / Decimal(budget.amount) * Decimal("100"))
            if budget.amount > 0
            else 0
        )

        return CurrentBudgetResponse(
            month=budget.month,
            amount=budget.amount,
            amount_spent=amount_spent,
            remaining=remaining,
            percentage_used=percentage_used,
        )

    def upsert_current_budget(
        self,
        user: User,
        amount: float,
    ) -> Budget:

        budget = self._get_current_budget(user)

        if budget is None:
            budget = Budget(
                user_id=user.id,
                month=self._current_month(),
                amount=amount,
            )

            self.db.add(budget)

        else:
            budget.amount = amount

        self.db.commit()
        self.db.refresh(budget)

        return budget

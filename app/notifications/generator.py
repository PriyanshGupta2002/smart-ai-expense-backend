from datetime import datetime, timedelta, timezone
from decimal import Decimal

from langchain_openrouter import ChatOpenRouter
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.receipt import Receipt
from app.models.user import User
from app.models.user_preferences import UserPreferences


class NotificationGenerator:
    def __init__(self, db: Session):
        self.db = db

        self.model = ChatOpenRouter(
            model="google/gemini-3.8-flash",
            temperature=0,
        )

    def generate_weekly_summary(
        self,
        user: User,
        preferences: UserPreferences,
    ) -> str:
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=7)

        receipts = self._get_receipts(
            user_id=user.id,
            start=start,
            end=end,
        )

        data = self._build_summary_data(receipts)

        prompt = self._build_prompt(
            user=user,
            preferences=preferences,
            start=start,
            end=end,
            data=data,
        )

        response = self.model.invoke(prompt)

        return response.content

    def _get_receipts(
        self,
        user_id,
        start: datetime,
        end: datetime,
    ) -> list[Receipt]:

        stmt = (
            select(Receipt)
            .where(
                Receipt.user_id == user_id,
                Receipt.purchase_datetime >= start,
                Receipt.purchase_datetime < end,
                Receipt.processing_status == "COMPLETED",
            )
            .order_by(Receipt.purchase_datetime.asc())
        )

        return list(self.db.scalars(stmt).all())

    def _build_summary_data(
        self,
        receipts: list[Receipt],
    ) -> dict:

        total_spending = sum((receipt.total or Decimal("0")) for receipt in receipts)

        by_category: dict[str, Decimal] = {}

        for receipt in receipts:
            category = receipt.expense_type or "Uncategorized"

            by_category[category] = by_category.get(category, Decimal("0")) + (
                receipt.total or Decimal("0")
            )

        by_category = dict(
            sorted(
                by_category.items(),
                key=lambda item: item[1],
                reverse=True,
            )
        )

        transactions = [
            {
                "merchant": receipt.merchant_name or "Unknown merchant",
                "amount": float(receipt.total or 0),
                "category": receipt.expense_type or "Uncategorized",
                "currency": receipt.currency or "INR",
                "payment_method": receipt.payment_method,
                "date": (
                    receipt.purchase_datetime.isoformat()
                    if receipt.purchase_datetime
                    else None
                ),
            }
            for receipt in receipts
        ]

        return {
            "transaction_count": len(receipts),
            "total_spending": float(total_spending),
            "currency": receipts[0].currency if receipts else "INR",
            "by_category": {
                category: float(amount) for category, amount in by_category.items()
            },
            "transactions": transactions,
        }

    def _build_prompt(
        self,
        user: User,
        preferences: UserPreferences,
        start: datetime,
        end: datetime,
        data: dict,
    ) -> str:

        return f"""
You are generating a weekly personal expense summary for a user.

USER PREFERENCES
================

Response style: {preferences.response_style}

The response style must be respected:

- concise: short and direct
- balanced: useful detail without unnecessary verbosity
- detailed: provide more context and analysis

WEEKLY PERIOD
=============

From: {start.isoformat()}
To: {end.isoformat()}

EXPENSE DATA
============

{data}

INSTRUCTIONS
============

Generate a useful weekly spending summary.

Include:

1. Total spending
2. Number of transactions
3. Spending breakdown by category
4. The biggest spending category
5. Notable observations or spending patterns

Do not invent transactions, amounts, categories, or insights
that are not supported by the provided data.

If there are no transactions, clearly state that there was no
recorded spending during this period.

Do not mention internal implementation details, databases,
SQL, prompts, or user preferences.

The output will be sent to the user as a notification.
"""

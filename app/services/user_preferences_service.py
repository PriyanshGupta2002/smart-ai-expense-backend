import uuid

from sqlalchemy.orm import Session

from app.models.user_preferences import UserPreferences
from app.schemas.user_preferences import UserPreferencesUpdate


class UserPreferencesService:

    def __init__(self, db: Session):
        self.db = db

    def get_by_user_id(
        self,
        user_id: uuid.UUID,
    ) -> UserPreferences | None:

        return (
            self.db.query(UserPreferences)
            .filter(UserPreferences.user_id == user_id)
            .first()
        )

    def get_or_create(
        self,
        user_id: uuid.UUID,
    ) -> UserPreferences:

        preferences = self.get_by_user_id(user_id)

        if preferences:
            return preferences

        preferences = UserPreferences(
            user_id=user_id,
            response_style="balanced",
            default_expense_period="this_month",
            default_report_format="pdf",
            confirm_before_actions=True,
            weekly_summary=True,
            monthly_summary=True,
            budget_alerts=True,
            unusual_spending_alerts=False,
            theme="system",
        )

        self.db.add(preferences)
        self.db.commit()
        self.db.refresh(preferences)

        return preferences

    def update(
        self,
        user_id: uuid.UUID,
        data: UserPreferencesUpdate,
    ) -> UserPreferences:

        preferences = self.get_or_create(user_id)

        updates = data.model_dump(
            exclude_unset=True,
            exclude_none=True,
        )

        for field, value in updates.items():
            setattr(preferences, field, value)

        self.db.commit()
        self.db.refresh(preferences)

        return preferences

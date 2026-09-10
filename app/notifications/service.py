from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.user_preferences import UserPreferences
from app.notifications.generator import NotificationGenerator
from app.notifications.types import NotificationType
from datetime import datetime, timedelta, timezone

from app.models.notification import Notification


class NotificationService:
    def __init__(self, db: Session):
        self.db = db
        self.generator = NotificationGenerator(db)

    def get_preferences(
        self,
        user: User,
    ) -> UserPreferences | None:

        stmt = select(UserPreferences).where(UserPreferences.user_id == user.id)

        return self.db.scalar(stmt)

    def should_send(
        self,
        user: User,
        notification_type: NotificationType,
    ) -> bool:

        preferences = self.get_preferences(user)

        if preferences is None:
            return False

        preference_map = {
            NotificationType.WEEKLY_SUMMARY: preferences.weekly_summary,
            NotificationType.MONTHLY_SUMMARY: preferences.monthly_summary,
            NotificationType.BUDGET_ALERT: preferences.budget_alerts,
            NotificationType.UNUSUAL_SPENDING_ALERT: (
                preferences.unusual_spending_alerts
            ),
        }

        return preference_map[notification_type]

    def create_weekly_summary(
        self,
        user: User,
    ) -> Notification | None:

        if not self.should_send(
            user=user,
            notification_type=NotificationType.WEEKLY_SUMMARY,
        ):
            return None

        preferences = self.get_preferences(user)

        content = self.generator.generate_weekly_summary(
            user=user,
            preferences=preferences,
        )

        if not content:
            return None

        now = datetime.now(timezone.utc)

        period_end = now
        period_start = now - timedelta(days=7)

        notification = Notification(
            user_id=user.id,
            type=NotificationType.WEEKLY_SUMMARY,
            status="generated",
            content=content,
            period_start=period_start,
            period_end=period_end,
            generated_at=now,
        )

        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)

        return notification

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.user import User
from app.services.gmail_service import GmailService
from app.notifications.templates import build_weekly_summary_html


class NotificationDeliveryService:

    def __init__(self, db: Session):
        self.db = db
        self.gmail_service = GmailService(db)

    def send_email(
        self,
        notification: Notification,
    ) -> Notification:

        user = self.db.get(
            User,
            notification.user_id,
        )

        if not user:
            raise ValueError("User not found")

        subject = self._build_subject(notification)

        if notification.type == "weekly_summary":

            html_body = build_weekly_summary_html(
                notification=notification,
            )

            self.gmail_service.send_email(
                user_id=user.id,
                subject="Your Weekly Expense Summary",
                body=notification.content,
                html_body=html_body,
            )

        else:
            self.gmail_service.send_email(
                user_id=user.id,
                subject=subject,
                body=notification.content,
            )

        notification.status = "sent"
        notification.sent_at = datetime.now(timezone.utc)

        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        print(
            "DELIVERING NOTIFICATION",
            "notification_id=",
            notification.id,
            "notification_user_id=",
            notification.user_id,
            "gmail_user_id=",
            user.id,
        )

        return notification

    def _build_subject(
        self,
        notification: Notification,
    ) -> str:

        if notification.type == "weekly_summary":
            return "Your Weekly Expense Summary"

        if notification.type == "monthly_summary":
            return "Your Monthly Expense Summary"

        if notification.type == "budget_alert":
            return "Budget Alert"

        if notification.type == "unusual_spending_alert":
            return "Unusual Spending Alert"

        return "Expense Tracker Notification"

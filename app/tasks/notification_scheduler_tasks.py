from app.core.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.user import User
from app.models.user_preferences import UserPreferences
from app.notifications.service import NotificationService
from app.tasks.notification_tasks import deliver_notification


@celery_app.task
def schedule_weekly_summaries():
    db = SessionLocal()

    try:
        users = (
            db.query(User)
            .join(
                UserPreferences,
                UserPreferences.user_id == User.id,
            )
            .filter(
                UserPreferences.weekly_summary.is_(True),
            )
            .all()
        )

        queued = 0

        notification_service = NotificationService(db)

        for user in users:
            notification = notification_service.create_weekly_summary(
                user=user,
            )

            if notification:
                deliver_notification.delay(str(notification.id))
                queued += 1

        return {
            "success": True,
            "users_queued": queued,
        }

    finally:
        db.close()

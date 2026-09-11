from uuid import UUID

from app.core.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.notification import Notification
from app.notifications.notification_delivery_service import (
    NotificationDeliveryService,
)


@celery_app.task
def deliver_notification(notification_id: str):

    db = SessionLocal()

    try:
        notification = db.get(
            Notification,
            UUID(notification_id),
        )

        if not notification:
            raise ValueError("Notification not found")

        # Don't send the same notification twice.
        if notification.status == "sent":
            return {
                "success": True,
                "message": "Notification already sent",
            }

        if notification.status != "generated":
            return {
                "success": False,
                "message": (
                    f"Notification cannot be delivered "
                    f"because status is '{notification.status}'"
                ),
            }

        delivery_service = NotificationDeliveryService(db)

        notification = delivery_service.send_email(
            notification,
        )

        return {
            "success": True,
            "notification_id": str(notification.id),
            "status": notification.status,
        }

    except Exception:
        db.rollback()

        notification = db.get(
            Notification,
            UUID(notification_id),
        )

        if notification:
            notification.status = "failed"
            db.add(notification)
            db.commit()

        raise

    finally:
        db.close()

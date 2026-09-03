from app.core.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.google_connections import GoogleConnection
from app.tasks.gmail_tasks import sync_user_gmail


@celery_app.task
def schedule_gmail_syncs():
    db = SessionLocal()

    try:
        connections = (
            db.query(GoogleConnection)
            .filter(GoogleConnection.refresh_token.isnot(None))
            .all()
        )

        queued = 0

        for connection in connections:
            sync_user_gmail.delay(str(connection.user_id))
            queued += 1

        return {
            "success": True,
            "users_queued": queued,
        }

    finally:
        db.close()

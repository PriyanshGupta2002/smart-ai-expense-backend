import logging
from uuid import UUID

from app.core.celery_app import celery_app
from app.db.session import SessionLocal
from app.services.receipt_service import ReceiptService

logger = logging.getLogger(__name__)


@celery_app.task
def test_task(name: str):
    print(f"CELERY WORKS: {name}")

    return {
        "success": True,
        "name": name,
    }


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=60,
    retry_jitter=True,
    retry_kwargs={
        "max_retries": 3,
    },
    acks_late=True,
)
def process_receipt_task(
    self,
    receipt_id: str,
) -> None:
    """
    Process an uploaded receipt in the background.

    The task receives only the receipt ID because Celery
    arguments should be serializable.

    The worker creates its own database session and loads
    the Receipt from the database.
    """

    db = SessionLocal()

    try:
        parsed_receipt_id = UUID(receipt_id)

        logger.info(
            "Starting receipt processing",
            extra={
                "receipt_id": receipt_id,
                "task_id": self.request.id,
            },
        )

        service = ReceiptService(db=db)

        service.process_receipt_background(
            receipt_id=parsed_receipt_id,
        )

        logger.info(
            "Receipt processing completed",
            extra={
                "receipt_id": receipt_id,
                "task_id": self.request.id,
            },
        )

    except ValueError:
        logger.exception(
            "Invalid receipt ID: %s",
            receipt_id,
        )

        # Invalid UUID will never succeed on retry.
        return

    except Exception:
        logger.exception(
            "Receipt processing task failed",
            extra={
                "receipt_id": receipt_id,
                "task_id": self.request.id,
                "retry": self.request.retries,
            },
        )

        # Required for autoretry_for=(Exception,)
        raise

    finally:
        db.close()

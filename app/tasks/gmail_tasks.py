from uuid import UUID

from app.core.celery_app import celery_app
from app.db.session import SessionLocal
from app.services.gmail_sync_service import GmailSyncService
from app.services.gmail_ingestion_service import GmailIngestionService
from app.services.gmail_transaction_processor import GmailTransactionProcessor
from app.services.gmail_service import GmailService
from app.services.gmail_parser import GmailParser
from app.ai.gmail.transaction_classifier import GmailTransactionClassifier
from langchain_openrouter import ChatOpenRouter


@celery_app.task
def sync_user_gmail(user_id: str):
    db = SessionLocal()

    try:
        # -----------------------------------------
        # Build Gmail dependencies
        # -----------------------------------------

        gmail_service = GmailService(db)

        gmail_parser = GmailParser()

        ingestion_service = GmailIngestionService(
            email_service=gmail_service,
            gmail_parser=gmail_parser,
        )

        # -----------------------------------------
        # Build classifier
        # -----------------------------------------

        model = ChatOpenRouter(
            model="google/gemini-2.5-flash",
            temperature=0,
        )

        classifier = GmailTransactionClassifier(
            model=model,
        )

        # -----------------------------------------
        # Build transaction processor
        # -----------------------------------------

        transaction_processor = GmailTransactionProcessor(
            db=db,
            classifier=classifier,
        )

        # -----------------------------------------
        # Build sync service
        # -----------------------------------------

        sync_service = GmailSyncService(
            db=db,
            ingestion_service=ingestion_service,
            transaction_processor=transaction_processor,
        )

        # -----------------------------------------
        # Run sync
        # -----------------------------------------

        return sync_service.sync(
            user_id=UUID(user_id),
            max_results=50,
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()

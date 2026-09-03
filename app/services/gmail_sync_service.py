from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.google_connections import GoogleConnection
from app.services.gmail_ingestion_service import GmailIngestionService
from app.services.gmail_transaction_processor import GmailTransactionProcessor


class GmailSyncService:

    def __init__(
        self,
        db: Session,
        ingestion_service: GmailIngestionService,
        transaction_processor: GmailTransactionProcessor,
    ):
        self.db = db
        self.ingestion_service = ingestion_service
        self.transaction_processor = transaction_processor

    def sync(
        self,
        *,
        user_id: UUID,
        max_results: int = 50,
    ) -> dict:

        connection = self.db.execute(
            select(GoogleConnection).where(GoogleConnection.user_id == user_id)
        ).scalar_one_or_none()

        if not connection:
            raise ValueError("Google account is not connected.")

        # -----------------------------------------
        # 1. Capture sync start time
        # -----------------------------------------

        sync_started_at = datetime.now(timezone.utc)

        # -----------------------------------------
        # 2. Determine incremental sync point
        # -----------------------------------------

        last_sync = connection.last_gmail_sync_at

        # -----------------------------------------
        # 3. Fetch Gmail messages
        # -----------------------------------------

        messages = self.ingestion_service.get_transaction_messages(
            user_id=user_id,
            max_results=max_results,
            after=last_sync,
        )

        # -----------------------------------------
        # 4. Process transactions
        # -----------------------------------------

        results = self.transaction_processor.process_messages(
            user_id=user_id,
            messages=messages,
        )

        # -----------------------------------------
        # 5. Update sync timestamp
        # -----------------------------------------

        connection.last_gmail_sync_at = sync_started_at

        self.db.commit()

        return {
            "success": True,
            "messages_found": len(messages),
            "processed": len(results),
            "results": results,
            "last_gmail_sync_at": connection.last_gmail_sync_at,
        }

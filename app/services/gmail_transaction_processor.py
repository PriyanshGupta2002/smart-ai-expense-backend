from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.gmail.transaction_classifier import GmailTransactionClassifier
from app.ai.gmail.schemas import TransactionType
from app.models.receipt import Receipt


class GmailTransactionProcessor:
    """
    Converts parsed Gmail messages into expense records.

    Flow:

        parsed Gmail message
            ↓
        LLM classifier
            ↓
        TransactionCandidate
            ↓
        Receipt
    """

    def __init__(
        self,
        db: Session,
        classifier: GmailTransactionClassifier,
    ):
        self.db = db
        self.classifier = classifier

    def process_message(
        self,
        *,
        user_id: UUID,
        message: dict,
    ) -> dict:
        """
        Classify and process one parsed Gmail message.
        """

        message_id = message.get("message_id")

        # -----------------------------------------
        # 1. Prevent duplicate processing
        # -----------------------------------------

        if message_id:
            existing = self.db.execute(
                select(Receipt).where(Receipt.gmail_message_id == message_id)
            ).scalar_one_or_none()

            if existing:
                return {
                    "success": True,
                    "created": False,
                    "duplicate": True,
                    "receipt_id": str(existing.id),
                    "message": "Transaction already imported.",
                }

        # -----------------------------------------
        # 2. Get email text
        # -----------------------------------------

        text = (
            message.get("text")
            or message.get("plain_text")
            or message.get("html")
            or message.get("snippet")
            or ""
        )

        if not text.strip():
            return {
                "success": False,
                "created": False,
                "message": "Email does not contain readable content.",
            }

        # -----------------------------------------
        # 3. Classify email with LLM
        # -----------------------------------------

        candidate = self.classifier.classify(
            subject=message.get("subject"),
            sender=message.get("sender"),
            date=(message.get("date").isoformat() if message.get("date") else None),
            text=text,
        )

        # -----------------------------------------
        # 4. Ignore non-transactions
        # -----------------------------------------

        if not candidate.is_transaction:
            return {
                "success": True,
                "created": False,
                "transaction": False,
                "message": "Email is not a financial transaction.",
            }

        # -----------------------------------------
        # 5. Ignore income
        # -----------------------------------------

        if candidate.transaction_type == TransactionType.INCOME:
            return {
                "success": True,
                "created": False,
                "transaction": True,
                "transaction_type": "income",
                "message": "Income transaction ignored.",
            }

        # -----------------------------------------
        # 6. Ignore transfers
        # -----------------------------------------

        if candidate.transaction_type == TransactionType.TRANSFER:
            return {
                "success": True,
                "created": False,
                "transaction": True,
                "transaction_type": "transfer",
                "message": "Transfer transaction ignored.",
            }

        # -----------------------------------------
        # 7. Only expenses reach Receipt creation
        # -----------------------------------------

        if candidate.transaction_type != TransactionType.EXPENSE:
            return {
                "success": True,
                "created": False,
                "transaction": True,
                "transaction_type": str(candidate.transaction_type),
                "message": "Transaction type is not an expense.",
            }

        # -----------------------------------------
        # 8. Validate amount
        # -----------------------------------------

        if candidate.amount is None:
            return {
                "success": False,
                "created": False,
                "message": "Expense transaction has no amount.",
            }

        if candidate.amount <= 0:
            return {
                "success": False,
                "created": False,
                "message": "Expense amount is invalid.",
            }

        # -----------------------------------------
        # 9. Create Receipt
        # -----------------------------------------

        receipt = Receipt(
            user_id=user_id,
            # Gmail source
            source="gmail",
            gmail_message_id=message_id,
            # Gmail emails don't necessarily have receipt images
            imagekit_file_id=None,
            image_url=None,
            # Transaction information
            merchant_name=candidate.merchant_name,
            purchase_datetime=candidate.transaction_date or message.get("date"),
            # Classification
            expense_type=candidate.category,
            classification_confidence=Decimal(str(candidate.confidence)),
            # Money
            total=candidate.amount,
            currency=candidate.currency,
            # Payment
            payment_method=candidate.payment_method,
            # Description
            notes=candidate.description,
            # Processing
            processing_status="COMPLETED",
            validation_status="VALIDATED",
            validation_confidence=Decimal(str(candidate.confidence)),
        )

        self.db.add(receipt)
        self.db.commit()
        self.db.refresh(receipt)

        return {
            "success": True,
            "created": True,
            "duplicate": False,
            "transaction": True,
            "transaction_type": "expense",
            "receipt_id": str(receipt.id),
            "merchant_name": candidate.merchant_name,
            "amount": str(candidate.amount),
            "currency": candidate.currency,
            "category": candidate.category,
        }

    def process_messages(
        self,
        *,
        user_id: UUID,
        messages: list[dict],
    ) -> list[dict]:
        """
        Process multiple Gmail messages.
        """

        results = []

        for message in messages:
            try:
                result = self.process_message(
                    user_id=user_id,
                    message=message,
                )

                results.append(
                    {
                        "message_id": message.get("message_id"),
                        **result,
                    }
                )

            except Exception as e:
                self.db.rollback()

                results.append(
                    {
                        "message_id": message.get("message_id"),
                        "success": False,
                        "created": False,
                        "error": str(e),
                    }
                )

        return results

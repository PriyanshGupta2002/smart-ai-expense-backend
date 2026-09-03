from langchain_openrouter import ChatOpenRouter

from app.ai.gmail.prompt import (
    TRANSACTION_CLASSIFIER_SYSTEM_PROMPT,
)
from app.ai.gmail.schemas import TransactionCandidate


class GmailTransactionClassifier:

    def __init__(
        self,
        model: ChatOpenRouter,
    ):
        self.model = model

        self.structured_model = model.with_structured_output(
            TransactionCandidate,
        )

    def classify(
        self,
        *,
        subject: str | None,
        sender: str | None,
        date: str | None,
        text: str,
    ) -> TransactionCandidate:

        user_message = f"""
EMAIL INFORMATION

Subject:
{subject or "N/A"}

Sender:
{sender or "N/A"}

Date:
{date or "N/A"}

Email content:
{text}
"""

        response = self.structured_model.invoke(
            [
                {
                    "role": "system",
                    "content": TRANSACTION_CLASSIFIER_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": user_message,
                },
            ]
        )

        return response

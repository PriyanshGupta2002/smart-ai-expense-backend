from app.services.gmail_service import GmailService
from uuid import UUID
from app.services.gmail_parser import GmailParser
from datetime import datetime


class GmailIngestionService:
    def __init__(self, email_service: GmailService, gmail_parser: GmailParser):
        self.email_service = email_service
        self.gmail_parser = gmail_parser

    def get_transaction_messages(
        self,
        user_id: UUID,
        max_results: int = 50,
        after: datetime | None = None,
    ):
        query_parts = [
            '"UPI"',
            '"transaction"',
            '"debited"',
            '"credited"',
            '"payment successful"',
            '"payment received"',
            '"purchase"',
        ]

        query = "(" + " OR ".join(query_parts) + ")"

        if after:
            query += f" after:{int(after.timestamp())}"

        messages = self.email_service.search_messages(
            user_id,
            query=query,
            max_results=max_results,
        )

        results = []

        for message in messages:
            message_id = message["id"]

            full_message = self.email_service.get_message(
                user_id,
                message_id,
            )

            parsed_message = self.gmail_parser.parse_message(full_message)

            if parsed_message:
                results.append(parsed_message)

        return results

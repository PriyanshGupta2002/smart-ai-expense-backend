from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

ALLOWED_TABLES = {
    "receipts",
    "receipt_items",
}


@dataclass
class ExpenseAgentContext:
    user_id: UUID
    db: Session

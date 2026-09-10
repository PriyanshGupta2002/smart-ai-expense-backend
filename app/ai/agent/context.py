from dataclasses import dataclass
from uuid import UUID
from app.services.storage_service import StorageService
from sqlalchemy.orm import Session
from app.models.user_preferences import UserPreferences

ALLOWED_TABLES = {"receipts", "receipt_items", "budgets"}


@dataclass
class ExpenseAgentContext:
    user_id: UUID
    db: Session
    storage: StorageService
    preferences: UserPreferences | None

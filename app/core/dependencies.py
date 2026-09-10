from collections.abc import Generator

from fastapi import Depends, HTTPException, Request
from langchain_openrouter import ChatOpenRouter
from sqlalchemy.orm import Session

from app.services.gmail_sync_service import GmailSyncService
from app.services.gmail_transaction_processor import GmailTransactionProcessor
from app.ai.gmail.transaction_classifier import GmailTransactionClassifier
from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import decode_token
import uuid
import jwt
from fastapi import Depends
from sqlalchemy.orm import Session
from functools import lru_cache
import redis
from app.services.auth_service import AuthService
from app.services.gmail_parser import GmailParser
from app.services.receipt_service import ReceiptService
from app.services.dashboard_service import DashboardService
from app.services.insights_service import InsightService
from app.services.chat_service import ChatService
from app.services.thread_service import ThreadService
from app.services.user_service import UserService
from fastapi import Request
from app.services.storage_service import StorageService
from app.core.config import settings
from imagekitio import ImageKit
from functools import lru_cache
from app.services.budget_service import BudgetService
from app.ai.classifiers.scope_classifier import ScopeClassifier
from app.services.gmail_service import GmailService
from app.services.gmail_ingestion_service import GmailIngestionService
from app.services.whatsapp_connection_service import WhatsAppConnectionService
from app.services.whatsapp_service import WhatsAppService
from app.services.user_preferences_service import UserPreferencesService

redis_client = redis.Redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
)


@lru_cache
def get_scope_classifier():

    return ScopeClassifier()


@lru_cache
def _get_imagekit_client() -> ImageKit:
    return ImageKit(
        private_key=settings.IMAGEKIT_PRIVATE_KEY,
    )


def get_redis():
    return redis_client


def get_expense_agent(request: Request):
    return request.app.state.expense_agent


def get_storage_service() -> StorageService:
    imagekit_client = _get_imagekit_client()
    return StorageService(imagekit=imagekit_client)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:

    token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
        )

    try:
        payload = decode_token(token)

        if payload.get("type") != "access":
            raise HTTPException(
                status_code=401,
                detail="Invalid token type",
            )

        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Invalid token",
            )

    except jwt.PyJWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
        )

    user = db.get(
        User,
        uuid.UUID(user_id),
    )

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found",
        )

    return user


def get_auth_service(
    db: Session = Depends(get_db),
) -> AuthService:

    return AuthService(db)


def get_receipt_service(
    db: Session = Depends(get_db),
):
    return ReceiptService(db)


def get_dashboard_service(
    db: Session = Depends(get_db),
):
    return DashboardService(db)


def get_insight_service(
    db: Session = Depends(get_db),
):
    return InsightService(db)


def get_user_preferences_service(db: Session = Depends(get_db)):
    return UserPreferencesService(db=db)


def get_chat_service(
    db: Session,
    agent=Depends(get_expense_agent),
    storage=Depends(get_storage_service),
    classifier=Depends(get_scope_classifier),
):
    return ChatService(db, agent, storage, classifier)


def get_thread_service(
    db: Session,
):
    return ThreadService(db)


def get_budget_service(
    db: Session = Depends(get_db),
):
    return BudgetService(db)


def get_user_service(
    db: Session = Depends(get_db),
):
    return UserService(db)


def get_gmail_service(
    db: Session = Depends(get_db),
) -> GmailService:

    return GmailService(db)


def get_gmail_parser() -> GmailParser:
    return GmailParser()


def get_gmail_ingestion_service(
    gmail_service: GmailService = Depends(get_gmail_service),
    gmail_parser: GmailParser = Depends(get_gmail_parser),
):
    return GmailIngestionService(email_service=gmail_service, gmail_parser=gmail_parser)


def get_gmail_transaction_classifier() -> GmailTransactionClassifier:
    model = ChatOpenRouter(
        model="google/gemini-2.5-flash",
        temperature=0,
    )

    return GmailTransactionClassifier(
        model=model,
    )


def get_gmail_transaction_processor(
    db=Depends(get_db),
    classifier=Depends(get_gmail_transaction_classifier),
) -> GmailTransactionProcessor:

    return GmailTransactionProcessor(
        db=db,
        classifier=classifier,
    )


def get_gmail_sync_service(
    db=Depends(get_db),
    ingestion_service=Depends(get_gmail_ingestion_service),
    transaction_processor=Depends(get_gmail_transaction_processor),
):
    return GmailSyncService(
        db=db,
        ingestion_service=ingestion_service,
        transaction_processor=transaction_processor,
    )


def get_whatsapp_service() -> WhatsAppService:
    return WhatsAppService(
        base_url=settings.OPENWA_URL,
        api_key=settings.OPENWA_API_KEY,
    )


def get_whatsapp_connection_service(
    db: Session = Depends(get_db),
    whatsapp_service: WhatsAppService = Depends(get_whatsapp_service),
) -> WhatsAppConnectionService:
    return WhatsAppConnectionService(db=db, whatsapp_service=whatsapp_service)

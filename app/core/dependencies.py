from collections.abc import Generator

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import decode_token
import uuid
import jwt
from fastapi import Depends
from sqlalchemy.orm import Session
from functools import lru_cache

from app.services.auth_service import AuthService
from app.services.receipt_service import ReceiptService
from app.services.dashboard_service import DashboardService
from app.services.insights_service import InsightService
from app.services.chat_service import ChatService
from app.services.thread_service import ThreadService
from fastapi import Request
from app.services.storage_service import StorageService
from app.core.config import settings
from imagekitio import ImageKit
from functools import lru_cache
from app.services.budget_service import BudgetService
from app.ai.classifiers.scope_classifier import ScopeClassifier


@lru_cache
def get_scope_classifier():

    return ScopeClassifier()


@lru_cache
def _get_imagekit_client() -> ImageKit:
    return ImageKit(
        private_key=settings.IMAGEKIT_PRIVATE_KEY,
    )


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

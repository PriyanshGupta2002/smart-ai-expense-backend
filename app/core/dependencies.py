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

from app.services.auth_service import AuthService
from app.services.receipt_service import ReceiptService
from app.services.dashboard_service import DashboardService
from app.services.insights_service import InsightService
from app.services.chat_service import ChatService


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
    db: Session,
):
    return InsightService(db)


def get_chat_service(
    db: Session,
):
    return ChatService(db)

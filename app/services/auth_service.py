import hmac
import uuid

import jwt

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.models.user import User
from app.models.user_session import UserSession
from app.schemas.auth import LoginRequest, RegisterRequest
from app.utils.auth_cookie import (
    clear_auth_cookies,
    set_auth_cookies,
)


class AuthService:

    def __init__(self, db: Session):
        self.db = db

    # ==========================================
    # Register
    # ==========================================

    def register(
        self,
        payload: RegisterRequest,
    ) -> User:

        email = payload.email.lower()

        existing = self.db.scalar(select(User).where(User.email == email))

        if existing:
            raise HTTPException(
                status_code=409,
                detail="Email already exists",
            )

        user = User(
            email=email,
            password_hash=hash_password(payload.password),
            first_name=payload.first_name,
            last_name=payload.last_name,
        )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        return user

    # ==========================================
    # Login
    # ==========================================

    def login(
        self,
        data: LoginRequest,
        response: Response,
    ) -> User:

        email = data.email.lower()

        user = self.db.scalar(select(User).where(User.email == email))

        if user is None or not verify_password(
            data.password,
            user.password_hash,
        ):
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials",
            )

        session = UserSession(
            user_id=user.id,
            refresh_token_hash="",
            expires_at=(
                datetime.now(timezone.utc)
                + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
            ),
        )

        self.db.add(session)

        # Generate session.id without committing yet
        self.db.flush()

        access_token = create_access_token(user.id)

        refresh_token = create_refresh_token(
            user.id,
            session.id,
        )

        session.refresh_token_hash = hash_refresh_token(refresh_token)

        self.db.commit()

        set_auth_cookies(
            response=response,
            access_token=access_token,
            refresh_token=refresh_token,
        )

        return user

    # ==========================================
    # Refresh
    # ==========================================

    def refresh(
        self,
        refresh_token: str | None,
        response: Response,
    ) -> None:

        if not refresh_token:
            raise HTTPException(
                status_code=401,
                detail="Refresh token missing",
            )

        try:
            payload = decode_token(refresh_token)

            if payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=401,
                    detail="Invalid token type",
                )

            session_id = uuid.UUID(payload["sid"])

            user_id = uuid.UUID(payload["sub"])

        except (
            jwt.PyJWTError,
            KeyError,
            ValueError,
        ):
            raise HTTPException(
                status_code=401,
                detail="Invalid refresh token",
            )

        session = self.db.get(
            UserSession,
            session_id,
        )

        if (
            session is None
            or session.revoked
            or session.user_id != user_id
            or session.expires_at <= datetime.now(timezone.utc)
        ):
            raise HTTPException(
                status_code=401,
                detail="Session expired or revoked",
            )

        supplied_hash = hash_refresh_token(refresh_token)

        if not hmac.compare_digest(
            supplied_hash,
            session.refresh_token_hash,
        ):
            # An old/unknown refresh token was presented
            # for this session.
            session.revoked = True
            self.db.commit()

            raise HTTPException(
                status_code=401,
                detail="Invalid refresh token",
            )

        new_access_token = create_access_token(user_id)

        new_refresh_token = create_refresh_token(
            user_id,
            session.id,
        )

        # Rotate refresh token
        session.refresh_token_hash = hash_refresh_token(new_refresh_token)

        session.expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        self.db.commit()

        set_auth_cookies(
            response=response,
            access_token=new_access_token,
            refresh_token=new_refresh_token,
        )

    # ==========================================
    # Logout
    # ==========================================

    def logout(
        self,
        refresh_token: str | None,
        response: Response,
    ) -> None:

        if refresh_token:
            try:
                payload = decode_token(refresh_token)

                if payload.get("type") == "refresh":
                    session_id = uuid.UUID(payload["sid"])

                    session = self.db.get(
                        UserSession,
                        session_id,
                    )

                    if session:
                        session.revoked = True
                        self.db.commit()

            except (
                jwt.PyJWTError,
                KeyError,
                ValueError,
            ):
                pass

        clear_auth_cookies(response)

import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, logger
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.core.config import settings
from app.core.dependencies import (
    get_current_user,
    get_db,
    get_gmail_sync_service,
    get_redis,
)
from app.models.user import User
from app.models.google_connections import GoogleConnection
from app.services.gmail_sync_service import GmailSyncService
from app.services.google_connection_service import GoogleConnectionService
from app.services.google_oauth_service import GoogleOAuthService
from app.services.gmail_service import GmailService
from app.tasks.gmail_tasks import sync_user_gmail

router = APIRouter(
    prefix="/api/auth/google",
    tags=["google"],
)


@router.get("/connect")
def connect_google(
    user: User = Depends(get_current_user),
    redis=Depends(get_redis),
):
    oauth_service = GoogleOAuthService()

    state = oauth_service.generate_state()

    authorization_url, code_verifier = oauth_service.get_authorization_url(
        state=state,
    )

    # state -> user
    redis.setex(
        f"google_oauth_state:{state}",
        600,
        str(user.id),
    )

    # state -> code verifier
    redis.setex(
        f"google_oauth_verifier:{state}",
        600,
        code_verifier,
    )

    return RedirectResponse(
        url=authorization_url,
        status_code=307,
    )


@router.get("/callback")
def google_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
    redis=Depends(get_redis),
):
    if error:
        raise HTTPException(
            status_code=400,
            detail=f"Google OAuth error: {error}",
        )

    if not code or not state:
        raise HTTPException(
            status_code=400,
            detail="Missing OAuth code or state",
        )

    state_key = f"google_oauth_state:{state}"
    verifier_key = f"google_oauth_verifier:{state}"

    user_id = redis.get(state_key)
    code_verifier = redis.get(verifier_key)

    if not user_id:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired OAuth state",
        )

    if not code_verifier:
        raise HTTPException(
            status_code=400,
            detail="Missing or expired OAuth code verifier",
        )

    # OAuth values are single-use
    redis.delete(state_key)
    redis.delete(verifier_key)

    try:
        user_id = UUID(user_id)

        oauth_service = GoogleOAuthService()

        credentials = oauth_service.exchange_code(
            code=code,
            code_verifier=code_verifier,
        )
        connection_service = GoogleConnectionService(db)

        connection_service.save_connection(
            user_id=user_id,
            access_token=credentials.token,
            refresh_token=credentials.refresh_token,
            token_expires_at=credentials.expiry,
            scopes=list(credentials.scopes or []),
        )

    except Exception as e:
        print("GOOGLE OAUTH ERROR:", repr(e))

        raise HTTPException(
            status_code=500,
            detail="Failed to authenticate with Google",
        )

    # Save credentials in next step...

    return RedirectResponse(
        url=f"{settings.FRONTEND_URL}/settings/profile",
        status_code=303,
    )


@router.get("/status")
def google_status(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return whether the authenticated user has connected Google.
    """

    service = GoogleConnectionService(db)

    connection = service.get_by_user_id(
        user.id,
    )

    return {
        "connected": connection is not None,
    }


@router.delete("/disconnect")
def disconnect_google(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Disconnect Google from the authenticated user's account.
    """

    service = GoogleConnectionService(db)

    disconnected = service.disconnect(
        user.id,
    )

    if not disconnected:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Google account is not connected",
        )

    return {
        "message": "Google account disconnected",
    }


@router.get("/gmail-tools")
def gmail_tools(
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    gmail_service = GmailService(db)

    tools = gmail_service.get_tools(user.id)

    return {
        "connected": bool(tools),
        "tools": [tool.name for tool in tools],
    }


@router.post("/gmail/sync")
def sync_gmail(
    user=Depends(get_current_user),
    sync_service: GmailSyncService = Depends(get_gmail_sync_service),
):
    sync_user_gmail.delay(str(user.id))
    # try:
    #     return sync_service.sync(
    #         user_id=user.id,
    #         max_results=50,
    #     )

    # except ValueError as e:
    #     raise HTTPException(
    #         status_code=400,
    #         detail=str(e),
    #     )

    # except Exception:
    #     logger.exception("Gmail sync failed")

    #     raise HTTPException(
    #         status_code=500,
    #         detail="Failed to sync Gmail",
    #     )

from fastapi import APIRouter, Depends, Request, UploadFile, HTTPException
from sqlalchemy.orm import Session
from app.core.dependencies import (
    get_db,
    get_current_user,
    get_whatsapp_service,
    get_whatsapp_connection_service,
)
from app.services import whatsapp_service
from app.services.whatsapp_connection_service import WhatsAppConnectionService
from app.services.whatsapp_service import WhatsAppService
from app.core.config import settings
from app.models.whatsapp_connections import WhatsAppConnection
from datetime import datetime, timezone

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])


@router.post("/connect")
async def connect_whatsapp(
    user=Depends(get_current_user),
    connection_service: WhatsAppConnectionService = Depends(
        get_whatsapp_connection_service
    ),
    whatsapp_service: WhatsAppService = Depends(get_whatsapp_service),
):
    connection = connection_service.create_connection(user.id)

    # If we already have a session, don't create another one.
    if connection.session_id:
        session = await whatsapp_service.get_session(connection.session_id)

        return {
            "success": True,
            "session_id": connection.session_id,
            "status": session.get("status"),
            "connected": connection.connected,
        }

    # Create a unique OpenWA session name.
    session_name = f"expense-ai-{user.id}"

    session = await whatsapp_service.create_session(name=session_name)

    session_id = session["id"]

    # Save OpenWA session ID in our DB.
    connection_service.set_session_id(
        connection,
        session_id,
    )

    # Register webhook for this session.
    await whatsapp_service.create_webhook(
        session_id=session_id, webhook_url=settings.WHATSAPP_WEBHOOK_URL
    )

    # Start the WhatsApp session.
    await whatsapp_service.start_session(session_id)

    # Get QR.
    qr = await whatsapp_service.get_qr(session_id)

    return {
        "success": True,
        "session_id": session_id,
        "status": "qr_ready",
        "qr": qr,
    }


@router.post("/whatsapp/test")
async def test_whatsapp(
    user=Depends(get_current_user),
    connection_service: WhatsAppConnectionService = Depends(
        get_whatsapp_connection_service
    ),
    whatsapp_service: WhatsAppService = Depends(get_whatsapp_service),
):
    connection = connection_service.get_by_user_id(user.id)

    if not connection:
        raise HTTPException(
            status_code=404,
            detail="WhatsApp is not connected.",
        )

    if not connection.connected:
        raise HTTPException(
            status_code=400,
            detail="WhatsApp is not connected.",
        )

    if not connection.phone_number:
        raise HTTPException(
            status_code=400,
            detail="WhatsApp phone number is not available.",
        )

    result = await whatsapp_service.send_text(
        session_name=connection.session_name,
        chat_id=f"{connection.phone_number}@c.us",
        text="Hello from Expense AI 🚀",
    )

    return {
        "success": True,
        "whatsapp": result,
    }


@router.post("/webhook")
async def whatsapp_webhook(
    request: Request,
    db: Session = Depends(get_db),
    whatsapp_service: WhatsAppService = Depends(get_whatsapp_service),
):
    payload = await request.json()

    print("WHATSAPP WEBHOOK:")
    print(payload)

    # ---------------------------------------------------------
    # 1. Get event information
    # ---------------------------------------------------------

    event = payload.get("event")

    if not event:
        return {
            "success": True,
            "message": "Event missing",
        }

    # We currently only care about session status events.
    if event != "session.status":
        return {
            "success": True,
            "message": "Event ignored",
        }

    # ---------------------------------------------------------
    # 2. Extract session information
    # ---------------------------------------------------------

    session_id = payload.get("sessionId")

    data = payload.get("data") or {}

    # OpenWA also sends the session ID inside data.
    # Prefer that if available.
    session_id = data.get("sessionId") or session_id

    status = data.get("status")

    if not session_id or not status:
        return {
            "success": True,
            "message": "Invalid session status payload",
        }

    # ---------------------------------------------------------
    # 3. Find our WhatsApp connection
    # ---------------------------------------------------------

    connection = (
        db.query(WhatsAppConnection)
        .filter(WhatsAppConnection.session_id == session_id)
        .first()
    )

    if not connection:
        # This can happen if:
        # - OpenWA has an old session
        # - user deleted the connection from our DB
        # - webhook arrived after the connection was deleted
        print(f"WhatsApp connection not found for session: " f"{session_id}")

        return {
            "success": True,
            "message": "Connection not found",
        }

    # ---------------------------------------------------------
    # 4. Handle session status
    # ---------------------------------------------------------

    if status == "ready":

        connection.connected = True

        connection.connected_at = datetime.now(timezone.utc)

        session = await whatsapp_service.get_session(session_id)
        phone_number = session.get("phone")
        if phone_number:
            connection.phone_number = phone_number
        db.commit()
        print(f"WhatsApp connected for user " f"{connection.user_id}")

    elif status in {
        "disconnected",
        "logged_out",
        "failed",
    }:

        connection.connected = False

        print(f"WhatsApp disconnected for user " f"{connection.user_id}: {status}")

    # For statuses such as:
    #
    # authenticating
    # qr_ready
    # starting
    #
    # we don't change the connection state.

    # ---------------------------------------------------------
    # 5. Persist
    # ---------------------------------------------------------

    db.commit()

    return {
        "success": True,
    }


@router.get("/status")
async def whatsapp_status(
    user=Depends(get_current_user),
    connection_service: WhatsAppConnectionService = Depends(
        get_whatsapp_connection_service
    ),
):
    connection = connection_service.get_by_user_id(user.id)

    if not connection:
        return {
            "connected": False,
            "phone_number": None,
        }

    return {
        "connected": connection.connected,
        "phone_number": connection.phone_number,
    }


@router.post("/disconnect")
async def disconnect_whatsapp(
    user=Depends(get_current_user),
    connection_service: WhatsAppConnectionService = Depends(
        get_whatsapp_connection_service
    ),
):
    success = await connection_service.disconnect(user.id)

    if not success:
        raise HTTPException(
            status_code=400,
            detail="WhatsApp is not connected.",
        )

    return {
        "success": True,
    }

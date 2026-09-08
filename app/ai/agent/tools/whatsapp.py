import httpx

from langchain.tools import tool, ToolRuntime

from app.ai.agent.context import ExpenseAgentContext
from app.models.whatsapp_connections import WhatsAppConnection
from app.core.config import settings


@tool
def send_whatsapp_message(
    message: str,
    runtime: ToolRuntime[ExpenseAgentContext],
) -> str:
    """
    Send a message to the user's connected WhatsApp number.

    Use this tool when the user explicitly asks to send
    information or expense summaries to WhatsApp.
    """

    db = runtime.context.db
    user_id = runtime.context.user_id

    connection = (
        db.query(WhatsAppConnection)
        .filter(
            WhatsAppConnection.user_id == user_id,
            WhatsAppConnection.connected.is_(True),
        )
        .first()
    )

    if not connection:
        return "WhatsApp is not connected. Please connect WhatsApp from Settings first."

    if not connection.session_id:
        return "WhatsApp session is missing. Please reconnect WhatsApp."

    if not connection.phone_number:
        return "WhatsApp phone number is missing. Please reconnect WhatsApp."

    chat_id = f"{connection.phone_number}@c.us"

    url = (
        f"{settings.OPENWA_URL}/api/sessions/"
        f"{connection.session_id}/messages/send-text"
    )

    headers = {
        "X-API-Key": settings.OPENWA_API_KEY,
        "Content-Type": "application/json",
    }

    payload = {
        "chatId": chat_id,
        "text": message,
    }

    try:
        with httpx.Client(timeout=30) as client:
            response = client.post(
                url,
                headers=headers,
                json=payload,
            )

            response.raise_for_status()

        return "Message successfully sent to WhatsApp."

    except httpx.HTTPError:
        return (
            "I couldn't send the message to WhatsApp. "
            "Please make sure your WhatsApp connection is active."
        )

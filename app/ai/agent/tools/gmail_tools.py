# app/ai/agent/tools/gmail_tools.py

from langchain.tools import tool, ToolRuntime

from app.ai.agent.context import ExpenseAgentContext
from app.services.gmail_service import GmailService


@tool
def send_email(
    subject: str,
    body: str,
    runtime: ToolRuntime[ExpenseAgentContext],
) -> str:
    """
    Send an email using the user's connected Gmail account.

    Use this when the user asks to send information, reports,
    expense summaries, or other content through Gmail.
    """

    user_id = runtime.context.user_id
    db = runtime.context.db

    gmail_service = GmailService(db)

    return gmail_service.send_email(
        user_id=user_id,
        subject=subject,
        body=body,
    )

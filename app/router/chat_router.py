from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.schemas.chat import ChatRequest
from app.core.dependencies import (
    get_current_user,
    get_chat_service,
    get_db,
)

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("")
def chat(
    payload: ChatRequest,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    service = get_chat_service(db=db)

    return StreamingResponse(
        service.stream_chat(
            user=user,
            message=payload.message,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )

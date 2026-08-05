from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from fastapi.responses import StreamingResponse
from app.core.dependencies import get_scope_classifier


from app.schemas.chat import ChatRequest

from app.core.dependencies import (
    get_current_user,
    get_chat_service,
    get_thread_service,
    get_db,
    get_expense_agent,
    get_storage_service,
)

from app.services.storage_service import StorageService

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.post("/{thread_id}")
def chat(
    thread_id: UUID,
    payload: ChatRequest,
    user=Depends(get_current_user),
    db=Depends(get_db),
    agent=Depends(get_expense_agent),
    storage: StorageService = Depends(get_storage_service),
    classifier=Depends(get_scope_classifier),
):
    thread_service = get_thread_service(db=db)

    thread = thread_service.get_thread(
        user=user,
        thread_id=thread_id,
    )

    if thread is None:
        raise HTTPException(
            status_code=404,
            detail="Thread not found",
        )

    service = get_chat_service(
        db=db, agent=agent, storage=storage, classifier=classifier
    )

    return StreamingResponse(
        service.stream_chat(
            user=user,
            thread=thread,
            message=payload.message,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )

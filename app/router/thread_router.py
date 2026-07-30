from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from app.core.dependencies import (
    get_current_user,
    get_db,
    get_thread_service,
)

from app.schemas.thread import (
    ThreadListResponse,
    ThreadResponse,
    ThreadUpdate,
)

from app.schemas.message import (
    MessageListResponse,
)

router = APIRouter(
    prefix="/threads",
    tags=["Threads"],
)


@router.post(
    "",
    response_model=ThreadResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_thread(
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    service = get_thread_service(db=db)

    return service.create_thread(user=user)


@router.get(
    "",
    response_model=ThreadListResponse,
)
def get_threads(
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    service = get_thread_service(db=db)

    threads = service.get_threads(user=user)

    return {"threads": threads}


@router.get(
    "/{thread_id}",
    response_model=ThreadResponse,
)
def get_thread(
    thread_id: UUID,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    service = get_thread_service(db=db)

    thread = service.get_thread(
        user=user,
        thread_id=thread_id,
    )

    if thread is None:
        raise HTTPException(
            status_code=404,
            detail="Thread not found",
        )

    return thread


@router.get(
    "/{thread_id}/messages",
    response_model=MessageListResponse,
)
def get_thread_messages(
    thread_id: UUID,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    service = get_thread_service(db=db)

    thread = service.get_thread(
        user=user,
        thread_id=thread_id,
    )

    if thread is None:
        raise HTTPException(
            status_code=404,
            detail="Thread not found",
        )

    messages = service.get_messages(
        user=user,
        thread_id=thread_id,
    )

    return {"messages": messages}


@router.patch(
    "/{thread_id}",
    response_model=ThreadResponse,
)
def update_thread(
    thread_id: UUID,
    payload: ThreadUpdate,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    service = get_thread_service(db)

    thread = service.update_thread(
        user=user,
        thread_id=thread_id,
        title=payload.title,
    )

    if thread is None:
        raise HTTPException(
            status_code=404,
            detail="Thread not found",
        )

    return thread


@router.delete(
    "/{thread_id}",
    status_code=204,
)
def delete_thread(
    thread_id: UUID,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    service = get_thread_service(db)

    deleted = service.delete_thread(
        user=user,
        thread_id=thread_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Thread not found",
        )

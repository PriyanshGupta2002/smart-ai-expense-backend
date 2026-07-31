from fastapi import APIRouter, Depends, File, UploadFile, Query, status, HTTPException
from uuid import UUID
from app.core.dependencies import get_current_user, get_receipt_service, get_db
from app.tasks.receipt_tasks import process_receipt_task

from app.models.user import User

from app.schemas.receipt import ReceiptResponse, ReceiptListResponse
from typing import Annotated
from app.utils.date_range import DashboardPeriod
from app.services.receipt_service import (
    ReceiptService,
)

router = APIRouter(
    prefix="/receipts",
    tags=["Receipts"],
)


@router.post(
    "",
    response_model=ReceiptResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def upload_receipt(
    file: UploadFile,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    service = ReceiptService(db=db)

    receipt = service.upload_receipt(
        file=file,
        user=user,
    )

    process_receipt_task.delay(str(receipt.id))

    return receipt


@router.get(
    "",
    response_model=ReceiptListResponse,
)
def get_receipts(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    period: DashboardPeriod | None = None,
    category: str | None = None,
    search: Annotated[str | None, Query(max_length=100)] = None,
    status: str | None = None,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    service = ReceiptService(db)

    return service.get_receipts(
        user=user,
        page=page,
        page_size=page_size,
        period=period,
        category=category,
        search=search,
        status=status,
    )


@router.delete(
    "/{receipt_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_receipt(
    receipt_id: UUID,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    service = get_receipt_service(db=db)

    deleted = service.delete_receipt(
        user=user,
        receipt_id=receipt_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receipt not found",
        )

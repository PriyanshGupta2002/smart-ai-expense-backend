# app/routers/notifications.py

from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.notifications.service import NotificationService
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)


@router.get("/weekly-summary")
def generate_weekly_summary(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notification_service = NotificationService(db=db)

    summary = notification_service.create_weekly_summary(
        user=user,
    )

    if summary is None:
        raise HTTPException(
            status_code=400,
            detail="Weekly summary notifications are disabled.",
        )

    return {
        "type": "weekly_summary",
        "summary": summary,
    }

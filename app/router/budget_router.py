from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import (
    get_budget_service,
    get_current_user,
    get_db,
)
from app.models.user import User
from app.schemas.budget import BudgetRequest, CurrentBudgetResponse
from app.services.budget_service import BudgetService

router = APIRouter(
    prefix="/budget",
    tags=["Budget"],
)


@router.get(
    "/current",
    response_model=CurrentBudgetResponse | None,
)
def get_current_budget(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    budget_service: BudgetService = get_budget_service(db=db)

    budget = budget_service.get_current_budget(
        user=user,
    )

    if budget is None:
        return None

    return CurrentBudgetResponse.model_validate(budget)


@router.put(
    "/current",
)
def set_current_budget(
    request: BudgetRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    budget_service: BudgetService = get_budget_service(db=db)

    budget = budget_service.upsert_current_budget(
        user=user,
        amount=request.amount,
    )

    return budget

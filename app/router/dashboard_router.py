from fastapi import APIRouter, Depends
from app.core.dependencies import (
    get_current_user,
    get_dashboard_service,
    get_db,
    get_insight_service,
)
from app.schemas.dashboard import (
    DashboardSummaryResponse,
    CategoryDistributionResponse,
    TopMerchantResponse,
    SpendingTrendResponse,
    DashboardInsightsResponse,
)
from app.utils.date_range import DashboardPeriod

from app.ai.insight.schema import AIInsights

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get("/dashboard-summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(user=Depends(get_current_user), db=Depends(get_db)):
    dashboard_service = get_dashboard_service(db=db)
    data = dashboard_service.get_dashboard_summary(user=user)
    return DashboardSummaryResponse(**data)


@router.get(
    "/categories",
    response_model=CategoryDistributionResponse,
)
def get_category_distribution(
    user=Depends(get_current_user),
    db=Depends(get_db),
    period: DashboardPeriod = DashboardPeriod.THIS_MONTH,
    category: str | None = None,
):
    service = get_dashboard_service(db)

    return service.get_category_distribution(user=user, period=period)


@router.get(
    "/top-merchants",
    response_model=TopMerchantResponse,
)
def get_top_merchants(
    user=Depends(get_current_user),
    category: str | None = None,
    db=Depends(get_db),
    period: DashboardPeriod = DashboardPeriod.THIS_MONTH,
):
    service = get_dashboard_service(db)

    return service.top_merchants(user=user, period=period, category=category)


@router.get(
    "/spending-trend",
    response_model=SpendingTrendResponse,
)
def get_spending_trend(
    period: DashboardPeriod = DashboardPeriod.THIS_MONTH,
    category: str | None = None,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    service = get_dashboard_service(db)

    return service.get_spending_trend(user=user, period=period, category=category)


@router.get(
    "/insights",
    response_model=DashboardInsightsResponse,
)
def get_dashboard_insights(
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    insight_service = get_insight_service(db=db)

    return insight_service.generate_insights(user=user)


@router.get(
    "/ai-insights",
    response_model=AIInsights,
)
def get_dashboard_ai_insights(
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    insight_service = get_insight_service(db=db)

    return insight_service.generate_ai_insights(user=user)

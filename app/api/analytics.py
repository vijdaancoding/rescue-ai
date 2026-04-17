"""Analytics endpoints — aggregated views over calls, metadata, dispatches."""
from fastapi import APIRouter, Depends

from app.api.deps import (
    get_ai_metadata_repo,
    get_analytics_repo,
    get_current_user,
)
from app.db.models import User
from app.repositories.ai_metadata import AiMetadataRepository
from app.repositories.analytics import AnalyticsRepository
from app.schemas.analytics import (
    AnalyticsSummary,
    DayBucket,
    DispatchTypeCount,
)
from app.services import analytics as analytics_service

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/summary", response_model=AnalyticsSummary)
def get_summary(
    analytics: AnalyticsRepository = Depends(get_analytics_repo),
    current_user: User = Depends(get_current_user),
) -> AnalyticsSummary:
    return analytics_service.summary(analytics=analytics)


@router.get("/by-day", response_model=list[DayBucket])
def get_by_day(
    days: int = 30,
    analytics: AnalyticsRepository = Depends(get_analytics_repo),
    ai_metadata: AiMetadataRepository = Depends(get_ai_metadata_repo),
    current_user: User = Depends(get_current_user),
) -> list[DayBucket]:
    return analytics_service.by_day(
        days=days, analytics=analytics, ai_metadata=ai_metadata
    )


@router.get("/dispatches", response_model=list[DispatchTypeCount])
def get_dispatch_breakdown(
    analytics: AnalyticsRepository = Depends(get_analytics_repo),
    current_user: User = Depends(get_current_user),
) -> list[DispatchTypeCount]:
    return analytics_service.dispatch_breakdown(analytics=analytics)

"""
Analytics endpoints — aggregated data from call_sessions + ai_metadata + dispatches.

All endpoints require dispatcher authentication.
"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, case
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.db.models import CallSession, AiMetadata, Dispatch, User

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/summary")
def get_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    All-time aggregate counts and urgency breakdown.
    Spam vs real derived from latest ai_metadata per call.
    """
    total_calls = db.query(CallSession).count()

    status_counts: dict[str, int] = {}
    for status_val, cnt in db.query(CallSession.status, func.count(CallSession.id)).group_by(CallSession.status).all():
        status_counts[status_val or "unknown"] = cnt

    # Latest ai_metadata row per call via a subquery
    latest_meta_sq = (
        db.query(
            AiMetadata.call_id,
            AiMetadata.sentiment_label,
            AiMetadata.urgency_level,
            AiMetadata.processing_latency,
        )
        .distinct(AiMetadata.call_id)
        .order_by(AiMetadata.call_id, AiMetadata.created_at.desc())
        .subquery()
    )

    spam_count = (
        db.query(func.count())
        .select_from(latest_meta_sq)
        .filter(latest_meta_sq.c.sentiment_label == "spam")
        .scalar() or 0
    )
    real_count = (
        db.query(func.count())
        .select_from(latest_meta_sq)
        .filter(latest_meta_sq.c.sentiment_label == "not_spam")
        .scalar() or 0
    )

    avg_latency_ms = (
        db.query(func.avg(latest_meta_sq.c.processing_latency)).scalar() or 0
    )

    urgency_rows = (
        db.query(latest_meta_sq.c.urgency_level, func.count())
        .group_by(latest_meta_sq.c.urgency_level)
        .all()
    )
    urgency_breakdown = {row[0] or "unknown": row[1] for row in urgency_rows}

    return {
        "total_calls": total_calls,
        "real_calls": real_count,
        "spam_calls": spam_count,
        "dispatched": status_counts.get("Dispatched", 0),
        "false_alarms": status_counts.get("FalseAlarm", 0),
        "active": status_counts.get("Active", 0),
        "avg_processing_latency_ms": round(avg_latency_ms * 1000),
        "urgency_breakdown": urgency_breakdown,
    }


@router.get("/by-day")
def get_by_day(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Call volume grouped by date for the last N days (default 30).
    Returns total, spam, and real counts per day.
    """
    since = datetime.now(timezone.utc) - timedelta(days=days)

    # All calls in window
    calls = (
        db.query(CallSession)
        .filter(CallSession.start_time >= since)
        .all()
    )

    # Latest sentiment per call
    call_ids = [c.id for c in calls]
    sentiment_map: dict = {}
    if call_ids:
        latest_per_call = (
            db.query(AiMetadata.call_id, AiMetadata.sentiment_label)
            .distinct(AiMetadata.call_id)
            .filter(AiMetadata.call_id.in_(call_ids))
            .order_by(AiMetadata.call_id, AiMetadata.created_at.desc())
            .all()
        )
        sentiment_map = {str(r.call_id): r.sentiment_label for r in latest_per_call}

    # Group by date
    by_day: dict[str, dict] = {}
    for call in calls:
        if call.start_time is None:
            continue
        date_key = call.start_time.strftime("%Y-%m-%d")
        if date_key not in by_day:
            by_day[date_key] = {"date": date_key, "total": 0, "spam": 0, "real": 0}
        by_day[date_key]["total"] += 1
        sentiment = sentiment_map.get(str(call.id))
        if sentiment == "spam":
            by_day[date_key]["spam"] += 1
        elif sentiment == "not_spam":
            by_day[date_key]["real"] += 1

    return sorted(by_day.values(), key=lambda x: x["date"])


@router.get("/dispatches")
def get_dispatch_breakdown(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Dispatch count grouped by service type."""
    rows = (
        db.query(Dispatch.dispatch_type, func.count(Dispatch.id).label("count"))
        .group_by(Dispatch.dispatch_type)
        .all()
    )
    return [{"dispatch_type": r.dispatch_type, "count": r.count} for r in rows]

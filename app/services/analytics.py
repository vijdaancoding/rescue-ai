from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.repositories.ai_metadata import AiMetadataRepository
from app.repositories.analytics import AnalyticsRepository
from app.schemas.analytics import AnalyticsSummary, DayBucket, DispatchTypeCount


def summary(*, analytics: AnalyticsRepository) -> AnalyticsSummary:
    status_counts = analytics.status_counts()
    spam = analytics.spam_summary()
    return AnalyticsSummary(
        total_calls=analytics.total_calls(),
        real_calls=spam["real"],
        spam_calls=spam["spam"],
        dispatched=status_counts.get("Dispatched", 0),
        false_alarms=status_counts.get("FalseAlarm", 0),
        active=status_counts.get("Active", 0),
        avg_processing_latency_ms=round(spam["avg_latency_seconds"] * 1000),
        urgency_breakdown=spam["urgency_breakdown"],
    )


def by_day(
    *, days: int, analytics: AnalyticsRepository, ai_metadata: AiMetadataRepository
) -> list[DayBucket]:
    if days <= 0:
        return []
    since = datetime.now(timezone.utc) - timedelta(days=days)
    calls = analytics.calls_since(since)
    if not calls:
        return []

    meta_map = ai_metadata.latest_for_calls([c.id for c in calls])

    buckets: dict[str, DayBucket] = {}
    for call in calls:
        if call.start_time is None:
            continue
        key = call.start_time.strftime("%Y-%m-%d")
        bucket = buckets.get(key) or DayBucket(date=key, total=0, spam=0, real=0)
        bucket.total += 1
        meta = meta_map.get(str(call.id))
        label = meta.sentiment_label if meta else None
        if label == "spam":
            bucket.spam += 1
        elif label == "not_spam":
            bucket.real += 1
        buckets[key] = bucket

    return sorted(buckets.values(), key=lambda b: b.date)


def dispatch_breakdown(
    *, analytics: AnalyticsRepository
) -> list[DispatchTypeCount]:
    return [
        DispatchTypeCount(dispatch_type=dtype, count=count)
        for dtype, count in analytics.dispatch_type_counts()
    ]

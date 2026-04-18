from __future__ import annotations

from datetime import datetime
from typing import Protocol

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import AiMetadata, CallSession, Dispatch


class AnalyticsRepository(Protocol):
    def status_counts(self) -> dict[str, int]: ...
    def total_calls(self) -> int: ...
    def spam_summary(self) -> dict: ...
    def calls_since(self, since: datetime) -> list[CallSession]: ...
    def dispatch_type_counts(self) -> list[tuple[str, int]]: ...


class SqlAnalyticsRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def total_calls(self) -> int:
        return self._db.query(CallSession).count()

    def status_counts(self) -> dict[str, int]:
        rows = (
            self._db.query(CallSession.status, func.count(CallSession.id))
            .group_by(CallSession.status)
            .all()
        )
        return {(s or "unknown"): n for s, n in rows}

    def spam_summary(self) -> dict:
        latest_meta_sq = (
            self._db.query(
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
            self._db.query(func.count())
            .select_from(latest_meta_sq)
            .filter(latest_meta_sq.c.sentiment_label == "spam")
            .scalar()
            or 0
        )
        real_count = (
            self._db.query(func.count())
            .select_from(latest_meta_sq)
            .filter(latest_meta_sq.c.sentiment_label == "not_spam")
            .scalar()
            or 0
        )
        avg_latency_s = (
            self._db.query(func.avg(latest_meta_sq.c.processing_latency)).scalar() or 0
        )
        urgency_rows = (
            self._db.query(latest_meta_sq.c.urgency_level, func.count())
            .group_by(latest_meta_sq.c.urgency_level)
            .all()
        )
        urgency_breakdown = {row[0] or "unknown": row[1] for row in urgency_rows}

        return {
            "spam": spam_count,
            "real": real_count,
            "avg_latency_seconds": float(avg_latency_s),
            "urgency_breakdown": urgency_breakdown,
        }

    def calls_since(self, since: datetime) -> list[CallSession]:
        return (
            self._db.query(CallSession)
            .filter(CallSession.start_time >= since)
            .all()
        )

    def dispatch_type_counts(self) -> list[tuple[str, int]]:
        rows = (
            self._db.query(Dispatch.dispatch_type, func.count(Dispatch.id))
            .group_by(Dispatch.dispatch_type)
            .all()
        )
        return [(r[0], r[1]) for r in rows]

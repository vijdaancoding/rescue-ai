from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Protocol

from sqlalchemy.orm import Query, Session

from app.db.models import AiMetadata, CallSession


class CallRepository(Protocol):
    def get(self, call_id: uuid.UUID) -> Optional[CallSession]: ...
    def get_by_room(self, room_name: str) -> Optional[CallSession]: ...
    def get_by_caller_hash(self, caller_hash: str) -> Optional[CallSession]: ...
    def find_pending_by_phone(self, phone: str) -> Optional[CallSession]: ...
    def find_latest_for_phone(
        self, phone: str, *, max_age_seconds: int = 120
    ) -> Optional[CallSession]: ...
    def create(self, **fields) -> CallSession: ...
    def save(self, call: CallSession) -> None: ...
    def list_filtered(
        self,
        *,
        status: Optional[str],
        spam_label: Optional[str],
        date_from: Optional[datetime],
        date_to: Optional[datetime],
        search: Optional[str],
        offset: int,
        limit: int,
    ) -> list[CallSession]: ...


class SqlCallRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, call_id: uuid.UUID) -> Optional[CallSession]:
        return self._db.query(CallSession).filter(CallSession.id == call_id).first()

    def get_by_room(self, room_name: str) -> Optional[CallSession]:
        return (
            self._db.query(CallSession)
            .filter(CallSession.room_name == room_name)
            .first()
        )

    def get_by_caller_hash(self, caller_hash: str) -> Optional[CallSession]:
        return (
            self._db.query(CallSession)
            .filter(CallSession.caller_hash == caller_hash)
            .first()
        )

    def find_pending_by_phone(self, phone: str) -> Optional[CallSession]:
        return (
            self._db.query(CallSession)
            .filter(
                CallSession.caller_phone == phone,
                CallSession.status == "WaitingForCall",
            )
            .order_by(CallSession.start_time.desc())
            .first()
        )

    def find_latest_for_phone(
        self, phone: str, *, max_age_seconds: int = 120
    ) -> Optional[CallSession]:
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=max_age_seconds)
        return (
            self._db.query(CallSession)
            .filter(
                CallSession.caller_phone == phone,
                CallSession.start_time >= cutoff,
            )
            .order_by(CallSession.start_time.desc())
            .first()
        )

    def create(self, **fields) -> CallSession:
        call = CallSession(**fields)
        self._db.add(call)
        self._db.commit()
        self._db.refresh(call)
        return call

    def save(self, call: CallSession) -> None:
        self._db.add(call)
        self._db.commit()

    def list_filtered(
        self,
        *,
        status: Optional[str],
        spam_label: Optional[str],
        date_from: Optional[datetime],
        date_to: Optional[datetime],
        search: Optional[str],
        offset: int,
        limit: int,
    ) -> list[CallSession]:
        # Join latest-per-call ai_metadata at the DB level when filtering by
        # spam — otherwise we'd scan every row and discard most in Python.
        if spam_label:
            latest_meta_sq = (
                self._db.query(AiMetadata.call_id)
                .distinct(AiMetadata.call_id)
                .filter(AiMetadata.sentiment_label == spam_label)
                .order_by(AiMetadata.call_id, AiMetadata.created_at.desc())
                .subquery()
            )
            query: Query = (
                self._db.query(CallSession)
                .join(latest_meta_sq, CallSession.id == latest_meta_sq.c.call_id)
            )
        else:
            query = self._db.query(CallSession)

        if status:
            query = query.filter(CallSession.status == status)
        if date_from:
            query = query.filter(CallSession.start_time >= date_from)
        if date_to:
            query = query.filter(CallSession.start_time <= date_to)
        if search:
            term = f"%{search}%"
            query = query.filter(
                (CallSession.caller_phone.ilike(term))
                | (CallSession.caller_city.ilike(term))
            )

        return (
            query.order_by(CallSession.start_time.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

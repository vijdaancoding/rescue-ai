from __future__ import annotations

import uuid
from collections import defaultdict
from typing import Optional, Protocol

from sqlalchemy.orm import Session

from app.db.models import Dispatch


class DispatchRepository(Protocol):
    def get(self, dispatch_id: uuid.UUID) -> Optional[Dispatch]: ...
    def list_for_call(self, call_id: uuid.UUID) -> list[Dispatch]: ...
    def existing_types(self, call_id: uuid.UUID) -> set[str]: ...
    def create_many(self, rows: list[Dispatch]) -> None: ...
    def save(self, row: Dispatch) -> None: ...
    def types_by_call(
        self, call_ids: list[uuid.UUID]
    ) -> dict[str, list[str]]: ...


class SqlDispatchRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, dispatch_id: uuid.UUID) -> Optional[Dispatch]:
        return (
            self._db.query(Dispatch)
            .filter(Dispatch.id == dispatch_id)
            .first()
        )

    def list_for_call(self, call_id: uuid.UUID) -> list[Dispatch]:
        return (
            self._db.query(Dispatch)
            .filter(Dispatch.call_id == call_id)
            .order_by(Dispatch.created_at.asc())
            .all()
        )

    def existing_types(self, call_id: uuid.UUID) -> set[str]:
        rows = (
            self._db.query(Dispatch.dispatch_type)
            .filter(Dispatch.call_id == call_id)
            .all()
        )
        return {r.dispatch_type for r in rows}

    def create_many(self, rows: list[Dispatch]) -> None:
        if not rows:
            return
        self._db.add_all(rows)
        self._db.flush()

    def save(self, row: Dispatch) -> None:
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)

    def types_by_call(
        self, call_ids: list[uuid.UUID]
    ) -> dict[str, list[str]]:
        if not call_ids:
            return {}
        rows = (
            self._db.query(Dispatch.call_id, Dispatch.dispatch_type)
            .filter(Dispatch.call_id.in_(call_ids))
            .all()
        )
        grouped: dict[str, list[str]] = defaultdict(list)
        for row in rows:
            grouped[str(row.call_id)].append(row.dispatch_type)
        return grouped

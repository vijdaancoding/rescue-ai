from __future__ import annotations

import uuid
from typing import Iterable, Optional, Protocol

from sqlalchemy.orm import Session

from app.db.models import Geolocation


class GeolocationRepository(Protocol):
    def latest_for_call(self, call_id: uuid.UUID) -> Optional[Geolocation]: ...
    def latest_for_calls(
        self, call_ids: Iterable[uuid.UUID]
    ) -> dict[str, Geolocation]: ...
    def create(self, **fields) -> Geolocation: ...


class SqlGeolocationRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def latest_for_call(self, call_id: uuid.UUID) -> Optional[Geolocation]:
        return (
            self._db.query(Geolocation)
            .filter(Geolocation.call_id == call_id)
            .order_by(Geolocation.created_at.desc())
            .first()
        )

    def latest_for_calls(
        self, call_ids: Iterable[uuid.UUID]
    ) -> dict[str, Geolocation]:
        ids = list(call_ids)
        if not ids:
            return {}
        # Grab every geolocation row for these calls, then collapse to the
        # newest per call_id in Python — simpler than a windowed subquery and
        # the list is always bounded by the calls page size.
        rows = (
            self._db.query(Geolocation)
            .filter(Geolocation.call_id.in_(ids))
            .order_by(Geolocation.created_at.desc())
            .all()
        )
        result: dict[str, Geolocation] = {}
        for row in rows:
            key = str(row.call_id)
            if key not in result:
                result[key] = row
        return result

    def create(self, **fields) -> Geolocation:
        row = Geolocation(**fields)
        self._db.add(row)
        self._db.commit()
        return row

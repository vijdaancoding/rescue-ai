from __future__ import annotations

import uuid
from typing import Optional, Protocol

from sqlalchemy.orm import Session

from app.db.models import Geolocation


class GeolocationRepository(Protocol):
    def latest_for_call(self, call_id: uuid.UUID) -> Optional[Geolocation]: ...
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

    def create(self, **fields) -> Geolocation:
        row = Geolocation(**fields)
        self._db.add(row)
        self._db.commit()
        return row

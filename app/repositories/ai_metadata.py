from __future__ import annotations

import uuid
from typing import Protocol

from sqlalchemy.orm import Session

from app.db.models import AiMetadata


class AiMetadataRepository(Protocol):
    def create(self, **fields) -> AiMetadata: ...
    def count_for_call(self, call_id: uuid.UUID) -> int: ...
    def latest_for_calls(
        self, call_ids: list[uuid.UUID]
    ) -> dict[str, AiMetadata]: ...


class SqlAiMetadataRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, **fields) -> AiMetadata:
        row = AiMetadata(**fields)
        self._db.add(row)
        self._db.flush()
        return row

    def count_for_call(self, call_id: uuid.UUID) -> int:
        return (
            self._db.query(AiMetadata)
            .filter(AiMetadata.call_id == call_id)
            .count()
        )

    def latest_for_calls(
        self, call_ids: list[uuid.UUID]
    ) -> dict[str, AiMetadata]:
        if not call_ids:
            return {}
        rows = (
            self._db.query(AiMetadata)
            .distinct(AiMetadata.call_id)
            .filter(AiMetadata.call_id.in_(call_ids))
            .order_by(AiMetadata.call_id, AiMetadata.created_at.desc())
            .all()
        )
        return {str(r.call_id): r for r in rows}

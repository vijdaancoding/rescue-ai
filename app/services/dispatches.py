from __future__ import annotations

import uuid
from typing import Optional

from app.db.models import Dispatch
from app.repositories.calls import CallRepository
from app.repositories.dispatches import DispatchRepository
from app.schemas.dispatches import (
    DispatchCreate,
    DispatchOut,
    VALID_DISPATCH_STATUSES,
    VALID_DISPATCH_TYPES,
)
from app.services.errors import NotFoundError, ValidationError


def _to_out(row: Dispatch) -> DispatchOut:
    return DispatchOut(
        id=str(row.id),
        created_at=row.created_at.isoformat(),
        call_id=str(row.call_id),
        dispatch_type=row.dispatch_type,
        status=row.status,
        notes=row.notes,
        ai_recommended=row.ai_recommended,
    )


def create_dispatches(
    body: DispatchCreate,
    *,
    calls: CallRepository,
    dispatches: DispatchRepository,
) -> list[DispatchOut]:
    invalid = set(body.dispatch_types) - VALID_DISPATCH_TYPES
    if invalid:
        raise ValidationError(f"Invalid dispatch types: {sorted(invalid)}")

    call_uuid = uuid.UUID(body.call_id)
    call = calls.get(call_uuid)
    if not call:
        raise NotFoundError("Call not found")

    existing = dispatches.existing_types(call_uuid)
    new_rows = [
        Dispatch(
            call_id=call_uuid,
            dispatch_type=dtype,
            status="dispatched",
            notes=body.notes,
            ai_recommended=(dtype in body.ai_recommended),
        )
        for dtype in body.dispatch_types
        if dtype not in existing
    ]

    dispatches.create_many(new_rows)
    call.status = "Dispatched"
    calls.save(call)

    return [_to_out(row) for row in new_rows]


def list_for_call(
    call_id: str, *, dispatches: DispatchRepository
) -> list[DispatchOut]:
    rows = dispatches.list_for_call(uuid.UUID(call_id))
    return [_to_out(r) for r in rows]


def update_status(
    dispatch_id: str, new_status: str, *, dispatches: DispatchRepository
) -> DispatchOut:
    if new_status not in VALID_DISPATCH_STATUSES:
        raise ValidationError(
            f"Invalid status. Allowed: {sorted(VALID_DISPATCH_STATUSES)}"
        )
    row = dispatches.get(uuid.UUID(dispatch_id))
    if not row:
        raise NotFoundError("Dispatch not found")
    row.status = new_status
    dispatches.save(row)
    return _to_out(row)

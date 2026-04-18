from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends

from app.api.deps import (
    get_ai_metadata_repo,
    get_call_repo,
    get_current_user,
    get_dispatch_repo,
    get_geolocation_repo,
)
from app.db.models import User
from app.repositories.ai_metadata import AiMetadataRepository
from app.repositories.calls import CallRepository
from app.repositories.dispatches import DispatchRepository
from app.repositories.geolocation import GeolocationRepository
from app.schemas.calls import CallContext, CallFilters, CallSummary, StatusUpdate
from app.services import calls as calls_service

router = APIRouter(prefix="/calls", tags=["Calls"])


@router.get("/", response_model=list[CallSummary])
def get_calls(
    status: Optional[str] = None,
    spam_label: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
    calls: CallRepository = Depends(get_call_repo),
    ai_metadata: AiMetadataRepository = Depends(get_ai_metadata_repo),
    dispatches: DispatchRepository = Depends(get_dispatch_repo),
    current_user: User = Depends(get_current_user),
) -> list[CallSummary]:
    filters = CallFilters(
        status=status,
        spam_label=spam_label,
        date_from=date_from,
        date_to=date_to,
        search=search,
        page=page,
        limit=limit,
    )
    return calls_service.list_calls(
        filters, calls=calls, ai_metadata=ai_metadata, dispatches=dispatches
    )


@router.patch("/{call_id}/status")
def update_call_status(
    call_id: str,
    body: StatusUpdate,
    calls: CallRepository = Depends(get_call_repo),
    current_user: User = Depends(get_current_user),
) -> dict:
    result = calls_service.update_status(call_id, body.status, calls=calls)
    import uuid as _uuid
    call = calls.get(_uuid.UUID(call_id))
    if call:
        result["end_time"] = call.end_time.isoformat() if call.end_time else None
    return result


@router.patch("/{call_id}")
def update_call_status_short(
    call_id: str,
    body: StatusUpdate,
    calls: CallRepository = Depends(get_call_repo),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Alias for /{call_id}/status."""
    result = calls_service.update_status(call_id, body.status, calls=calls)
    import uuid as _uuid
    call = calls.get(_uuid.UUID(call_id))
    if call:
        result["end_time"] = call.end_time.isoformat() if call.end_time else None
    return result


@router.get("/context/{room_name}", response_model=CallContext)
def get_call_context(
    room_name: str,
    calls: CallRepository = Depends(get_call_repo),
    geolocation: GeolocationRepository = Depends(get_geolocation_repo),
) -> CallContext:
    """Internal agent-facing endpoint; no auth required."""
    return calls_service.get_context(room_name, calls=calls, geolocation=geolocation)


@router.get("/{call_id}/context")
def get_call_context_by_id(
    call_id: str,
    calls: CallRepository = Depends(get_call_repo),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Return full call details by call_id."""
    import uuid as _uuid
    try:
        call = calls.get(_uuid.UUID(call_id))
    except ValueError:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="Invalid call_id")
    if not call:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Call not found")
    return {
        "id": str(call.id),
        "status": call.status,
        "caller_phone": call.caller_phone,
        "caller_city": call.caller_city,
        "caller_state": call.caller_state,
        "caller_country": call.caller_country,
        "start_time": call.start_time.isoformat() if call.start_time else None,
        "end_time": call.end_time.isoformat() if call.end_time else None,
    }

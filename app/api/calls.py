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
from app.schemas.calls import (
    BindRoomRequest,
    CallContext,
    CallFilters,
    CallSummary,
    ListenerToken,
    StatusUpdate,
)
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
    geolocation: GeolocationRepository = Depends(get_geolocation_repo),
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
        filters,
        calls=calls,
        ai_metadata=ai_metadata,
        dispatches=dispatches,
        geolocation=geolocation,
    )


@router.get("/{call_id}", response_model=CallSummary)
def get_call(
    call_id: str,
    calls: CallRepository = Depends(get_call_repo),
    ai_metadata: AiMetadataRepository = Depends(get_ai_metadata_repo),
    dispatches: DispatchRepository = Depends(get_dispatch_repo),
    geolocation: GeolocationRepository = Depends(get_geolocation_repo),
    current_user: User = Depends(get_current_user),
) -> CallSummary:
    """Single-call summary — same shape as the list endpoint, for observers
    that want to watch a specific call (e.g. the Listen page)."""
    return calls_service.get_one(
        call_id,
        calls=calls,
        ai_metadata=ai_metadata,
        dispatches=dispatches,
        geolocation=geolocation,
    )


@router.patch("/{call_id}/status")
def update_call_status(
    call_id: str,
    body: StatusUpdate,
    calls: CallRepository = Depends(get_call_repo),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    return calls_service.update_status(call_id, body.status, calls=calls)


@router.get("/context/{room_name}", response_model=CallContext)
def get_call_context(
    room_name: str,
    calls: CallRepository = Depends(get_call_repo),
    geolocation: GeolocationRepository = Depends(get_geolocation_repo),
) -> CallContext:
    """Internal agent-facing endpoint; no auth required."""
    return calls_service.get_context(room_name, calls=calls, geolocation=geolocation)


@router.get("/{call_id}/listener-token", response_model=ListenerToken)
def get_listener_token(
    call_id: str,
    calls: CallRepository = Depends(get_call_repo),
    current_user: User = Depends(get_current_user),
) -> ListenerToken:
    """Authed endpoint: dispatcher gets a subscribe-only LiveKit token to watch
    live transcription of a call in progress."""
    return calls_service.mint_listener_token(call_id, calls=calls)


@router.post("/bind-room", response_model=CallContext)
def bind_room_for_phone(
    body: BindRoomRequest,
    calls: CallRepository = Depends(get_call_repo),
    geolocation: GeolocationRepository = Depends(get_geolocation_repo),
) -> CallContext:
    """Internal agent-facing endpoint; no auth required.
    For SIP-originated rooms where Twilio created the call_sessions row but
    doesn't know the LiveKit room name — agent calls this on connect to bind
    the room name and fetch context in one shot."""
    return calls_service.bind_room_for_phone(
        body.phone, body.room_name, calls=calls, geolocation=geolocation
    )

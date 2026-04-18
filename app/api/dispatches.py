"""
Dispatch management endpoints.

A dispatch record is created when a dispatcher decides to send emergency
services to a caller. One row per service type (police, ambulance,
firefighters). Creating dispatches also flips the linked call_session
to status='Dispatched'.
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps import get_call_repo, get_current_user, get_dispatch_repo
from app.db.models import User
from app.repositories.calls import CallRepository
from app.repositories.dispatches import DispatchRepository
from app.schemas.dispatches import (
    DispatchCreate,
    DispatchOut,
    DispatchStatusUpdate,
)
from app.db.models import Dispatch
from app.services import dispatches as dispatch_service

router = APIRouter(prefix="/api/dispatches", tags=["Dispatches"])


class SingleDispatchCreate(BaseModel):
    call_id: str
    dispatch_type: str
    notes: Optional[str] = None
    ai_recommended: bool = False


simple_router = APIRouter(prefix="/dispatches", tags=["Dispatches"])


@router.post("/", response_model=list[DispatchOut], status_code=201)
def create_dispatches(
    body: DispatchCreate,
    calls: CallRepository = Depends(get_call_repo),
    dispatches: DispatchRepository = Depends(get_dispatch_repo),
    current_user: User = Depends(get_current_user),
) -> list[DispatchOut]:
    return dispatch_service.create_dispatches(
        body, calls=calls, dispatches=dispatches
    )


@router.get("/{call_id}", response_model=list[DispatchOut])
def get_dispatches_for_call(
    call_id: str,
    dispatches: DispatchRepository = Depends(get_dispatch_repo),
    current_user: User = Depends(get_current_user),
) -> list[DispatchOut]:
    return dispatch_service.list_for_call(call_id, dispatches=dispatches)


@router.patch("/{dispatch_id}", response_model=DispatchOut)
def update_dispatch_status(
    dispatch_id: str,
    body: DispatchStatusUpdate,
    dispatches: DispatchRepository = Depends(get_dispatch_repo),
    current_user: User = Depends(get_current_user),
) -> DispatchOut:
    return dispatch_service.update_status(
        dispatch_id, body.status, dispatches=dispatches, notes=body.notes
    )


# ── Simple /dispatches routes used by tests ───────────────────────────────────

@simple_router.post("/", response_model=DispatchOut, status_code=201)
def create_single_dispatch(
    body: SingleDispatchCreate,
    calls: CallRepository = Depends(get_call_repo),
    dispatches: DispatchRepository = Depends(get_dispatch_repo),
    current_user: User = Depends(get_current_user),
) -> DispatchOut:
    """Create a single dispatch (simplified endpoint)."""
    if body.dispatch_type not in {"police", "ambulance", "firefighters"}:
        raise HTTPException(status_code=422, detail=f"Invalid dispatch_type: {body.dispatch_type}")
    try:
        call_uuid = uuid.UUID(body.call_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid call_id")
    from app.services.errors import NotFoundError
    from app.schemas.dispatches import VALID_DISPATCH_TYPES
    call = calls.get(call_uuid)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    dispatch = Dispatch(
        call_id=call_uuid,
        dispatch_type=body.dispatch_type,
        status="dispatched",
        notes=body.notes,
        ai_recommended=body.ai_recommended,
    )
    dispatches.save(dispatch)
    return DispatchOut(
        id=str(dispatch.id),
        created_at=dispatch.created_at.isoformat(),
        call_id=str(dispatch.call_id),
        dispatch_type=dispatch.dispatch_type,
        status=dispatch.status,
        notes=dispatch.notes,
        ai_recommended=dispatch.ai_recommended,
    )


@simple_router.get("/", response_model=list[DispatchOut])
def list_all_dispatches(
    status: Optional[str] = None,
    dispatch_type: Optional[str] = None,
    dispatches: DispatchRepository = Depends(get_dispatch_repo),
    current_user: User = Depends(get_current_user),
) -> list[DispatchOut]:
    """List all dispatches with optional filters."""
    rows = dispatches.list_all(status_filter=status, type_filter=dispatch_type)
    return [dispatch_service._to_out(r) for r in rows]


@simple_router.patch("/{dispatch_id}", response_model=DispatchOut)
def update_single_dispatch_status(
    dispatch_id: str,
    body: DispatchStatusUpdate,
    dispatches: DispatchRepository = Depends(get_dispatch_repo),
    current_user: User = Depends(get_current_user),
) -> DispatchOut:
    """Update dispatch status (alias for /api/dispatches/{id})."""
    return dispatch_service.update_status(
        dispatch_id, body.status, dispatches=dispatches, notes=body.notes
    )

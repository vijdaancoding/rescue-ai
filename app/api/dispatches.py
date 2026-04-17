"""
Dispatch management endpoints.

A dispatch record is created when a dispatcher decides to send emergency
services to a caller. One row per service type (police, ambulance,
firefighters). Creating dispatches also flips the linked call_session
to status='Dispatched'.
"""
from fastapi import APIRouter, Depends

from app.api.deps import get_call_repo, get_current_user, get_dispatch_repo
from app.db.models import User
from app.repositories.calls import CallRepository
from app.repositories.dispatches import DispatchRepository
from app.schemas.dispatches import (
    DispatchCreate,
    DispatchOut,
    DispatchStatusUpdate,
)
from app.services import dispatches as dispatch_service

router = APIRouter(prefix="/api/dispatches", tags=["Dispatches"])


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
        dispatch_id, body.status, dispatches=dispatches
    )

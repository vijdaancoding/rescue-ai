"""
Dispatch management endpoints.

A dispatch record is created when a dispatcher decides to send emergency services
to a caller. One row per service type (police, ambulance, firefighters).
Creating dispatches also updates the linked call_session status to 'Dispatched'.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.db.models import Dispatch, CallSession, User

router = APIRouter(prefix="/api/dispatches", tags=["Dispatches"])


# ── Schemas ────────────────────────────────────────────────────────────────────

class DispatchCreate(BaseModel):
    call_id: str
    dispatch_types: list[str]          # ["ambulance", "firefighters"]
    ai_recommended: list[str] = []     # subset of dispatch_types recommended by AI
    notes: Optional[str] = None


class DispatchStatusUpdate(BaseModel):
    status: str  # dispatched | en_route | on_scene | resolved


class DispatchOut(BaseModel):
    id: str
    created_at: str
    call_id: str
    dispatch_type: str
    status: str
    notes: Optional[str]
    ai_recommended: bool

    class Config:
        from_attributes = True


# ── Endpoints ──────────────────────────────────────────────────────────────────

VALID_TYPES = {"police", "ambulance", "firefighters"}
VALID_STATUSES = {"dispatched", "en_route", "on_scene", "resolved"}


@router.post("/", response_model=list[DispatchOut], status_code=201)
def create_dispatches(
    body: DispatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create one dispatch row per service type and mark the call as Dispatched.
    Idempotent per type — skips types already dispatched for this call.
    """
    invalid = set(body.dispatch_types) - VALID_TYPES
    if invalid:
        raise HTTPException(status_code=400, detail=f"Invalid dispatch types: {invalid}")

    call_uuid = uuid.UUID(body.call_id)
    call = db.query(CallSession).filter(CallSession.id == call_uuid).first()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    # Find already-dispatched types for this call (avoid duplicates)
    existing_types = {
        d.dispatch_type
        for d in db.query(Dispatch).filter(Dispatch.call_id == call_uuid).all()
    }

    created: list[Dispatch] = []
    for dtype in body.dispatch_types:
        if dtype in existing_types:
            continue
        row = Dispatch(
            call_id=call_uuid,
            dispatch_type=dtype,
            status="dispatched",
            notes=body.notes,
            ai_recommended=(dtype in body.ai_recommended),
        )
        db.add(row)
        created.append(row)

    # Update call status to Dispatched
    call.status = "Dispatched"
    db.commit()
    for row in created:
        db.refresh(row)

    return [
        DispatchOut(
            id=str(row.id),
            created_at=row.created_at.isoformat(),
            call_id=str(row.call_id),
            dispatch_type=row.dispatch_type,
            status=row.status,
            notes=row.notes,
            ai_recommended=row.ai_recommended,
        )
        for row in created
    ]


@router.get("/{call_id}", response_model=list[DispatchOut])
def get_dispatches_for_call(
    call_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return all dispatch records for a given call."""
    call_uuid = uuid.UUID(call_id)
    rows = (
        db.query(Dispatch)
        .filter(Dispatch.call_id == call_uuid)
        .order_by(Dispatch.created_at.asc())
        .all()
    )
    return [
        DispatchOut(
            id=str(r.id),
            created_at=r.created_at.isoformat(),
            call_id=str(r.call_id),
            dispatch_type=r.dispatch_type,
            status=r.status,
            notes=r.notes,
            ai_recommended=r.ai_recommended,
        )
        for r in rows
    ]


@router.patch("/{dispatch_id}", response_model=DispatchOut)
def update_dispatch_status(
    dispatch_id: str,
    body: DispatchStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update the status of a single dispatch (e.g. en_route → on_scene)."""
    if body.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Allowed: {VALID_STATUSES}")

    row = db.query(Dispatch).filter(Dispatch.id == uuid.UUID(dispatch_id)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Dispatch not found")

    row.status = body.status
    db.commit()
    db.refresh(row)
    return DispatchOut(
        id=str(row.id),
        created_at=row.created_at.isoformat(),
        call_id=str(row.call_id),
        dispatch_type=row.dispatch_type,
        status=row.status,
        notes=row.notes,
        ai_recommended=row.ai_recommended,
    )

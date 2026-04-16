from collections import defaultdict
from datetime import datetime, timezone
from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.db.models import CallSession, AiMetadata, Dispatch, User

router = APIRouter(prefix="/calls", tags=["Calls"])


# ── Response schema ────────────────────────────────────────────────────────────

class CallSummary(BaseModel):
    id: str
    start_time: Optional[str]
    end_time: Optional[str]
    duration_seconds: Optional[int]
    status: Optional[str]
    caller_phone: Optional[str]
    caller_city: Optional[str]
    caller_country: Optional[str]
    spam_label: Optional[str]
    urgency_level: Optional[str]
    scam_probability: Optional[int]
    dispatch_types: list[str]

    class Config:
        from_attributes = True


class StatusUpdate(BaseModel):
    status: str


# ── Helpers ────────────────────────────────────────────────────────────────────

def _enrich_calls(calls: list[CallSession], db: Session) -> list[CallSummary]:
    """
    Batch-load ai_metadata and dispatches for a list of calls — 3 queries total
    regardless of how many calls are returned (avoids N+1).
    """
    if not calls:
        return []

    call_ids = [c.id for c in calls]

    # Latest AiMetadata per call — one query using DISTINCT ON
    meta_rows = (
        db.query(AiMetadata)
        .distinct(AiMetadata.call_id)
        .filter(AiMetadata.call_id.in_(call_ids))
        .order_by(AiMetadata.call_id, AiMetadata.created_at.desc())
        .all()
    )
    meta_map: dict = {str(m.call_id): m for m in meta_rows}

    # All dispatches in one query
    dispatch_rows = (
        db.query(Dispatch.call_id, Dispatch.dispatch_type)
        .filter(Dispatch.call_id.in_(call_ids))
        .all()
    )
    dispatch_map: dict[str, list[str]] = defaultdict(list)
    for row in dispatch_rows:
        dispatch_map[str(row.call_id)].append(row.dispatch_type)

    results = []
    for call in calls:
        meta = meta_map.get(str(call.id))
        dispatch_types = dispatch_map.get(str(call.id), [])

        duration_seconds = None
        if call.start_time and call.end_time:
            start = call.start_time.replace(tzinfo=timezone.utc) if call.start_time.tzinfo is None else call.start_time
            end = call.end_time.replace(tzinfo=timezone.utc) if call.end_time.tzinfo is None else call.end_time
            duration_seconds = int((end - start).total_seconds())

        results.append(CallSummary(
            id=str(call.id),
            start_time=call.start_time.isoformat() if call.start_time else None,
            end_time=call.end_time.isoformat() if call.end_time else None,
            duration_seconds=duration_seconds,
            status=call.status,
            caller_phone=call.caller_phone,
            caller_city=call.caller_city,
            caller_country=call.caller_country,
            spam_label=meta.sentiment_label if meta else None,
            urgency_level=meta.urgency_level if meta else None,
            scam_probability=meta.scam_probability if meta else None,
            dispatch_types=dispatch_types,
        ))

    return results


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("/", response_model=list[CallSummary])
def get_calls(
    status: Optional[str] = None,
    spam_label: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return calls with optional filters. Enriched with latest AI metadata and dispatch types.

    Filters:
    - status: Incoming | Active | Dispatched | FalseAlarm
    - spam_label: spam | not_spam (from latest ai_metadata)
    - date_from / date_to: ISO date strings (YYYY-MM-DD)
    - search: matches caller_phone or caller_city (case-insensitive)
    - page / limit: pagination
    """
    # When filtering by spam_label we must join through ai_metadata at the DB level
    # to avoid fetching all rows and discarding most of them in Python.
    if spam_label:
        latest_meta_sq = (
            db.query(AiMetadata.call_id)
            .distinct(AiMetadata.call_id)
            .filter(AiMetadata.sentiment_label == spam_label)
            .order_by(AiMetadata.call_id, AiMetadata.created_at.desc())
            .subquery()
        )
        query = db.query(CallSession).join(latest_meta_sq, CallSession.id == latest_meta_sq.c.call_id)
    else:
        query = db.query(CallSession)

    if status:
        query = query.filter(CallSession.status == status)

    if date_from:
        query = query.filter(CallSession.start_time >= datetime.fromisoformat(date_from))

    if date_to:
        query = query.filter(CallSession.start_time <= datetime.fromisoformat(date_to + "T23:59:59"))

    if search:
        term = f"%{search}%"
        query = query.filter(
            (CallSession.caller_phone.ilike(term)) |
            (CallSession.caller_city.ilike(term))
        )

    query = query.order_by(CallSession.start_time.desc())
    offset = (page - 1) * limit
    calls = query.offset(offset).limit(limit).all()

    return _enrich_calls(calls, db)


@router.patch("/{call_id}/status")
def update_call_status(
    call_id: str,
    body: StatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update the status of a call (e.g. mark as FalseAlarm or Active)."""
    allowed = {"Incoming", "Active", "Dispatched", "FalseAlarm", "Archived"}
    if body.status not in allowed:
        raise HTTPException(status_code=400, detail=f"Invalid status. Allowed: {allowed}")

    call = db.query(CallSession).filter(CallSession.id == uuid.UUID(call_id)).first()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    call.status = body.status
    if body.status == "FalseAlarm" and call.end_time is None:
        call.end_time = datetime.now(timezone.utc)
    db.commit()
    return {"call_id": call_id, "status": call.status}


@router.post("/dummy-call")
def create_dummy_call(db: Session = Depends(get_db)):
    new_call = CallSession(caller_hash="anon_caller_xyz", status="Incoming")
    db.add(new_call)
    db.commit()
    db.refresh(new_call)
    return {"msg": "Dummy call created", "call_id": new_call.id}

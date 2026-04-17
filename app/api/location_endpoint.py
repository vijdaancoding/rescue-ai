"""
PWA endpoint: user submits exact GPS before dialing, so the helpline already
knows where they are when Twilio connects the call.
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models import CallSession, Geolocation
from app.utils.geocoding import reverse_geocode

router = APIRouter(prefix="/location", tags=["Location"])


class LocationPayload(BaseModel):
    phone_number: str
    lat: float
    lng: float


def _save_pending_session(
    db: Session,
    session_id: uuid.UUID,
    phone: str,
    lat: float,
    lng: float,
    geo_data: dict[str, str | None],
) -> None:
    db.add(
        CallSession(
            id=session_id,
            caller_hash=f"pwa-waiting-{phone}",
            caller_phone=phone,
            status="WaitingForCall",
            start_time=datetime.now(timezone.utc),
            caller_city=geo_data["city"],
            caller_state=geo_data["state"],
            caller_country=geo_data["country"],
            caller_zip=geo_data["zip"],
        )
    )
    db.add(
        Geolocation(
            call_id=session_id,
            latitude=lat,
            longitude=lng,
            is_simulated=False,
        )
    )
    db.commit()


@router.post("")
async def save_pwa_location(payload: LocationPayload, db: Session = Depends(get_db)):
    """Persist exact GPS + reverse-geocoded address keyed by phone number."""
    phone = payload.phone_number.strip()
    if not phone.startswith("+"):
        phone = f"+{phone}"

    geo_data = await reverse_geocode(payload.lat, payload.lng)

    session_id = uuid.uuid4()
    await asyncio.to_thread(
        _save_pending_session, db, session_id, phone, payload.lat, payload.lng, geo_data
    )

    return {"status": "ok", "message": "Location saved, ready for call"}

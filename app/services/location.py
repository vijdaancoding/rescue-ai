from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

from app.repositories.calls import CallRepository
from app.repositories.geolocation import GeolocationRepository
from app.utils.geocoding import reverse_geocode


async def save_pending_location(
    *,
    phone: str,
    lat: float,
    lng: float,
    calls: CallRepository,
    geolocation: GeolocationRepository,
) -> uuid.UUID:
    """
    Persist a pending CallSession keyed by phone + exact GPS.
    Twilio's webhook upgrades this row to an Active session when the call lands.
    """
    geo_data = await reverse_geocode(lat, lng)
    session_id = uuid.uuid4()
    await asyncio.to_thread(
        _persist,
        session_id=session_id,
        phone=phone,
        lat=lat,
        lng=lng,
        geo_data=geo_data,
        calls=calls,
        geolocation=geolocation,
    )
    return session_id


def _persist(
    *,
    session_id: uuid.UUID,
    phone: str,
    lat: float,
    lng: float,
    geo_data: dict,
    calls: CallRepository,
    geolocation: GeolocationRepository,
) -> None:
    calls.create(
        id=session_id,
        caller_hash=f"pwa-waiting-{phone}",
        caller_phone=phone,
        status="WaitingForCall",
        start_time=datetime.now(timezone.utc),
        caller_city=geo_data.get("city"),
        caller_state=geo_data.get("state"),
        caller_country=geo_data.get("country"),
        caller_zip=geo_data.get("zip"),
    )
    geolocation.create(
        call_id=session_id,
        latitude=lat,
        longitude=lng,
        is_simulated=False,
    )

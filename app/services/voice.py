"""
Voice-call side-effects.

The WebSocket router owns I/O with the browser + LiveKit. Everything that
touches the database lives here so the router stays focused on orchestration.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from app.repositories.calls import CallRepository
from app.repositories.geolocation import GeolocationRepository


def create_incoming_call(
    *, caller_hash: str, room_name: str, calls: CallRepository
):
    return calls.create(
        caller_hash=caller_hash, status="Incoming", room_name=room_name
    )


def save_geolocation(
    *,
    call_id: uuid.UUID,
    lat: float,
    lng: float,
    geo_data: dict[str, Optional[str]],
    calls: CallRepository,
    geolocation: GeolocationRepository,
) -> None:
    call = calls.get(call_id)
    if call is None:
        return
    call.caller_city = geo_data.get("city")
    call.caller_state = geo_data.get("state")
    call.caller_country = geo_data.get("country")
    call.caller_zip = geo_data.get("zip")
    calls.save(call)
    geolocation.create(
        call_id=call_id, latitude=lat, longitude=lng, is_simulated=True
    )


def mark_active(*, call_id: uuid.UUID, calls: CallRepository) -> None:
    call = calls.get(call_id)
    if call is None:
        return
    call.status = "Active"
    calls.save(call)


def close_call(*, call_id: uuid.UUID, calls: CallRepository) -> None:
    call = calls.get(call_id)
    if call is None:
        return
    call.end_time = datetime.now(timezone.utc)
    call.status = "FalseAlarm"
    calls.save(call)

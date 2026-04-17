"""
PWA endpoint: user submits exact GPS before dialing, so the helpline already
knows where they are when Twilio connects the call.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_call_repo, get_geolocation_repo
from app.repositories.calls import CallRepository
from app.repositories.geolocation import GeolocationRepository
from app.schemas.location import LocationPayload, LocationResponse
from app.services import location as location_service

router = APIRouter(prefix="/location", tags=["Location"])


@router.post("", response_model=LocationResponse)
async def save_pwa_location(
    payload: LocationPayload,
    calls: CallRepository = Depends(get_call_repo),
    geolocation: GeolocationRepository = Depends(get_geolocation_repo),
) -> LocationResponse:
    phone = payload.phone_number.strip()
    if not phone.startswith("+"):
        phone = f"+{phone}"

    await location_service.save_pending_location(
        phone=phone,
        lat=payload.lat,
        lng=payload.lng,
        calls=calls,
        geolocation=geolocation,
    )
    return LocationResponse(status="ok", message="Location saved, ready for call")

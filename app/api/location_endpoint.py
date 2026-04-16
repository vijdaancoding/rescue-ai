import uuid
import httpx
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Import from your existing codebase
from app.api.deps import get_db
from app.db.models import CallSession, Geolocation
from app.core.config import settings

router = APIRouter(prefix="/location", tags=["Location"])

class LocationPayload(BaseModel):
    phone_number: str  # User inputs this in the PWA
    lat: float
    lng: float

async def reverse_geocode(lat: float, lng: float) -> dict:
    api_key = settings.OPENCAGE_API_KEY
    if not api_key:
        return {"city": None, "state": None, "country": None, "zip": None}

    url = "https://api.opencagedata.com/geocode/v1/json"
    params = {
        "q": f"{lat},{lng}",
        "key": api_key,
        "no_annotations": 1,
        "limit": 1
    }

    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            data = r.json()
            
            if data and data.get("results"):
                components = data["results"][0].get("components", {})
                return {
                    "city": components.get("city") or components.get("town") or components.get("county"),
                    "state": components.get("state"),
                    "country": components.get("country"),
                    "zip": components.get("postcode"),
                }
            return {"city": None, "state": None, "country": None, "zip": None}
    except Exception as e:
        print(f"Geocoding failed: {e}")
        return {"city": None, "state": None, "country": None, "zip": None}


@router.post("")
async def save_pwa_location(payload: LocationPayload, db: Session = Depends(get_db)):
    """
    The PWA hits this endpoint right before dialing the phone number.
    Saves exact GPS linked to the phone number.
    """
    # Standardize phone format (ensure it has a +)
    phone = payload.phone_number.strip()
    if not phone.startswith("+"):
        phone = f"+{phone}"

    # Get address details from OpenCage
    geo_data = await reverse_geocode(payload.lat, payload.lng)

    # Generate a UUID for this incoming session
    session_id = uuid.uuid4()
    
    # Save a pending session waiting for Twilio to call
    new_session = CallSession(
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
    db.add(new_session)

    # Save exact GPS
    new_geo = Geolocation(
        call_id=session_id,
        latitude=payload.lat,
        longitude=payload.lng,
        is_simulated=False
    )
    db.add(new_geo)
    db.commit()

    return {"status": "ok", "message": "Location saved, ready for call"}
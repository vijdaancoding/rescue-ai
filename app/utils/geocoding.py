"""
Reverse geocoding helper.

Default provider is Nominatim (OpenStreetMap) — free, no API key required.
Set GEOCODING_PROVIDER=google in env to use Google Maps Geocoding instead;
that branch reads GOOGLE_MAPS_API_KEY (falls back to GOOGLE_API_KEY).

Uses the app's shared httpx.AsyncClient so per-call TCP/TLS handshakes are
avoided. Always returns a dict of the same shape — callers never have to
handle None separately.
"""
from __future__ import annotations

from loguru import logger

from app.core import http_client
from app.core.config import settings

_EMPTY: dict[str, str | None] = {"city": None, "state": None, "country": None, "zip": None}

_GOOGLE_ENDPOINT = "https://maps.googleapis.com/maps/api/geocode/json"
_NOMINATIM_ENDPOINT = "https://nominatim.openstreetmap.org/reverse"

# Nominatim requires an identifying User-Agent per their usage policy.
_NOMINATIM_UA = "rescue-ai/1.0 (emergency-helpline; contact: admin@rescueai)"


def _extract_google(components: list[dict], target_type: str) -> str | None:
    for comp in components:
        if target_type in comp.get("types", []):
            return comp.get("long_name")
    return None


async def _reverse_google(lat: float, lng: float) -> dict[str, str | None]:
    api_key = settings.GOOGLE_MAPS_API_KEY or settings.GOOGLE_API_KEY
    if not api_key:
        logger.warning("GOOGLE_MAPS_API_KEY not set — skipping reverse geocode")
        return dict(_EMPTY)

    params = {"latlng": f"{lat},{lng}", "key": api_key}
    try:
        r = await http_client.get().get(_GOOGLE_ENDPOINT, params=params, timeout=6.0)
        r.raise_for_status()
        data = r.json()
    except Exception as exc:
        logger.warning("Google reverse geocode failed for ({}, {}): {}", lat, lng, exc)
        return dict(_EMPTY)

    if data.get("status") != "OK" or not data.get("results"):
        logger.warning("Google geocode non-OK status: {}", data.get("status"))
        return dict(_EMPTY)

    components = data["results"][0].get("address_components", [])
    return {
        "city": (
            _extract_google(components, "locality")
            or _extract_google(components, "postal_town")
            or _extract_google(components, "administrative_area_level_2")
            or _extract_google(components, "sublocality")
        ),
        "state": _extract_google(components, "administrative_area_level_1"),
        "country": _extract_google(components, "country"),
        "zip": _extract_google(components, "postal_code"),
    }


async def _reverse_nominatim(lat: float, lng: float) -> dict[str, str | None]:
    params = {
        "lat": str(lat),
        "lon": str(lng),
        "format": "jsonv2",
        "zoom": "14",  # city-level detail
        "addressdetails": "1",
    }
    try:
        r = await http_client.get().get(
            _NOMINATIM_ENDPOINT,
            params=params,
            headers={
                "User-Agent": _NOMINATIM_UA,
                "Accept": "application/json",
                # Force English — matches Twilio FromCity/FromState casing and avoids
                # mixing Urdu and English in the same call_sessions row.
                "Accept-Language": "en",
            },
            timeout=6.0,
        )
        r.raise_for_status()
        data = r.json()
    except Exception as exc:
        logger.warning("Nominatim reverse geocode failed for ({}, {}): {}", lat, lng, exc)
        return dict(_EMPTY)

    addr = data.get("address") or {}
    return {
        "city": (
            addr.get("city")
            or addr.get("town")
            or addr.get("village")
            or addr.get("municipality")
            or addr.get("suburb")
            or addr.get("county")
        ),
        "state": addr.get("state") or addr.get("state_district") or addr.get("region"),
        "country": addr.get("country"),
        "zip": addr.get("postcode"),
    }


async def reverse_geocode(lat: float, lng: float) -> dict[str, str | None]:
    """
    Reverse-geocode GPS coordinates to address components.
    Returns keys: city, state, country, zip (any may be None).
    """
    provider = (settings.GEOCODING_PROVIDER or "nominatim").lower()
    if provider == "google":
        return await _reverse_google(lat, lng)
    return await _reverse_nominatim(lat, lng)

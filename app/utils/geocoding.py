"""
OpenCage reverse geocoding helper.

Uses the app's shared httpx.AsyncClient so per-call TCP/TLS handshakes are
avoided. Always returns a dict of the same shape — callers never have to
handle None separately.
"""
from __future__ import annotations

from loguru import logger

from app.core import http_client
from app.core.config import settings

_ENDPOINT = "https://api.opencagedata.com/geocode/v1/json"
_EMPTY: dict[str, str | None] = {"city": None, "state": None, "country": None, "zip": None}


async def reverse_geocode(lat: float, lng: float) -> dict[str, str | None]:
    """
    Reverse-geocode GPS coordinates to address components.
    Returns keys: city, state, country, zip (any may be None).
    """
    api_key = settings.OPENCAGE_API_KEY
    if not api_key:
        logger.warning("OPENCAGE_API_KEY not set — skipping reverse geocode")
        return dict(_EMPTY)

    params = {
        "q": f"{lat},{lng}",
        "key": api_key,
        "no_annotations": 1,
    }

    try:
        r = await http_client.get().get(_ENDPOINT, params=params, timeout=6.0)
        r.raise_for_status()
        data = r.json()
    except Exception as exc:
        logger.warning("Reverse geocode failed for ({}, {}): {}", lat, lng, exc)
        return dict(_EMPTY)

    results = data.get("results") or []
    if not results:
        return dict(_EMPTY)

    components = results[0].get("components", {})
    return {
        "city": components.get("city") or components.get("town") or components.get("county"),
        "state": components.get("state"),
        "country": components.get("country"),
        "zip": components.get("postcode"),
    }

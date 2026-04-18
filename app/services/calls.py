from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from livekit.api import AccessToken, VideoGrants

from app.core.config import settings
from app.db.models import CallSession
from app.repositories.ai_metadata import AiMetadataRepository
from app.repositories.calls import CallRepository
from app.repositories.dispatches import DispatchRepository
from app.repositories.geolocation import GeolocationRepository
from app.schemas.calls import (
    ALLOWED_STATUSES,
    CallContext,
    CallFilters,
    CallSummary,
    ListenerToken,
)
from app.services.errors import NotFoundError, ValidationError


_LISTENER_TTL = timedelta(hours=2)


def _duration_seconds(call: CallSession) -> Optional[int]:
    if not call.start_time or not call.end_time:
        return None
    start = (
        call.start_time
        if call.start_time.tzinfo
        else call.start_time.replace(tzinfo=timezone.utc)
    )
    end = (
        call.end_time
        if call.end_time.tzinfo
        else call.end_time.replace(tzinfo=timezone.utc)
    )
    return int((end - start).total_seconds())


def _build_summary(
    call: CallSession,
    meta,
    dispatch_types: list[str],
    geo=None,
) -> CallSummary:
    return CallSummary(
        id=str(call.id),
        start_time=call.start_time.isoformat() if call.start_time else None,
        end_time=call.end_time.isoformat() if call.end_time else None,
        duration_seconds=_duration_seconds(call),
        status=call.status,
        caller_phone=call.caller_phone,
        caller_city=call.caller_city,
        caller_country=call.caller_country,
        lat=geo.latitude if geo else None,
        lng=geo.longitude if geo else None,
        spam_label=meta.sentiment_label if meta else None,
        urgency_level=meta.urgency_level if meta else None,
        scam_probability=meta.scam_probability if meta else None,
        dispatch_types=dispatch_types,
    )


def _parse_date(value: Optional[str], *, end_of_day: bool) -> Optional[datetime]:
    if not value:
        return None
    iso = f"{value}T23:59:59" if end_of_day else value
    return datetime.fromisoformat(iso)


def list_calls(
    filters: CallFilters,
    *,
    calls: CallRepository,
    ai_metadata: AiMetadataRepository,
    dispatches: DispatchRepository,
    geolocation: GeolocationRepository,
) -> list[CallSummary]:
    rows = calls.list_filtered(
        status=filters.status,
        spam_label=filters.spam_label,
        date_from=_parse_date(filters.date_from, end_of_day=False),
        date_to=_parse_date(filters.date_to, end_of_day=True),
        search=filters.search,
        offset=(filters.page - 1) * filters.limit,
        limit=filters.limit,
    )
    if not rows:
        return []

    call_ids = [c.id for c in rows]
    meta_map = ai_metadata.latest_for_calls(call_ids)
    dispatch_map = dispatches.types_by_call(call_ids)
    geo_map = geolocation.latest_for_calls(call_ids)

    return [
        _build_summary(
            call,
            meta_map.get(str(call.id)),
            dispatch_map.get(str(call.id), []),
            geo_map.get(str(call.id)),
        )
        for call in rows
    ]


def get_one(
    call_id: str,
    *,
    calls: CallRepository,
    ai_metadata: AiMetadataRepository,
    dispatches: DispatchRepository,
    geolocation: GeolocationRepository,
) -> CallSummary:
    call = calls.get(uuid.UUID(call_id))
    if not call:
        raise NotFoundError("Call not found")
    meta = ai_metadata.latest_for_calls([call.id]).get(str(call.id))
    dispatch_types = dispatches.types_by_call([call.id]).get(str(call.id), [])
    geo = geolocation.latest_for_calls([call.id]).get(str(call.id))
    return _build_summary(call, meta, dispatch_types, geo)


def update_status(
    call_id: str, new_status: str, *, calls: CallRepository
) -> dict[str, str]:
    if new_status not in ALLOWED_STATUSES:
        raise ValidationError(f"Invalid status. Allowed: {sorted(ALLOWED_STATUSES)}")
    call = calls.get(uuid.UUID(call_id))
    if not call:
        raise NotFoundError("Call not found")

    call.status = new_status
    if new_status == "FalseAlarm" and call.end_time is None:
        call.end_time = datetime.now(timezone.utc)
    calls.save(call)
    return {"call_id": call_id, "status": call.status}


def _build_context(
    call: CallSession,
    *,
    geolocation: GeolocationRepository,
) -> CallContext:
    geo = geolocation.latest_for_call(call.id)
    has_location = bool(call.caller_city or (geo and geo.latitude is not None))
    return CallContext(
        has_location=has_location,
        call_id=str(call.id),
        city=call.caller_city,
        state=call.caller_state,
        country=call.caller_country,
        lat=geo.latitude if geo else None,
        lng=geo.longitude if geo else None,
    )


def get_context(
    room_name: str,
    *,
    calls: CallRepository,
    geolocation: GeolocationRepository,
) -> CallContext:
    call = calls.get_by_room(room_name)
    if not call:
        return CallContext(has_location=False)
    return _build_context(call, geolocation=geolocation)


def mint_listener_token(call_id: str, *, calls: CallRepository) -> ListenerToken:
    """Mint a subscribe-only LiveKit token so a dispatcher can observe the live
    call. Requires the call to already have a room_name (agent connected)."""
    call = calls.get(uuid.UUID(call_id))
    if not call:
        raise NotFoundError("Call not found")
    if not call.room_name:
        raise ValidationError(
            "Call has no room yet — agent hasn't joined or call ended before binding"
        )

    grants = VideoGrants(
        room_join=True,
        room=call.room_name,
        can_publish=False,
        can_subscribe=True,
        can_publish_data=False,
    )
    token = (
        AccessToken(settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET)
        .with_identity(f"listener-{uuid.uuid4()}")
        .with_name("Dispatcher")
        .with_ttl(_LISTENER_TTL)
        .with_grants(grants)
        .to_jwt()
    )
    return ListenerToken(
        token=token,
        room_name=call.room_name,
        livekit_url=settings.LIVEKIT_URL,
    )


def bind_room_for_phone(
    phone: str,
    room_name: str,
    *,
    calls: CallRepository,
    geolocation: GeolocationRepository,
) -> CallContext:
    """Bind a LiveKit room name to the most recent call row for this phone.
    Called by the agent on connect for SIP-originated rooms, where the Twilio
    webhook creates the row but can't know the LiveKit-assigned room name."""
    call = calls.find_latest_for_phone(phone)
    if not call:
        return CallContext(has_location=False)

    if call.room_name != room_name:
        call.room_name = room_name
        calls.save(call)

    return _build_context(call, geolocation=geolocation)

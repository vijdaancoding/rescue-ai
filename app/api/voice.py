"""
WebSocket endpoint that bridges a browser caller to a LiveKit room + agent.

The endpoint is async (required for WebSockets) but our SQLAlchemy session is
sync — any DB call here is wrapped in `asyncio.to_thread` so it doesn't block
the event loop while Supabase replies.
"""
from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from livekit.api import AccessToken, CreateAgentDispatchRequest, LiveKitAPI, VideoGrants
from loguru import logger
from sqlalchemy.orm import Session
from starlette.websockets import WebSocketState

from app.api.deps import get_db
from app.core.config import settings
from app.db.models import CallSession, Geolocation
from app.utils.geocoding import reverse_geocode

router = APIRouter(prefix="/ws", tags=["Voice"])

AGENT_NAME = "rescue-operator"
_TOKEN_TTL = timedelta(hours=2)


def _mint_token(identity: str, display_name: str, room: str, *, publish: bool) -> str:
    """Build a signed LiveKit access token. Pure CPU — fine to call from async."""
    grants = VideoGrants(
        room_join=True,
        room=room,
        can_publish=publish,
        can_subscribe=True,
        can_publish_data=publish,
    )
    return (
        AccessToken(settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET)
        .with_identity(identity)
        .with_name(display_name)
        .with_ttl(_TOKEN_TTL)
        .with_grants(grants)
        .to_jwt()
    )


def _create_call_row(db: Session, caller_hash: str, room_name: str) -> CallSession:
    call = CallSession(caller_hash=caller_hash, status="Incoming", room_name=room_name)
    db.add(call)
    db.commit()
    db.refresh(call)
    return call


def _save_geolocation(
    db: Session, call_id, lat: float, lng: float, geo_data: dict[str, Optional[str]]
) -> None:
    call = db.query(CallSession).filter(CallSession.id == call_id).first()
    if call is None:
        return
    call.caller_city = geo_data["city"]
    call.caller_state = geo_data["state"]
    call.caller_country = geo_data["country"]
    call.caller_zip = geo_data["zip"]
    db.add(Geolocation(call_id=call_id, latitude=lat, longitude=lng, is_simulated=True))
    db.commit()


def _mark_call_active(db: Session, call_id) -> None:
    call = db.query(CallSession).filter(CallSession.id == call_id).first()
    if call is not None:
        call.status = "Active"
        db.commit()


def _close_call(db: Session, call_id) -> None:
    call = db.query(CallSession).filter(CallSession.id == call_id).first()
    if call is None:
        return
    call.end_time = datetime.now(timezone.utc)
    call.status = "FalseAlarm"
    db.commit()


@router.websocket("/call")
async def websocket_call(
    websocket: WebSocket,
    db: Session = Depends(get_db),
    lat: Optional[float] = Query(default=None),
    lng: Optional[float] = Query(default=None),
) -> None:
    await websocket.accept()

    caller_hash = f"anon-{uuid.uuid4()}"
    room_name = f"call-{uuid.uuid4()}"

    call = await asyncio.to_thread(_create_call_row, db, caller_hash, room_name)
    call_id = call.id

    # Kick off reverse geocoding in parallel with LiveKit dispatch work.
    geocode_task = (
        asyncio.create_task(reverse_geocode(lat, lng))
        if lat is not None and lng is not None
        else None
    )

    try:
        dispatcher_token = _mint_token(
            f"dispatcher-{uuid.uuid4()}", "Dispatcher", room_name, publish=False
        )
        caller_token = _mint_token(caller_hash, "Caller", room_name, publish=True)

        location_meta: dict = {}
        if geocode_task is not None:
            try:
                geo_data = await asyncio.wait_for(geocode_task, timeout=3.0)
            except asyncio.TimeoutError:
                logger.warning("Reverse geocode timed out for call {}", call_id)
                geo_data = {"city": None, "state": None, "country": None, "zip": None}
            await asyncio.to_thread(_save_geolocation, db, call_id, lat, lng, geo_data)
            location_meta = {
                "lat": lat,
                "lng": lng,
                "city": geo_data["city"],
                "state": geo_data["state"],
                "country": geo_data["country"],
            }

        async with LiveKitAPI(
            url=settings.LIVEKIT_URL,
            api_key=settings.LIVEKIT_API_KEY,
            api_secret=settings.LIVEKIT_API_SECRET,
        ) as lkapi:
            await lkapi.agent_dispatch.create_dispatch(
                CreateAgentDispatchRequest(
                    agent_name=AGENT_NAME,
                    room=room_name,
                    metadata=json.dumps(
                        {
                            "call_id": str(call_id),
                            "caller_identity": caller_hash,
                            "location": location_meta,
                        }
                    ),
                )
            )

        await asyncio.to_thread(_mark_call_active, db, call_id)

        # The client might have reloaded the page during setup. Don't try to
        # send to a closed socket — the finally block will still clean up.
        if websocket.client_state != WebSocketState.CONNECTED:
            return

        await websocket.send_json(
            {
                "token": dispatcher_token,
                "caller_token": caller_token,
                "room_name": room_name,
                "livekit_url": settings.LIVEKIT_URL,
                "call_id": str(call_id),
            }
        )

        while True:
            data = await websocket.receive_text()
            if data == "end_call":
                break

    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.exception("WS call {} crashed: {}", call_id, exc)
    finally:
        try:
            await asyncio.to_thread(_close_call, db, call_id)
        except Exception as exc:
            logger.warning("Failed to close call {} in DB: {}", call_id, exc)

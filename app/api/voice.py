"""
WebSocket endpoint that bridges a browser caller to a LiveKit room + agent.

The endpoint is async (required for WebSockets); SQLAlchemy is sync so every
DB call is wrapped in `asyncio.to_thread` to keep the event loop responsive.
"""
from __future__ import annotations

import asyncio
import json
import uuid
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from livekit.api import AccessToken, CreateAgentDispatchRequest, LiveKitAPI, VideoGrants
from loguru import logger
from starlette.websockets import WebSocketState

from app.api.deps import get_call_repo, get_geolocation_repo
from app.core.config import settings
from app.repositories.calls import CallRepository
from app.repositories.geolocation import GeolocationRepository
from app.services import voice as voice_service
from app.utils.geocoding import reverse_geocode

router = APIRouter(prefix="/ws", tags=["Voice"])

AGENT_NAME = "rescue-operator"
_TOKEN_TTL = timedelta(hours=2)
_GEOCODE_TIMEOUT_SECONDS = 3.0


def _mint_token(
    identity: str, display_name: str, room: str, *, publish: bool
) -> str:
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


async def _resolve_location(
    call_id: uuid.UUID,
    lat: Optional[float],
    lng: Optional[float],
    *,
    calls: CallRepository,
    geolocation: GeolocationRepository,
) -> dict:
    if lat is None or lng is None:
        return {}
    try:
        geo_data = await asyncio.wait_for(
            reverse_geocode(lat, lng), timeout=_GEOCODE_TIMEOUT_SECONDS
        )
    except asyncio.TimeoutError:
        logger.warning("Reverse geocode timed out for call {}", call_id)
        geo_data = {"city": None, "state": None, "country": None, "zip": None}

    await asyncio.to_thread(
        voice_service.save_geolocation,
        call_id=call_id,
        lat=lat,
        lng=lng,
        geo_data=geo_data,
        calls=calls,
        geolocation=geolocation,
    )
    return {
        "lat": lat,
        "lng": lng,
        "city": geo_data.get("city"),
        "state": geo_data.get("state"),
        "country": geo_data.get("country"),
    }


async def _dispatch_agent(room_name: str, metadata: dict) -> None:
    async with LiveKitAPI(
        url=settings.LIVEKIT_URL,
        api_key=settings.LIVEKIT_API_KEY,
        api_secret=settings.LIVEKIT_API_SECRET,
    ) as lkapi:
        await lkapi.agent_dispatch.create_dispatch(
            CreateAgentDispatchRequest(
                agent_name=AGENT_NAME,
                room=room_name,
                metadata=json.dumps(metadata),
            )
        )


@router.websocket("/call")
async def websocket_call(
    websocket: WebSocket,
    calls: CallRepository = Depends(get_call_repo),
    geolocation: GeolocationRepository = Depends(get_geolocation_repo),
    lat: Optional[float] = Query(default=None),
    lng: Optional[float] = Query(default=None),
) -> None:
    await websocket.accept()

    caller_hash = f"anon-{uuid.uuid4()}"
    room_name = f"call-{uuid.uuid4()}"

    call = await asyncio.to_thread(
        voice_service.create_incoming_call,
        caller_hash=caller_hash,
        room_name=room_name,
        calls=calls,
    )
    call_id = call.id

    try:
        dispatcher_token = _mint_token(
            f"dispatcher-{uuid.uuid4()}", "Dispatcher", room_name, publish=False
        )
        caller_token = _mint_token(caller_hash, "Caller", room_name, publish=True)

        location_meta = await _resolve_location(
            call_id, lat, lng, calls=calls, geolocation=geolocation
        )

        await _dispatch_agent(
            room_name,
            {
                "call_id": str(call_id),
                "caller_identity": caller_hash,
                "location": location_meta,
            },
        )

        await asyncio.to_thread(
            voice_service.mark_active, call_id=call_id, calls=calls
        )

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
            await asyncio.to_thread(
                voice_service.close_call, call_id=call_id, calls=calls
            )
        except Exception as exc:
            logger.warning("Failed to close call {} in DB: {}", call_id, exc)

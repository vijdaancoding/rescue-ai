import json
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from starlette.websockets import WebSocketState

from livekit.api import LiveKitAPI, AccessToken, VideoGrants, CreateAgentDispatchRequest

from app.api.deps import get_db
from app.core.config import settings
from app.db.models import CallSession

router = APIRouter(prefix="/ws", tags=["Voice"])

AGENT_NAME = "rescue-operator"


@router.websocket("/call")
async def websocket_call(websocket: WebSocket, db: Session = Depends(get_db)):
    await websocket.accept()

    caller_hash = f"anon-{uuid.uuid4()}"
    room_name = f"call-{uuid.uuid4()}"

    call = CallSession(caller_hash=caller_hash, status="Incoming")
    db.add(call)
    db.commit()
    db.refresh(call)

    try:
        # Dispatcher token: subscribe-only (the dashboard just watches)
        token = (
            AccessToken(settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET)
            .with_identity(f"dispatcher-{uuid.uuid4()}")
            .with_name("Dispatcher")
            .with_ttl(timedelta(hours=2))
            .with_grants(VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=False,
                can_subscribe=True,
            ))
            .to_jwt()
        )

        # Caller token: can publish audio (simulates Twilio in production)
        caller_token = (
            AccessToken(settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET)
            .with_identity(caller_hash)
            .with_name("Caller")
            .with_ttl(timedelta(hours=2))
            .with_grants(VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True,
            ))
            .to_jwt()
        )

        async with LiveKitAPI(
            url=settings.LIVEKIT_URL,
            api_key=settings.LIVEKIT_API_KEY,
            api_secret=settings.LIVEKIT_API_SECRET,
        ) as lkapi:
            await lkapi.agent_dispatch.create_dispatch(
                CreateAgentDispatchRequest(
                    agent_name=AGENT_NAME,
                    room=room_name,
                    # Include caller_identity so the agent knows which participant to listen to
                    metadata=json.dumps({
                        "call_id": str(call.id),
                        "caller_identity": caller_hash,
                    }),
                )
            )

        call.status = "Active"
        db.commit()

        # Guard: client may have disconnected during setup (e.g. browser reload)
        if websocket.client_state != WebSocketState.CONNECTED:
            return

        await websocket.send_json({
            "token": token,
            "caller_token": caller_token,
            "room_name": room_name,
            "livekit_url": settings.LIVEKIT_URL,
            "call_id": str(call.id),
        })

        while True:
            data = await websocket.receive_text()
            if data == "end_call":
                break

    except WebSocketDisconnect:
        pass
    except Exception:
        # Covers uvicorn's ClientDisconnected and any LiveKit API errors
        pass
    finally:
        call = db.query(CallSession).filter(CallSession.id == call.id).first()
        if call:
            call.end_time = datetime.now(timezone.utc)
            call.status = "FalseAlarm"
            db.commit()

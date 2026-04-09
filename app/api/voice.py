import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session

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

    token = (
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
                metadata=str(call.id),
            )
        )

    call.status = "Active"
    db.commit()

    await websocket.send_json({
        "token": token,
        "room_name": room_name,
        "livekit_url": settings.LIVEKIT_URL,
        "call_id": str(call.id),
    })

    try:
        while True:
            data = await websocket.receive_text()
            if data == "end_call":
                break
    except WebSocketDisconnect:
        pass
    finally:
        call = db.query(CallSession).filter(CallSession.id == call.id).first()
        call.end_time = datetime.now(timezone.utc)
        call.status = "FalseAlarm"
        db.commit()

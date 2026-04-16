from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Form, Response
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings
from app.db.models import CallSession

router = APIRouter(prefix="/twilio", tags=["Twilio"])


@router.post("/voice")
async def twilio_voice_webhook(
    db: Session = Depends(get_db),
    From: str = Form(default=""),
    CallSid: str = Form(default=""),
    FromCity: str = Form(default=""),
    FromState: str = Form(default=""),
    FromZip: str = Form(default=""),
    FromCountry: str = Form(default=""),
):
    """
    Twilio hits this when someone calls our number.
    We record the caller phone + geo, then forward the audio to LiveKit
    via SIP. LiveKit's inbound trunk + dispatch rule create the room
    and auto-dispatch the rescue-operator agent.
    """
    call = CallSession(
        caller_hash=f"twilio-{CallSid}",
        status="Active",
        caller_phone=From or None,
        caller_city=FromCity or None,
        caller_state=FromState or None,
        caller_country=FromCountry or None,
        caller_zip=FromZip or None,
    )
    db.add(call)
    db.commit()

    sip_host = settings.LIVEKIT_SIP_URI.replace("sip:", "").strip()
    sip_target = f"sip:{settings.TWILIO_PHONE_NUMBER}@{sip_host};transport=tcp"

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Dial answerOnBridge="true">
        <Sip username="{settings.LIVEKIT_SIP_USERNAME}" password="{settings.LIVEKIT_SIP_PASSWORD}">{sip_target}</Sip>
    </Dial>
</Response>"""

    return Response(content=twiml, media_type="application/xml")


@router.post("/status")
async def twilio_call_status(
    db: Session = Depends(get_db),
    CallSid: str = Form(default=""),
    CallStatus: str = Form(default=""),
):
    if CallStatus in ("completed", "failed", "busy", "no-answer", "canceled"):
        call = (
            db.query(CallSession)
            .filter(CallSession.caller_hash == f"twilio-{CallSid}")
            .first()
        )
        if call:
            call.end_time = datetime.now(timezone.utc)
            if call.status == "Active":
                call.status = "FalseAlarm"
            db.commit()
    return Response(status_code=204)

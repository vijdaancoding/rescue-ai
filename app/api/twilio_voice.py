import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Form, Response
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings
from app.db.models import CallSession

router = APIRouter(prefix="/twilio", tags=["Twilio"])


@router.post("/voice")
def twilio_voice_webhook(
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
    Checks if the user just submitted exact GPS via the PWA.
    If not, falls back to Twilio's rough cell-tower estimates.
    """
    # 1. Look for a pending PWA location submission for this phone number
    existing_session = (
        db.query(CallSession)
        .filter(
            CallSession.caller_phone == From,
            CallSession.status == "WaitingForCall",
        )
        .order_by(CallSession.start_time.desc())
        .first()
    )

    if existing_session:
        # User used the PWA — update the pending session with Twilio's live Call ID
        existing_session.caller_hash = f"twilio-{CallSid}"
        existing_session.status = "Active"
        existing_session.start_time = datetime.now(timezone.utc)
        db.commit()
    else:
        # User dialed manually (no PWA) — create a new session from Twilio's data
        call = CallSession(
            id=uuid.uuid4(),
            caller_hash=f"twilio-{CallSid}",
            status="Active",
            start_time=datetime.now(timezone.utc),
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
def twilio_call_status(
    db: Session = Depends(get_db),
    CallSid: str = Form(default=""),
    CallStatus: str = Form(default=""),
):
    """Handle Twilio call-status webhooks (hang-ups, failures, etc.)."""
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

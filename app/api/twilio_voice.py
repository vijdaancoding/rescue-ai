"""
Twilio webhooks: inbound voice (TwiML to dial LiveKit SIP) + status callbacks.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Response

from app.api.deps import get_call_repo
from app.repositories.calls import CallRepository
from app.services import twilio as twilio_service

router = APIRouter(prefix="/twilio", tags=["Twilio"])


@router.post("/voice")
def twilio_voice_webhook(
    From: str = Form(default=""),
    CallSid: str = Form(default=""),
    FromCity: str = Form(default=""),
    FromState: str = Form(default=""),
    FromZip: str = Form(default=""),
    FromCountry: str = Form(default=""),
    calls: CallRepository = Depends(get_call_repo),
) -> Response:
    """
    Handle Twilio's inbound voice webhook.

    If the caller first submitted GPS via the PWA we upgrade that pending row
    in-place; otherwise we record a new session from Twilio's cell-tower data.
    """
    twilio_service.upsert_incoming_call(
        from_phone=From,
        call_sid=CallSid,
        city=FromCity,
        state=FromState,
        country=FromCountry,
        zip_code=FromZip,
        calls=calls,
    )
    return Response(content=twilio_service.dial_sip_twiml(), media_type="application/xml")


@router.post("/status")
def twilio_call_status(
    CallSid: str = Form(default=""),
    CallStatus: str = Form(default=""),
    calls: CallRepository = Depends(get_call_repo),
) -> Response:
    """React to Twilio terminal statuses (completed, failed, busy, etc.)."""
    twilio_service.handle_status_update(
        call_sid=CallSid, call_status=CallStatus, calls=calls
    )
    return Response(status_code=204)

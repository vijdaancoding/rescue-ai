from __future__ import annotations

import html
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.core.config import settings
from app.repositories.calls import CallRepository

_TERMINAL_TWILIO_STATUSES = frozenset(
    {"completed", "failed", "busy", "no-answer", "canceled"}
)


def upsert_incoming_call(
    *,
    from_phone: str,
    call_sid: str,
    city: Optional[str],
    state: Optional[str],
    country: Optional[str],
    zip_code: Optional[str],
    calls: CallRepository,
) -> None:
    existing = calls.find_pending_by_phone(from_phone) if from_phone else None
    if existing is not None:
        existing.caller_hash = f"twilio-{call_sid}"
        existing.status = "Active"
        existing.start_time = datetime.now(timezone.utc)
        calls.save(existing)
        return

    calls.create(
        id=uuid.uuid4(),
        caller_hash=f"twilio-{call_sid}",
        status="Active",
        start_time=datetime.now(timezone.utc),
        caller_phone=from_phone or None,
        caller_city=city or None,
        caller_state=state or None,
        caller_country=country or None,
        caller_zip=zip_code or None,
    )


def handle_status_update(
    *, call_sid: str, call_status: str, calls: CallRepository
) -> None:
    if call_status not in _TERMINAL_TWILIO_STATUSES:
        return
    call = calls.get_by_caller_hash(f"twilio-{call_sid}")
    if call is None:
        return
    call.end_time = datetime.now(timezone.utc)
    if call.status == "Active":
        call.status = "FalseAlarm"
    calls.save(call)


def dial_sip_twiml() -> str:
    sip_host = settings.LIVEKIT_SIP_URI.replace("sip:", "").strip()
    sip_target = f"sip:{settings.TWILIO_PHONE_NUMBER}@{sip_host};transport=tcp"
    username = html.escape(settings.LIVEKIT_SIP_USERNAME, quote=True)
    password = html.escape(settings.LIVEKIT_SIP_PASSWORD, quote=True)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response>"
        '<Dial answerOnBridge="true">'
        f'<Sip username="{username}" password="{password}">{html.escape(sip_target)}</Sip>'
        "</Dial>"
        "</Response>"
    )

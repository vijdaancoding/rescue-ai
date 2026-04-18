from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


ALLOWED_STATUSES = {"Incoming", "Active", "Dispatched", "FalseAlarm", "Archived", "WaitingForCall"}


class CallSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_seconds: Optional[int] = None
    status: Optional[str] = None
    caller_phone: Optional[str] = None
    caller_city: Optional[str] = None
    caller_country: Optional[str] = None
    # Precise lat/lng when available (PWA submitted GPS) — used for the live map.
    lat: Optional[float] = None
    lng: Optional[float] = None
    spam_label: Optional[str] = None
    urgency_level: Optional[str] = None
    scam_probability: Optional[int] = None
    dispatch_types: list[str] = Field(default_factory=list)


class CallContext(BaseModel):
    has_location: bool
    call_id: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None


class StatusUpdate(BaseModel):
    status: str


class BindRoomRequest(BaseModel):
    phone: str = Field(min_length=1)
    room_name: str = Field(min_length=1)


class ListenerToken(BaseModel):
    token: str
    room_name: str
    livekit_url: str


class CallFilters(BaseModel):
    """Pure filter params — keeps router signature flat but logic testable."""
    status: Optional[str] = None
    spam_label: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    search: Optional[str] = None
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=50, ge=1, le=200)

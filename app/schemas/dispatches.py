from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


VALID_DISPATCH_TYPES: frozenset[str] = frozenset({"police", "ambulance", "firefighters"})
VALID_DISPATCH_STATUSES: frozenset[str] = frozenset(
    {"dispatched", "en_route", "on_scene", "resolved"}
)


class DispatchCreate(BaseModel):
    call_id: str
    dispatch_types: list[str]
    ai_recommended: list[str] = Field(default_factory=list)
    notes: Optional[str] = None


class DispatchStatusUpdate(BaseModel):
    status: str


class DispatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: str
    call_id: str
    dispatch_type: str
    status: str
    notes: Optional[str] = None
    ai_recommended: bool

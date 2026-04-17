from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class ProbeOut(BaseModel):
    name: str
    ok: bool
    latency_ms: float
    detail: str = ""


class HealthStatus(BaseModel):
    ok: bool
    probes: list[ProbeOut]
    uptime_seconds: float
    version: str


class EndpointStats(BaseModel):
    method: str
    path: str
    count_recent: int
    count_total: int
    errors_total: int
    p50_ms: float
    p95_ms: float
    p99_ms: float
    avg_ms: float
    max_ms: float


class ErrorSample(BaseModel):
    ts: float
    method: str
    path: str
    status: int
    duration_ms: float
    request_id: Optional[str] = None


class MetricsResponse(BaseModel):
    started_at: float
    uptime_seconds: float
    total_requests: int
    total_errors: int
    endpoints: list[EndpointStats]
    recent_errors: list[ErrorSample]

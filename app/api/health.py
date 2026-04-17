"""
Health + observability endpoints.

- GET /health/live     — cheap liveness probe (always 200 if process is up)
- GET /health/status   — readiness: DB + external API probes
- GET /health/metrics  — per-endpoint latency + error snapshot
- GET /health/errors   — just the recent-errors tail
- WS  /health/ws       — live-tail of request + error events
"""
from __future__ import annotations

import asyncio
from typing import Optional

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from loguru import logger
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.observability import collector
from app.schemas.health import (
    ErrorSample,
    HealthStatus,
    MetricsResponse,
    ProbeOut,
)
from app.services import health as health_service

router = APIRouter(prefix="/health", tags=["Health"])

_APP_VERSION = "1.0"


@router.get("/live")
def liveness() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/status", response_model=HealthStatus)
async def readiness(db: Session = Depends(get_db)) -> HealthStatus:
    probes = await health_service.run_probes(db)
    snap = collector.snapshot()
    return HealthStatus(
        ok=all(p.ok for p in probes),
        probes=[
            ProbeOut(name=p.name, ok=p.ok, latency_ms=p.latency_ms, detail=p.detail)
            for p in probes
        ],
        uptime_seconds=snap["uptime_seconds"],
        version=_APP_VERSION,
    )


@router.get("/metrics", response_model=MetricsResponse)
def metrics() -> MetricsResponse:
    snap = collector.snapshot()
    return MetricsResponse(**snap)


@router.get("/errors", response_model=list[ErrorSample])
def errors(limit: int = 50) -> list[ErrorSample]:
    return [ErrorSample(**e) for e in collector.recent_errors(limit=limit)]


@router.websocket("/ws")
async def health_ws(websocket: WebSocket) -> None:
    """Live-tail of requests + errors. Pushes each sample as JSON."""
    await websocket.accept()
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue[dict] = asyncio.Queue(maxsize=200)

    def _sink(payload: dict) -> None:
        # Called from the request thread; hop back to the event loop.
        try:
            loop.call_soon_threadsafe(queue.put_nowait, payload)
        except RuntimeError:
            pass
        except asyncio.QueueFull:
            pass

    collector.subscribe(_sink)
    try:
        while True:
            payload = await queue.get()
            await websocket.send_json(payload)
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.warning("Health WS errored: {}", exc)
    finally:
        collector.unsubscribe(_sink)

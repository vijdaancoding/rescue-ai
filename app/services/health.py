"""
Liveness + readiness probes.

Runs a DB round-trip plus optional external-API pings concurrently so the
health endpoint latency is bounded by the slowest probe instead of the sum.
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Awaitable, Callable

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core import http_client
from app.core.config import settings


@dataclass
class ProbeResult:
    name: str
    ok: bool
    latency_ms: float
    detail: str = ""


async def _timed(name: str, fn: Callable[[], Awaitable[bool]]) -> ProbeResult:
    start = time.perf_counter()
    try:
        ok = await fn()
        latency = (time.perf_counter() - start) * 1000
        return ProbeResult(name=name, ok=ok, latency_ms=round(latency, 1))
    except Exception as exc:
        latency = (time.perf_counter() - start) * 1000
        return ProbeResult(
            name=name, ok=False, latency_ms=round(latency, 1), detail=str(exc)[:200]
        )


async def _probe_db(db: Session) -> bool:
    def ping() -> bool:
        db.execute(text("SELECT 1"))
        return True

    return await asyncio.to_thread(ping)


async def _probe_http(url: str) -> bool:
    resp = await http_client.get().get(url, timeout=4.0)
    return resp.status_code < 500


async def run_probes(db: Session) -> list[ProbeResult]:
    probes: list[tuple[str, Callable[[], Awaitable[bool]]]] = [
        ("database", lambda: _probe_db(db)),
    ]
    if settings.LIVEKIT_URL:
        # LiveKit Cloud exposes the same host over HTTPS for health checks.
        url = (
            settings.LIVEKIT_URL.replace("wss://", "https://")
            .replace("ws://", "http://")
            .rstrip("/")
        ) + "/"
        probes.append(("livekit", lambda u=url: _probe_http(u)))
    if settings.OPENCAGE_API_KEY:
        probes.append(
            (
                "opencage",
                lambda: _probe_http(
                    f"https://api.opencagedata.com/geocode/v1/json?q=0+0&key={settings.OPENCAGE_API_KEY}&no_annotations=1&limit=1"
                ),
            )
        )

    return await asyncio.gather(*[_timed(name, fn) for name, fn in probes])

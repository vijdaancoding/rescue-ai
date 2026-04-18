"""
In-process request/error telemetry.

We deliberately keep this in the single process — the goal is a live picture
of what this FastAPI instance is doing right now, not a replacement for a
real APM. Stats are computed on demand from bounded ring buffers, so memory
stays flat regardless of traffic.
"""
from __future__ import annotations

import math
import threading
import time
from bisect import insort
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Callable, Deque, Optional

_WINDOW_SECONDS = 300  # 5-minute rolling window for per-endpoint stats
_MAX_LATENCY_SAMPLES = 1024
_MAX_ERRORS = 200


@dataclass
class _EndpointStats:
    samples: Deque[tuple[float, float]] = field(default_factory=deque)  # (ts, ms)
    total_count: int = 0
    total_errors: int = 0

    def prune(self, now: float) -> None:
        cutoff = now - _WINDOW_SECONDS
        while self.samples and self.samples[0][0] < cutoff:
            self.samples.popleft()
        # Cap absolute size regardless of window to bound memory under storms.
        while len(self.samples) > _MAX_LATENCY_SAMPLES:
            self.samples.popleft()


@dataclass
class ErrorEvent:
    ts: float
    method: str
    path: str
    status: int
    request_id: Optional[str]
    duration_ms: float


def _percentile(sorted_values: list[float], p: float) -> float:
    if not sorted_values:
        return 0.0
    k = max(0, min(len(sorted_values) - 1, math.ceil(p * len(sorted_values)) - 1))
    return sorted_values[k]


class ObservabilityCollector:
    """Thread-safe ring-buffer collector. Singleton — see module-level `collector`."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._by_endpoint: dict[str, _EndpointStats] = defaultdict(_EndpointStats)
        self._errors: Deque[ErrorEvent] = deque(maxlen=_MAX_ERRORS)
        self._total_requests = 0
        self._total_errors = 0
        self._started_at = time.time()
        self._subscribers: list[Callable[[dict], None]] = []

    # ── Recording ─────────────────────────────────────────────────────────────

    def record(
        self,
        *,
        method: str,
        path: str,
        status: int,
        duration_ms: float,
        request_id: Optional[str] = None,
    ) -> None:
        now = time.time()
        key = f"{method} {path}"
        with self._lock:
            self._total_requests += 1
            stats = self._by_endpoint[key]
            stats.samples.append((now, duration_ms))
            stats.total_count += 1
            stats.prune(now)

            event: Optional[ErrorEvent] = None
            if status >= 400:
                stats.total_errors += 1
                self._total_errors += 1
                event = ErrorEvent(
                    ts=now,
                    method=method,
                    path=path,
                    status=status,
                    request_id=request_id,
                    duration_ms=duration_ms,
                )
                self._errors.append(event)

            subs = list(self._subscribers)

        payload = {
            "type": "sample",
            "method": method,
            "path": path,
            "status": status,
            "duration_ms": round(duration_ms, 2),
            "ts": now,
        }
        for sub in subs:
            try:
                sub(payload)
            except Exception:
                pass

        if event is not None:
            error_payload = {
                "type": "error",
                "method": event.method,
                "path": event.path,
                "status": event.status,
                "duration_ms": round(event.duration_ms, 2),
                "request_id": event.request_id,
                "ts": event.ts,
            }
            for sub in subs:
                try:
                    sub(error_payload)
                except Exception:
                    pass

    # ── Querying ──────────────────────────────────────────────────────────────

    def snapshot(self) -> dict:
        now = time.time()
        with self._lock:
            endpoints = []
            for key, stats in self._by_endpoint.items():
                stats.prune(now)
                samples = [d for _, d in stats.samples]
                if not samples:
                    # Drop idle endpoints from the live view once their window empties.
                    continue
                sorted_samples: list[float] = []
                for value in samples:
                    insort(sorted_samples, value)
                method, path = key.split(" ", 1)
                endpoints.append(
                    {
                        "method": method,
                        "path": path,
                        "count_recent": len(samples),
                        "count_total": stats.total_count,
                        "errors_total": stats.total_errors,
                        "p50_ms": round(_percentile(sorted_samples, 0.50), 2),
                        "p95_ms": round(_percentile(sorted_samples, 0.95), 2),
                        "p99_ms": round(_percentile(sorted_samples, 0.99), 2),
                        "avg_ms": round(sum(samples) / len(samples), 2),
                        "max_ms": round(max(samples), 2),
                    }
                )
            endpoints.sort(key=lambda e: e["count_recent"], reverse=True)

            errors = [
                {
                    "ts": e.ts,
                    "method": e.method,
                    "path": e.path,
                    "status": e.status,
                    "duration_ms": round(e.duration_ms, 2),
                    "request_id": e.request_id,
                }
                for e in list(self._errors)
            ]

            return {
                "started_at": self._started_at,
                "uptime_seconds": round(now - self._started_at, 1),
                "total_requests": self._total_requests,
                "total_errors": self._total_errors,
                "endpoints": endpoints,
                "recent_errors": list(reversed(errors)),
            }

    def recent_errors(self, limit: int = 50) -> list[dict]:
        with self._lock:
            return [
                {
                    "ts": e.ts,
                    "method": e.method,
                    "path": e.path,
                    "status": e.status,
                    "duration_ms": round(e.duration_ms, 2),
                    "request_id": e.request_id,
                }
                for e in list(self._errors)[-limit:][::-1]
            ]

    # ── Pub-sub for live-tail WebSocket ───────────────────────────────────────

    def subscribe(self, fn: Callable[[dict], None]) -> None:
        with self._lock:
            self._subscribers.append(fn)

    def unsubscribe(self, fn: Callable[[dict], None]) -> None:
        with self._lock:
            try:
                self._subscribers.remove(fn)
            except ValueError:
                pass


collector = ObservabilityCollector()

"""
HTTP middleware: request ID propagation + access logging + telemetry capture.

Every request gets a short request-ID (propagated from `X-Request-ID` if the
client sends one). The loguru patcher in app.core.logging pulls that ID out
of the ContextVar so log lines are tagged automatically, and the
observability collector receives a per-request sample for the /health page.
"""
from __future__ import annotations

import time
import uuid
from typing import Awaitable, Callable

from fastapi import Request, Response
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import request_id_ctx
from app.core.observability import collector


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
        token = request_id_ctx.set(request_id)
        start = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            path = request.url.path
            method = request.method
            logger.bind(
                method=method,
                path=path,
                status=status_code,
                duration_ms=round(duration_ms, 2),
            ).info("{} {} -> {} ({:.1f} ms)", method, path, status_code, duration_ms)
            try:
                collector.record(
                    method=method,
                    path=path,
                    status=status_code,
                    duration_ms=duration_ms,
                    request_id=request_id,
                )
            except Exception as exc:
                logger.warning("Collector record failed: {}", exc)
            request_id_ctx.reset(token)

"""
One shared httpx.AsyncClient for the whole app.

Reusing a single client reuses TCP + TLS connections across requests — per-call
geocoding and backend POSTs skip the handshake every time. Lifespan starts and
stops it.
"""
from __future__ import annotations

import httpx

_client: httpx.AsyncClient | None = None


def get() -> httpx.AsyncClient:
    if _client is None:
        raise RuntimeError("http_client not initialized — call startup() in the app lifespan")
    return _client


async def startup(*, timeout: float = 6.0, max_connections: int = 64) -> None:
    global _client
    if _client is not None:
        return
    limits = httpx.Limits(max_connections=max_connections, max_keepalive_connections=max_connections)
    _client = httpx.AsyncClient(timeout=timeout, limits=limits, http2=False)


async def shutdown() -> None:
    global _client
    if _client is None:
        return
    await _client.aclose()
    _client = None

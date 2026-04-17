"""
WebSocket endpoint for real-time dashboard updates.

All connected clients (Dashboard, LiveCall page) receive every analysis_update
broadcast. Clients filter by call_id on their end so each page only reacts
to the call it cares about.
"""
from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

router = APIRouter(prefix="/ws", tags=["Dashboard"])


class ConnectionManager:
    """Asyncio-safe registry of active dashboard WebSocket connections."""

    def __init__(self) -> None:
        self._connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.append(ws)
        logger.debug("Dashboard WS connected (total: {})", len(self._connections))

    def disconnect(self, ws: WebSocket) -> None:
        try:
            self._connections.remove(ws)
        except ValueError:
            pass
        logger.debug("Dashboard WS disconnected (total: {})", len(self._connections))

    async def broadcast(self, data: dict) -> None:
        """Fan out to every connected client; drop connections that error out."""
        dead: list[WebSocket] = []
        for ws in list(self._connections):
            try:
                await ws.send_json(data)
            except Exception as exc:
                logger.debug("Dropping dead WS: {}", exc)
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


# Singleton shared across the app (imported by api/analysis.py).
manager = ConnectionManager()


@router.websocket("/dashboard")
async def dashboard_ws(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    try:
        # Keep the connection alive; we don't care about client-sent frames.
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as exc:
        logger.warning("Dashboard WS errored: {}", exc)
        manager.disconnect(websocket)

from __future__ import annotations

from collections import defaultdict

from fastapi import WebSocket


class Broadcaster:
    def __init__(self) -> None:
        self._sockets: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, match_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._sockets[match_id].add(websocket)

    async def disconnect(self, match_id: str, websocket: WebSocket) -> None:
        self._sockets[match_id].discard(websocket)

    async def broadcast_snapshot(self, match_id: str, snapshot: dict) -> None:
        await self._broadcast(match_id, {"type": "snapshot", "data": snapshot})

    async def broadcast_event(self, match_id: str, event: dict) -> None:
        await self._broadcast(match_id, {"type": "event", "data": event})

    async def _broadcast(self, match_id: str, payload: dict) -> None:
        dead = []
        for ws in self._sockets.get(match_id, set()):
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._sockets[match_id].discard(ws)

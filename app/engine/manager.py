from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field

from fastapi import WebSocket

from app.api.schemas import MoveRequest, ResignRequest, UnlockRequest
from app.engine.game import MatchGame


@dataclass
class MatchRuntime:
    game: MatchGame
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    sockets: set[WebSocket] = field(default_factory=set)


class GameManager:
    def __init__(self) -> None:
        self._matches: dict[str, MatchRuntime] = {}

    async def create_match(self) -> MatchRuntime:
        match_id = uuid.uuid4().hex[:12]
        runtime = MatchRuntime(game=MatchGame(match_id))
        self._matches[match_id] = runtime
        return runtime

    def get_match(self, match_id: str) -> MatchRuntime | None:
        return self._matches.get(match_id)

    async def connect_socket(self, match_id: str, websocket: WebSocket) -> MatchRuntime | None:
        runtime = self.get_match(match_id)
        if runtime is None:
            return None
        await websocket.accept()
        runtime.sockets.add(websocket)
        await websocket.send_json({"type": "snapshot", "data": runtime.game.enriched_snapshot(time.time())})
        return runtime

    async def disconnect_socket(self, runtime: MatchRuntime, websocket: WebSocket) -> None:
        runtime.sockets.discard(websocket)

    async def handle_ws_command(self, runtime: MatchRuntime, payload: dict) -> dict[str, object]:
        now = time.time()
        cmd_type = payload.get("type")
        async with runtime.lock:
            if cmd_type == "move":
                req = MoveRequest.model_validate(payload)
                result = runtime.game.command_move(req.player, req.piece_id, req.target_x, req.target_y, now=now)
            elif cmd_type == "unlock":
                req = UnlockRequest.model_validate(payload)
                result = runtime.game.command_unlock(req.player, req.piece_type, now=now)
            elif cmd_type == "resign":
                req = ResignRequest.model_validate(payload)
                result = runtime.game.command_resign(req.player, now=now)
            else:
                result = type("R", (), {"ok": False, "message": "unsupported command"})()
            snapshot = runtime.game.enriched_snapshot(now)

        await self.broadcast(runtime, {"type": "snapshot", "data": snapshot})
        return {"ok": result.ok, "message": result.message, "snapshot": snapshot}

    async def broadcast(self, runtime: MatchRuntime, data: dict) -> None:
        dead: list[WebSocket] = []
        for ws in runtime.sockets:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            runtime.sockets.discard(ws)

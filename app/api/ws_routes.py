from __future__ import annotations

import json
import time

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.api.deps import get_container
from app.domain.enums import PieceType
from app.engine.snapshot import build_match_snapshot

router = APIRouter(tags=["ws"])


@router.websocket("/matches/{match_id}/ws")
@router.websocket("/ws/matches/{match_id}")
async def ws_match(websocket: WebSocket, match_id: str, container=Depends(get_container)):
    await container.broadcaster.connect(match_id, websocket)
    state = container.repo.get_match(match_id)
    if state:
        await websocket.send_json({"type": "snapshot", "data": build_match_snapshot(state, int(time.time() * 1000))})
    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            t = data.get("type")
            now = int(time.time() * 1000)
            if t == "move":
                ok, msg = container.command_service.handle_move_command(match_id, int(data["player"]), data["piece_id"], (int(data["target_x"]), int(data["target_y"])), now)
            elif t == "unlock":
                ok, msg = container.command_service.handle_unlock_command(match_id, int(data["player"]), PieceType(data["kind"]), now)
            elif t == "resign":
                ok, msg = container.command_service.handle_resign_command(match_id, int(data["player"]), now)
            else:
                ok, msg = False, "unsupported"
            await websocket.send_json({"type": "command_result", "data": {"ok": ok, "message": msg}})
    except WebSocketDisconnect:
        await container.broadcaster.disconnect(match_id, websocket)

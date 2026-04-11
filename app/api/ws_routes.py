from __future__ import annotations

import json
import time

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.api.deps import get_ws_container
from app.domain.enums import MatchStatus, PieceType
from app.engine.snapshot import build_match_snapshot

router = APIRouter(tags=["ws"])


@router.websocket("/matches/{match_id}/ws")
@router.websocket("/ws/matches/{match_id}")
async def ws_match(websocket: WebSocket, match_id: str, container=Depends(get_ws_container)):
    state = container.repo.get_match(match_id)
    if state is None:
        await websocket.accept()
        await websocket.send_json({"type": "error", "data": {"message": "match not found", "match_id": match_id}})
        await websocket.close(code=1008)
        return

    await container.broadcaster.connect(match_id, websocket)
    now_ms = int(time.time() * 1000)
    snap = build_match_snapshot(state, now_ms)
    await websocket.send_json(
        {
            "type": "subscribed",
            "data": {
                "match_id": match_id,
                "status": snap["match_meta"]["status"],
                "phase": snap["phase"]["name"],
                "version": snap["match_meta"]["version"],
                "started_at": snap["match_meta"]["started_at"],
                "winner": snap["match_meta"]["winner"],
                "reason": snap["match_meta"]["reason"],
                "version_semantics": "event_version",
            },
        }
    )
    await websocket.send_json({"type": "snapshot", "data": snap})

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            t = data.get("type")
            now = int(time.time() * 1000)

            if t == "ping":
                await websocket.send_json({"type": "pong", "data": {"ts_ms": now}})
                continue

            before_state = container.repo.get_match(match_id)
            before_events = len(before_state.event_log) if before_state else 0
            if t == "move":
                ok, msg = container.command_service.handle_move_command(
                    match_id,
                    data["player_id"],
                    data["piece_id"],
                    (int(data["target_x"]), int(data["target_y"])),
                    now,
                )
            elif t == "unlock":
                ok, msg = container.command_service.handle_unlock_command(
                    match_id,
                    data["player_id"],
                    PieceType(data["kind"]),
                    now,
                )
            elif t == "resign":
                ok, msg = container.command_service.handle_resign_command(match_id, data["player_id"], now)
            else:
                ok, msg = False, "unsupported"

            latest = container.repo.get_match(match_id)
            delta_events = latest.event_log[before_events:] if latest is not None else []
            await websocket.send_json({"type": "command_result", "data": {"ok": ok, "message": msg}})
            await websocket.send_json(
                {
                    "type": "events",
                    "data": {
                        "events": [{"type": e.event_type, "ts_ms": e.ts_ms, "payload": e.payload} for e in delta_events],
                        "note": "snapshot is broadcast by tick loop; clients should treat command events and broadcast frames as eventually consistent.",
                    },
                }
            )

            if latest is not None and latest.status == MatchStatus.ENDED:
                await websocket.send_json({"type": "event", "data": {"type": "match_ended", "ts_ms": now, "payload": {"match_id": match_id}}})
    except WebSocketDisconnect:
        await container.broadcaster.disconnect(match_id, websocket)

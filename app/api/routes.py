from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from app.api.schemas import MoveRequest, ResignRequest, UnlockRequest
from app.engine.manager import GameManager, MatchRuntime


router = APIRouter()


def get_manager() -> GameManager:
    from app.main import manager

    return manager


def get_runtime(match_id: str, manager: GameManager = Depends(get_manager)) -> MatchRuntime:
    runtime = manager.get_match(match_id)
    if runtime is None:
        raise HTTPException(status_code=404, detail="match not found")
    return runtime


@router.post("/matches")
async def create_match(manager: GameManager = Depends(get_manager)) -> dict[str, str]:
    runtime = await manager.create_match()
    return {"match_id": runtime.game.state.match_id}


@router.get("/matches/{match_id}")
async def get_match_state(runtime: MatchRuntime = Depends(get_runtime)) -> dict[str, object]:
    return runtime.game.enriched_snapshot()


@router.post("/matches/{match_id}/move")
async def move_piece(payload: MoveRequest, runtime: MatchRuntime = Depends(get_runtime)) -> dict[str, object]:
    async with runtime.lock:
        result = runtime.game.command_move(
            player=payload.player,
            piece_id=payload.piece_id,
            target_x=payload.target_x,
            target_y=payload.target_y,
        )
        snapshot = runtime.game.enriched_snapshot()
    return {"ok": result.ok, "message": result.message, "snapshot": snapshot}


@router.post("/matches/{match_id}/unlock")
async def choose_unlock(payload: UnlockRequest, runtime: MatchRuntime = Depends(get_runtime)) -> dict[str, object]:
    async with runtime.lock:
        result = runtime.game.command_unlock(player=payload.player, piece_type=payload.piece_type)
        snapshot = runtime.game.enriched_snapshot()
    return {"ok": result.ok, "message": result.message, "snapshot": snapshot}


@router.post("/matches/{match_id}/resign")
async def resign(payload: ResignRequest, runtime: MatchRuntime = Depends(get_runtime)) -> dict[str, object]:
    async with runtime.lock:
        result = runtime.game.command_resign(player=payload.player)
        snapshot = runtime.game.enriched_snapshot()
    return {"ok": result.ok, "message": result.message, "snapshot": snapshot}


@router.websocket("/matches/{match_id}/ws")
async def match_websocket(websocket: WebSocket, match_id: str, manager: GameManager = Depends(get_manager)) -> None:
    runtime = await manager.connect_socket(match_id, websocket)
    if runtime is None:
        await websocket.close(code=4404)
        return
    try:
        while True:
            raw = await websocket.receive_text()
            payload = json.loads(raw)
            result = await manager.handle_ws_command(runtime, payload)
            await websocket.send_json({"type": "command_result", "data": result})
    except WebSocketDisconnect:
        await manager.disconnect_socket(runtime, websocket)


@router.get("/demo", response_class=HTMLResponse)
async def demo_page() -> str:
    from pathlib import Path

    html_path = Path(__file__).resolve().parents[1] / "static" / "index.html"
    return html_path.read_text(encoding="utf-8")

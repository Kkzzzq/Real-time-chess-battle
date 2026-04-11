from __future__ import annotations

import time

from fastapi import APIRouter, Depends, HTTPException

from app.api.auth import require_player_auth
from app.api.deps import get_container
from app.api.schemas import CommandResultResponse, MoveCommandRequest, ResignRequest, UnlockCommandRequest
from app.engine.snapshot import build_match_snapshot

router = APIRouter(prefix="/matches/{match_id}/commands", tags=["commands"])


def _state_or_404(container, match_id: str):
    state = container.repo.get_match(match_id)
    if state is None:
        raise HTTPException(status_code=404, detail="match not found")
    return state


def _snapshot_or_404(container, match_id: str, now_ms: int, player_id: str | None = None) -> dict:
    state = _state_or_404(container, match_id)
    viewer_seat = None
    if player_id is not None:
        for seat, info in state.players.items():
            if info.get("player_id") == player_id:
                viewer_seat = seat
                break
    return build_match_snapshot(state, now_ms, viewer_seat=viewer_seat)


def _raise_for_command_error(msg: str) -> None:
    if msg == "match not found":
        raise HTTPException(status_code=404, detail=msg)
    if msg in {"player not found", "piece not found"}:
        raise HTTPException(status_code=404, detail=msg)
    if msg in {"not your piece", "player offline"}:
        raise HTTPException(status_code=403, detail=msg)
    if msg in {"match already ended", "match not running"}:
        raise HTTPException(status_code=409, detail=msg)
    raise HTTPException(status_code=400, detail=msg)


@router.post("/move", response_model=CommandResultResponse)
def move(match_id: str, payload: MoveCommandRequest, container=Depends(get_container)):
    now_ms = int(time.time() * 1000)
    state = _state_or_404(container, match_id)
    require_player_auth(state, payload.player_id, payload.player_token)
    ok, msg = container.command_service.handle_move_command(
        match_id,
        payload.player_id,
        payload.piece_id,
        (payload.target_x, payload.target_y),
        now_ms,
    )
    if not ok:
        _raise_for_command_error(msg)
    return {"ok": ok, "message": msg, "snapshot": _snapshot_or_404(container, match_id, now_ms, payload.player_id)}


@router.post("/unlock", response_model=CommandResultResponse)
def unlock(match_id: str, payload: UnlockCommandRequest, container=Depends(get_container)):
    now_ms = int(time.time() * 1000)
    state = _state_or_404(container, match_id)
    require_player_auth(state, payload.player_id, payload.player_token)
    ok, msg = container.command_service.handle_unlock_command(match_id, payload.player_id, payload.kind, now_ms)
    if not ok:
        _raise_for_command_error(msg)
    return {"ok": ok, "message": msg, "snapshot": _snapshot_or_404(container, match_id, now_ms, payload.player_id)}


@router.post("/resign", response_model=CommandResultResponse)
def resign(match_id: str, payload: ResignRequest, container=Depends(get_container)):
    now_ms = int(time.time() * 1000)
    state = _state_or_404(container, match_id)
    require_player_auth(state, payload.player_id, payload.player_token)
    ok, msg = container.command_service.handle_resign_command(match_id, payload.player_id, now_ms)
    if not ok:
        _raise_for_command_error(msg)
    return {"ok": ok, "message": msg, "snapshot": _snapshot_or_404(container, match_id, now_ms, payload.player_id)}

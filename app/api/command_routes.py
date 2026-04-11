from __future__ import annotations

import time

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_container
from app.api.schemas import CommandResultResponse, MoveCommandRequest, ResignRequest, UnlockCommandRequest
from app.engine.snapshot import build_match_snapshot

router = APIRouter(prefix="/matches/{match_id}/commands", tags=["commands"])


def _snapshot_or_404(container, match_id: str, now_ms: int) -> dict:
    state = container.repo.get_match(match_id)
    if state is None:
        raise HTTPException(status_code=404, detail="match not found")
    return build_match_snapshot(state, now_ms)


def _reconcile(container, match_id: str, now_ms: int) -> None:
    container.match_service.tick_once(match_id, now_ms)


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
    _reconcile(container, match_id, now_ms)
    ok, msg = container.command_service.handle_move_command(
        match_id,
        payload.player_id,
        payload.piece_id,
        (payload.target_x, payload.target_y),
        now_ms,
    )
    _reconcile(container, match_id, now_ms)
    if not ok:
        _raise_for_command_error(msg)
    return {"ok": ok, "message": msg, "snapshot": _snapshot_or_404(container, match_id, now_ms)}


@router.post("/unlock", response_model=CommandResultResponse)
def unlock(match_id: str, payload: UnlockCommandRequest, container=Depends(get_container)):
    now_ms = int(time.time() * 1000)
    _reconcile(container, match_id, now_ms)
    ok, msg = container.command_service.handle_unlock_command(match_id, payload.player_id, payload.kind, now_ms)
    _reconcile(container, match_id, now_ms)
    if not ok:
        _raise_for_command_error(msg)
    return {"ok": ok, "message": msg, "snapshot": _snapshot_or_404(container, match_id, now_ms)}


@router.post("/resign", response_model=CommandResultResponse)
def resign(match_id: str, payload: ResignRequest, container=Depends(get_container)):
    now_ms = int(time.time() * 1000)
    _reconcile(container, match_id, now_ms)
    ok, msg = container.command_service.handle_resign_command(match_id, payload.player_id, now_ms)
    _reconcile(container, match_id, now_ms)
    if not ok:
        _raise_for_command_error(msg)
    return {"ok": ok, "message": msg, "snapshot": _snapshot_or_404(container, match_id, now_ms)}

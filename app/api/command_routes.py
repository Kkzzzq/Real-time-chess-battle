from __future__ import annotations

import time

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_container
from app.api.schemas import MoveCommandRequest, ResignRequest, UnlockCommandRequest
from app.engine.snapshot import build_match_snapshot

router = APIRouter(prefix="/matches/{match_id}/commands", tags=["commands"])


def _snapshot_or_404(container, match_id: str, now_ms: int) -> dict:
    state = container.repo.get_match(match_id)
    if state is None:
        raise HTTPException(status_code=404, detail="match not found")
    return build_match_snapshot(state, now_ms)


@router.post("/move")
def move(match_id: str, payload: MoveCommandRequest, container=Depends(get_container)):
    now_ms = int(time.time() * 1000)
    ok, msg = container.command_service.handle_move_command(
        match_id,
        payload.player,
        payload.piece_id,
        (payload.target_x, payload.target_y),
        now_ms,
    )
    return {"ok": ok, "message": msg, "snapshot": _snapshot_or_404(container, match_id, now_ms)}


@router.post("/unlock")
def unlock(match_id: str, payload: UnlockCommandRequest, container=Depends(get_container)):
    now_ms = int(time.time() * 1000)
    ok, msg = container.command_service.handle_unlock_command(match_id, payload.player, payload.kind, now_ms)
    return {"ok": ok, "message": msg, "snapshot": _snapshot_or_404(container, match_id, now_ms)}


@router.post("/resign")
def resign(match_id: str, payload: ResignRequest, container=Depends(get_container)):
    now_ms = int(time.time() * 1000)
    ok, msg = container.command_service.handle_resign_command(match_id, payload.player, now_ms)
    return {"ok": ok, "message": msg, "snapshot": _snapshot_or_404(container, match_id, now_ms)}

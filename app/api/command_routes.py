from __future__ import annotations

import time

from fastapi import APIRouter, Depends

from app.api.deps import get_container
from app.api.schemas import MoveCommandRequest, ResignRequest, UnlockCommandRequest

router = APIRouter(prefix="/matches/{match_id}/commands", tags=["commands"])


@router.post("/move")
def move(match_id: str, payload: MoveCommandRequest, container=Depends(get_container)):
    ok, msg = container.command_service.handle_move_command(match_id, payload.player, payload.piece_id, (payload.target_x, payload.target_y), int(time.time() * 1000))
    return {"ok": ok, "message": msg}


@router.post("/unlock")
def unlock(match_id: str, payload: UnlockCommandRequest, container=Depends(get_container)):
    ok, msg = container.command_service.handle_unlock_command(match_id, payload.player, payload.kind, int(time.time() * 1000))
    return {"ok": ok, "message": msg}


@router.post("/resign")
def resign(match_id: str, payload: ResignRequest, container=Depends(get_container)):
    ok, msg = container.command_service.handle_resign_command(match_id, payload.player, int(time.time() * 1000))
    return {"ok": ok, "message": msg}

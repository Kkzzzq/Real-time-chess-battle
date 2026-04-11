from __future__ import annotations

import time

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_container
from app.api.schemas import JoinMatchRequest, LeaveMatchRequest, ReadyMatchRequest
from app.engine.snapshot import build_match_snapshot

router = APIRouter(prefix="/matches", tags=["matches"])


@router.post("")
def create_match(container=Depends(get_container)):
    state = container.room_service.create_match()
    return {"match_id": state.match_id, "status": state.status.value}


@router.get("")
def list_matches(container=Depends(get_container)):
    return [
        {"match_id": s.match_id, "status": s.status.value, "players": s.players}
        for s in container.repo.list_matches()
    ]


@router.post("/{match_id}/join")
def join_match(match_id: str, payload: JoinMatchRequest, container=Depends(get_container)):
    try:
        player = container.room_service.join_match(match_id, payload.player_name)
        state = container.repo.get_match(match_id)
        return {"player": player, "status": state.status.value if state else "deleted"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{match_id}/ready")
def ready_match(match_id: str, payload: ReadyMatchRequest, container=Depends(get_container)):
    try:
        state = container.room_service.ready_match(match_id, payload.player_id)
        return {"ok": True, "status": state.status.value, "players": state.players}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{match_id}/start")
async def start_match(match_id: str, container=Depends(get_container)):
    try:
        state = container.room_service.start_match(match_id)
        await container.tick_loop.ensure_match_loop(match_id)
        now_ms = int(time.time() * 1000)
        container.match_service.tick_once(match_id, now_ms)
        return {
            "ok": True,
            "status": state.status.value,
            "started_at": state.started_at,
            "snapshot": build_match_snapshot(state, now_ms),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{match_id}/leave")
def leave_match(match_id: str, payload: LeaveMatchRequest, container=Depends(get_container)):
    try:
        state = container.room_service.leave_match(match_id, payload.player_id)
        if container.repo.get_match(match_id) is None:
            container.tick_loop.stop_match_loop(match_id)
            return {"ok": True, "status": "deleted"}
        return {"ok": True, "status": state.status.value, "players": state.players}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

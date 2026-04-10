from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_container
from app.api.schemas import JoinMatchRequest, LeaveMatchRequest, ReadyMatchRequest

router = APIRouter(prefix="/matches", tags=["matches"])


@router.post("")
def create_match(container=Depends(get_container)):
    return {"match_id": container.room_service.create_match().match_id}


@router.get("")
def list_matches(container=Depends(get_container)):
    return [{"match_id": s.match_id, "status": s.status.value} for s in container.repo.list_matches()]


@router.post("/{match_id}/join")
def join_match(match_id: str, payload: JoinMatchRequest, container=Depends(get_container)):
    try:
        return container.room_service.join_match(match_id, payload.player_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{match_id}/ready")
def ready_match(match_id: str, payload: ReadyMatchRequest, container=Depends(get_container)):
    container.room_service.ready_match(match_id, payload.player_id)
    return {"ok": True}


@router.post("/{match_id}/start")
def start_match(match_id: str, container=Depends(get_container)):
    try:
        state = container.room_service.start_match(match_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    container.tick_loop.start_match_loop(match_id)
    return {"ok": True, "status": state.status.value}


@router.post("/{match_id}/leave")
def leave_match(match_id: str, payload: LeaveMatchRequest, container=Depends(get_container)):
    container.room_service.leave_match(match_id, payload.player_id)
    return {"ok": True}

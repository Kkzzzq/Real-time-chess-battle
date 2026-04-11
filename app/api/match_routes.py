from __future__ import annotations

import time

from fastapi import APIRouter, Depends, HTTPException

from app.api.auth import require_player_auth
from app.api.deps import get_container
from app.api.schemas import (
    CreateMatchRequest,
    JoinMatchRequest,
    JoinMatchResponse,
    LeaveMatchRequest,
    MatchCreatedResponse,
    MatchStatusResponse,
    ReadyMatchRequest,
    ReconnectMatchRequest,
    ReconnectMatchResponse,
    StartMatchRequest,
    StartMatchResponse,
)
from app.engine.snapshot import build_match_snapshot

router = APIRouter(prefix="/matches", tags=["matches"])


def _public_players(state) -> dict[str, dict]:
    players = {}
    for seat, info in state.players.items():
        players[str(seat)] = {
            "seat": seat,
            "player_id": info.get("player_id"),
            "name": info.get("name"),
            "ready": bool(info.get("ready", False)),
            "online": bool(info.get("online", False)),
            "is_host": state.host_seat == seat,
        }
    return players


@router.post("", response_model=MatchCreatedResponse)
def create_match(payload: CreateMatchRequest | None = None, container=Depends(get_container)):
    payload = payload or CreateMatchRequest()
    try:
        state = container.room_service.create_match(
            ruleset_name=payload.ruleset_name,
            allow_draw=payload.allow_draw,
            tick_ms=payload.tick_ms,
            custom_unlock_windows=payload.custom_unlock_windows,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "match_id": state.match_id,
        "status": state.status.value,
        "ruleset": {
            "ruleset_name": state.ruleset_name,
            "allow_draw": state.allow_draw,
            "tick_ms": state.tick_ms,
            "custom_unlock_windows": state.custom_unlock_windows,
        },
    }


@router.get("")
def list_matches(container=Depends(get_container)):
    return [
        {"match_id": s.match_id, "status": s.status.value, "players": _public_players(s)}
        for s in container.repo.list_matches()
    ]


@router.post("/{match_id}/join", response_model=JoinMatchResponse)
def join_match(match_id: str, payload: JoinMatchRequest, container=Depends(get_container)):
    try:
        player = container.room_service.join_match(match_id, payload.player_name)
        state = container.repo.get_match(match_id)
        return {"player": player, "status": state.status.value if state else "deleted"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{match_id}/reconnect", response_model=ReconnectMatchResponse)
def reconnect_match(match_id: str, payload: ReconnectMatchRequest, container=Depends(get_container)):
    try:
        player = container.room_service.reconnect_match(match_id, payload.player_id, payload.player_token)
        state = container.repo.get_match(match_id)
        return {"player": player, "status": state.status.value if state else "deleted"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{match_id}/ready", response_model=MatchStatusResponse)
def ready_match(match_id: str, payload: ReadyMatchRequest, container=Depends(get_container)):
    try:
        state = container.repo.get_match(match_id)
        if state is None:
            raise ValueError("match not found")
        require_player_auth(state, payload.player_id, payload.player_token)
        state = container.room_service.ready_match(match_id, payload.player_id)
        return {"ok": True, "status": state.status.value, "players": _public_players(state)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{match_id}/start", response_model=StartMatchResponse)
async def start_match(match_id: str, payload: StartMatchRequest, container=Depends(get_container)):
    try:
        state = container.repo.get_match(match_id)
        if state is None:
            raise ValueError("match not found")
        require_player_auth(state, payload.player_id, payload.player_token)
        state = container.room_service.start_match(match_id, payload.player_id)
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


@router.post("/{match_id}/leave", response_model=MatchStatusResponse)
def leave_match(match_id: str, payload: LeaveMatchRequest, container=Depends(get_container)):
    try:
        state = container.repo.get_match(match_id)
        if state is None:
            raise ValueError("match not found")
        require_player_auth(state, payload.player_id, payload.player_token)
        state = container.room_service.leave_match(match_id, payload.player_id)
        if container.repo.get_match(match_id) is None:
            container.tick_loop.stop_match_loop(match_id)
            return {"ok": True, "status": "deleted"}
        return {"ok": True, "status": state.status.value, "players": _public_players(state)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

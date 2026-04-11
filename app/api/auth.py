from __future__ import annotations

from fastapi import HTTPException


def resolve_viewer_seat_with_auth(state, player_id: str | None, player_token: str | None) -> int | None:
    if player_id is None:
        return None
    if not player_token:
        raise HTTPException(status_code=401, detail="player_token required")
    for seat, info in state.players.items():
        if info.get("player_id") == player_id:
            if info.get("player_token") != player_token:
                raise HTTPException(status_code=403, detail="invalid player token")
            return seat
    raise HTTPException(status_code=404, detail="player not found")


def require_player_auth(state, player_id: str, player_token: str) -> int:
    seat = resolve_viewer_seat_with_auth(state, player_id, player_token)
    if seat is None:
        raise HTTPException(status_code=401, detail="player_id required")
    return seat

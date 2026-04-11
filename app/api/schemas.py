from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from app.domain.enums import PieceType


class JoinMatchRequest(BaseModel):
    player_name: str


class ReadyMatchRequest(BaseModel):
    player_id: str


class LeaveMatchRequest(BaseModel):
    player_id: str


class MoveCommandRequest(BaseModel):
    player_id: str
    piece_id: str
    target_x: int
    target_y: int


class UnlockCommandRequest(BaseModel):
    player_id: str
    kind: PieceType


class ResignRequest(BaseModel):
    player_id: str


class CommandResultResponse(BaseModel):
    ok: bool
    message: str
    snapshot: dict[str, Any]


class PlayerJoinResponse(BaseModel):
    seat: int
    player_id: str
    name: str
    ready: bool
    online: bool
    is_host: bool


class JoinMatchResponse(BaseModel):
    player: PlayerJoinResponse
    status: str


class MatchStatusResponse(BaseModel):
    ok: bool
    status: str
    players: dict[int, dict[str, Any]] | None = None


class StartMatchResponse(BaseModel):
    ok: bool
    status: str
    started_at: int
    snapshot: dict[str, Any]


class MatchCreatedResponse(BaseModel):
    match_id: str
    status: str


class MatchSnapshotResponse(BaseModel):
    match_meta: dict[str, Any]
    players: dict[int, dict[str, Any]]
    phase: dict[str, Any]
    unlock: dict[str, Any]
    board: dict[str, Any]
    runtime_board: dict[str, Any]
    pieces: list[dict[str, Any]]
    events: list[dict[str, Any]]
    command_log: list[dict[str, Any]]

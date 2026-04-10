from __future__ import annotations

from pydantic import BaseModel

from app.domain.enums import PieceType


class CreateMatchRequest(BaseModel):
    pass


class JoinMatchRequest(BaseModel):
    player_name: str


class ReadyMatchRequest(BaseModel):
    player_id: str


class LeaveMatchRequest(BaseModel):
    player_id: str


class MoveCommandRequest(BaseModel):
    player: int
    piece_id: str
    target_x: int
    target_y: int


class UnlockCommandRequest(BaseModel):
    player: int
    kind: PieceType


class ResignRequest(BaseModel):
    player: int


class MatchSnapshotResponse(BaseModel):
    match_id: str
    status: str

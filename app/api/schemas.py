from __future__ import annotations

from pydantic import BaseModel, Field

from app.domain.enums import PieceType


class MoveRequest(BaseModel):
    type: str = "move"
    player: int = Field(ge=1, le=2)
    piece_id: str
    target_x: int = Field(ge=0, le=8)
    target_y: int = Field(ge=0, le=9)


class UnlockRequest(BaseModel):
    type: str = "unlock"
    player: int = Field(ge=1, le=2)
    piece_type: PieceType


class ResignRequest(BaseModel):
    type: str = "resign"
    player: int = Field(ge=1, le=2)

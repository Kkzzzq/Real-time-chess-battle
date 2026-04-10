from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.domain.enums import PieceType


@dataclass
class Piece:
    piece_id: str
    player: int
    piece_type: PieceType
    x: int
    y: int
    alive: bool = True
    moving: bool = False
    move_start_at: float | None = None
    move_end_at: float | None = None
    move_start_pos: tuple[int, int] | None = None
    target: tuple[int, int] | None = None
    cooldown_until: float = 0.0


@dataclass
class UnlockState:
    unlocked: set[PieceType] = field(default_factory=lambda: {PieceType.SOLDIER})
    selected_waves: set[int] = field(default_factory=set)


@dataclass
class MatchState:
    match_id: str
    started_at: float
    pieces: dict[str, Piece]
    unlocks: dict[int, UnlockState]
    winner: int | None = None
    draw: bool = False
    draw_reason: str | None = None
    resigned_player: int | None = None
    ended_at: float | None = None
    last_action_at: float | None = None
    last_capture_at: float | None = None
    tick_index: int = 0

    def to_dict(self, now: float) -> dict[str, Any]:
        return {
            "match_id": self.match_id,
            "started_at": self.started_at,
            "elapsed": round(max(0.0, now - self.started_at), 3),
            "winner": self.winner,
            "draw": self.draw,
            "draw_reason": self.draw_reason,
            "resigned_player": self.resigned_player,
            "pieces": [
                {
                    "piece_id": p.piece_id,
                    "player": p.player,
                    "piece_type": p.piece_type.value,
                    "x": p.x,
                    "y": p.y,
                    "alive": p.alive,
                    "moving": p.moving,
                    "target": p.target,
                    "cooldown_until": p.cooldown_until,
                }
                for p in self.pieces.values()
            ],
            "unlocks": {
                player: sorted([pt.value for pt in unlock.unlocked])
                for player, unlock in self.unlocks.items()
            },
        }


@dataclass
class MovePath:
    duration: float
    segments: list[tuple[int, int]]


@dataclass
class RuleResult:
    ok: bool
    message: str
    movement: MovePath | None = None


@dataclass
class CommandResult:
    ok: bool
    message: str

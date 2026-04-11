from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.domain.enums import MatchStatus, PieceType
from app.domain.events import GameEvent


@dataclass
class Piece:
    id: str
    owner: int
    kind: PieceType
    x: int
    y: int
    alive: bool = True
    is_moving: bool = False
    move_start_at: int | None = None
    move_end_at: int | None = None
    move_total_ms: int = 0
    path_points: list[tuple[int, int]] = field(default_factory=list)
    start_x: int = 0
    start_y: int = 0
    target_x: int = 0
    target_y: int = 0
    cooldown_end_at: int = 0
    last_command_at: int = 0
    spawn_index: int = 0
    captured_at: int | None = None
    death_reason: str | None = None
    current_segment_index: int = -1
    last_resolved_at: int | None = None


@dataclass
class MatchState:
    match_id: str
    status: MatchStatus = MatchStatus.WAITING
    winner: int | None = None
    reason: str | None = None
    created_at: int = 0
    started_at: int | None = None
    now_ms: int = 0
    phase_name: str = "waiting"
    phase_deadline_ms: int | None = None
    wave_index: int = -1
    pieces: dict[str, Piece] = field(default_factory=dict)
    unlocked_by_player: dict[int, set[PieceType]] = field(default_factory=dict)
    pending_unlock_choice: dict[int, dict[int, PieceType]] = field(default_factory=dict)
    auto_unlock_processed_waves: dict[int, set[int]] = field(default_factory=dict)
    players: dict[int, dict[str, Any]] = field(default_factory=dict)
    host_seat: int | None = None
    creator_player_id: str | None = None
    event_log: list[GameEvent] = field(default_factory=list)
    command_log: list[dict[str, Any]] = field(default_factory=list)
    last_action_at: int | None = None
    last_capture_at: int | None = None
    version: int = 0
    ruleset_name: str = "standard"
    allow_draw: bool = True
    tick_ms: int = 100
    custom_unlock_windows: list[int] | None = None

    def add_event(self, event: GameEvent) -> None:
        self.event_log.append(event)
        self.event_log = self.event_log[-200:]
        self.version += 1

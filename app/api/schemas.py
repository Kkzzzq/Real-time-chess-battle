from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from app.domain.enums import PieceType


class CreateMatchRequest(BaseModel):
    ruleset_name: str = "standard"
    allow_draw: bool = True
    tick_ms: int = Field(default=100, ge=20, le=1000)
    custom_unlock_windows: list[int] | None = None


class JoinMatchRequest(BaseModel):
    player_name: str


class ReadyMatchRequest(BaseModel):
    player_id: str
    player_token: str


class StartMatchRequest(BaseModel):
    player_id: str
    player_token: str


class LeaveMatchRequest(BaseModel):
    player_id: str
    player_token: str


class MoveCommandRequest(BaseModel):
    player_id: str
    player_token: str
    piece_id: str
    target_x: int
    target_y: int


class UnlockCommandRequest(BaseModel):
    player_id: str
    player_token: str
    kind: PieceType


class ResignRequest(BaseModel):
    player_id: str
    player_token: str


class MatchMetaSchema(BaseModel):
    match_id: str
    status: str
    winner: int | None
    reason: str | None
    created_at: int
    started_at: int | None
    now_ms: int
    version: int
    ruleset: dict[str, Any]


class PlayerSchema(BaseModel):
    seat: int
    player_id: str
    player_token: str | None = None
    name: str
    ready: bool
    online: bool
    is_host: bool


class PhaseSchema(BaseModel):
    name: str
    deadline_ms: int | None
    remaining_ms: int | None
    wave_index: int
    next_phase_name: str | None
    next_phase_start_ms: int | None
    next_wave_index: int | None
    next_wave_start_ms: int | None
    current_wave_start_ms: int | None
    current_wave_deadline_ms: int | None


class UnlockPlayerSchema(BaseModel):
    unlocked: list[str]
    available_options: list[str]
    wave_choice: str | None
    has_chosen: bool
    auto_selected: bool
    can_choose_now: bool
    waiting_for_timeout: bool
    choice_source: Literal["manual", "auto", "none"]


class UnlockSchema(BaseModel):
    phase: str
    fully_unlocked: bool
    window_open: bool
    current_wave: int
    wave_start_ms: int | None
    wave_deadline_ms: int | None
    current_wave_remaining_ms: int | None
    wave_timeout: bool
    wave_options: list[str]
    next_wave_index: int | None
    next_wave_start_ms: int | None
    players: dict[str, UnlockPlayerSchema]


class BoardOccupantSchema(BaseModel):
    piece_id: str
    owner: int
    kind: str
    moving: bool


class BoardCellSchema(BaseModel):
    occupants: list[BoardOccupantSchema]
    primary_occupant: BoardOccupantSchema | None


class BoardStatsSchema(BaseModel):
    alive_total: int
    alive_by_player: dict[str, int]


class BoardSchema(BaseModel):
    mode: Literal["logical", "runtime"]
    cells: list[list[BoardCellSchema]]
    stats: BoardStatsSchema


class PieceSegmentSchema(BaseModel):
    index: int
    start: tuple[int, int]
    end: tuple[int, int]
    local_progress: float


class PieceCommandabilitySchema(BaseModel):
    owner_can_command: bool
    owner_disabled_reason: str | None
    viewer_can_command: bool | None = None
    viewer_disabled_reason: str | None = None
    note: str


class PieceSchema(BaseModel):
    id: str
    owner: int
    kind: str
    x: int
    y: int
    display_x: float
    display_y: float
    alive: bool
    is_moving: bool
    target_x: int
    target_y: int
    path: list[tuple[int, int]]
    move_start_at: int | None
    move_end_at: int | None
    move_remaining_ms: int
    cooldown_remaining_ms: int
    can_command: bool
    disabled_reason: str | None
    can_command_scope: str
    commandability: PieceCommandabilitySchema
    runtime_cells: list[tuple[int, int]]
    segment: PieceSegmentSchema
    captured_at: int | None
    death_reason: str | None


class EventSchema(BaseModel):
    type: str
    ts_ms: int
    payload: dict[str, Any]


class CommandLogSchema(BaseModel):
    type: str
    ts: int
    player_id: str
    player: int | None = None
    piece_id: str | None = None
    target: tuple[int, int] | None = None
    kind: str | None = None


class MatchSnapshotResponse(BaseModel):
    match_meta: MatchMetaSchema
    players: dict[str, PlayerSchema]
    phase: PhaseSchema
    unlock: UnlockSchema
    board: BoardSchema
    runtime_board: BoardSchema
    pieces: list[PieceSchema]
    events: list[EventSchema]
    command_log: list[CommandLogSchema]


class LegalMovesStaticSchema(BaseModel):
    targets: list[tuple[int, int]]


class LegalMovesActionableSchema(BaseModel):
    viewer_seat: int | None
    actionable_targets: list[tuple[int, int]]
    executable: bool
    actionable_context: str
    reason: str | None


class LegalMovesResponse(BaseModel):
    piece_id: str
    owner: int
    player_id: str | None
    static: LegalMovesStaticSchema
    actionable: LegalMovesActionableSchema | None


class CommandResultResponse(BaseModel):
    ok: bool
    message: str
    snapshot: MatchSnapshotResponse


class PlayerJoinResponse(BaseModel):
    seat: int
    player_id: str
    player_token: str
    player_token_expires_at: int | None = None
    name: str
    ready: bool
    online: bool
    is_host: bool


class JoinMatchResponse(BaseModel):
    player: PlayerJoinResponse
    status: str




class ReconnectMatchRequest(BaseModel):
    player_id: str
    player_token: str


class ReconnectMatchResponse(BaseModel):
    player: PlayerJoinResponse
    status: str


class MatchStatusResponse(BaseModel):
    ok: bool
    status: str
    players: dict[str, PlayerSchema] | None = None


class StartMatchResponse(BaseModel):
    ok: bool
    status: str
    started_at: int
    snapshot: MatchSnapshotResponse


class MatchCreatedResponse(BaseModel):
    match_id: str
    status: str
    ruleset: dict[str, Any]

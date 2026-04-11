from __future__ import annotations

from app.core.constants import BOARD_COLS, BOARD_ROWS
from app.domain.enums import MatchStatus, PieceType
from app.domain.models import MatchState, Piece
from app.engine.occupancy import get_piece_runtime_cells
from app.engine.phase import (
    compute_phase,
    get_current_wave_deadline_ms,
    get_current_wave_index,
    get_current_wave_remaining_ms,
    get_current_wave_start_ms,
    get_latest_wave_index,
    get_wave_options,
    is_piece_kind_allowed_by_phase,
)
from app.engine.timeline import get_piece_display_position, get_piece_segment_state


def _piece_disabled_reason(state: MatchState, piece: Piece, now_ms: int) -> str | None:
    if state.status != MatchStatus.RUNNING:
        return "match_not_running"
    if not piece.alive:
        return "dead"
    if piece.kind not in state.unlocked_by_player.get(piece.owner, {PieceType.SOLDIER}):
        return "not_unlocked"
    if not is_piece_kind_allowed_by_phase(piece.owner, piece.kind, state, now_ms):
        return "locked_by_phase"
    if piece.is_moving:
        return "moving"
    if piece.cooldown_end_at > now_ms:
        return "cooldown"
    return None


def build_piece_snapshot(state: MatchState, piece: Piece, now_ms: int) -> dict:
    px, py = get_piece_display_position(piece, now_ms)
    remain_move = max(0, (piece.move_end_at or 0) - now_ms) if piece.is_moving else 0
    remain_cd = max(0, piece.cooldown_end_at - now_ms)
    seg = get_piece_segment_state(piece, now_ms)
    disabled_reason = _piece_disabled_reason(state, piece, now_ms)
    runtime_cells = sorted(list(get_piece_runtime_cells(piece, now_ms)))
    return {
        "id": piece.id,
        "owner": piece.owner,
        "kind": piece.kind.value,
        "x": piece.x,
        "y": piece.y,
        "display_x": round(px, 3),
        "display_y": round(py, 3),
        "alive": piece.alive,
        "is_moving": piece.is_moving,
        "target_x": piece.target_x,
        "target_y": piece.target_y,
        "path": list(piece.path_points),
        "move_start_at": piece.move_start_at,
        "move_end_at": piece.move_end_at,
        "move_remaining_ms": remain_move,
        "cooldown_remaining_ms": remain_cd,
        "can_command": disabled_reason is None,
        "disabled_reason": disabled_reason,
        "can_command_scope": "owner_view",
        "commandability": {
            "owner_can_command": disabled_reason is None,
            "owner_disabled_reason": disabled_reason,
            "note": "can_command is evaluated from piece owner's view; viewer permission must still check player identity.",
        },
        "runtime_cells": runtime_cells,
        "segment": {
            "index": seg["segment_index"],
            "start": seg["segment_start"],
            "end": seg["segment_end"],
            "local_progress": round(seg["local_progress"], 4),
        },
        "captured_at": piece.captured_at,
        "death_reason": piece.death_reason,
    }


def build_phase_snapshot(state: MatchState, now_ms: int) -> dict:
    name, deadline, wave = compute_phase(now_ms, state.started_at)
    next_phase_name = None
    next_phase_start_ms = None
    next_wave_index = None
    next_wave_start_ms = None
    if state.started_at is not None:
        if name == "waiting":
            next_phase_name, next_phase_start_ms = "sealed", state.started_at
        elif name == "sealed":
            next_phase_name, next_phase_start_ms = "soldier_only", state.started_at + 30_000
        elif name == "soldier_only":
            next_phase_name, next_phase_start_ms = "unlock_wave", state.started_at + 50_000
            next_wave_index, next_wave_start_ms = 0, state.started_at + 50_000
        elif name == "unlock_wave":
            if wave < 3:
                next_phase_name, next_phase_start_ms = "midgame", state.started_at + (50 + 20 * (wave + 1)) * 1000
                next_wave_index, next_wave_start_ms = wave + 1, state.started_at + [70_000, 90_000, 110_000][wave]
            else:
                next_phase_name, next_phase_start_ms = "midgame", state.started_at + 130_000
        elif name == "midgame":
            latest = get_latest_wave_index(now_ms, state.started_at)
            if latest < 3:
                next_wave_index = latest + 1
                next_wave_start_ms = state.started_at + [50_000, 70_000, 90_000, 110_000][next_wave_index]
            next_phase_name, next_phase_start_ms = "fully_unlocked", state.started_at + 130_000

    return {
        "name": name,
        "deadline_ms": deadline,
        "remaining_ms": None if deadline is None else max(0, deadline - now_ms),
        "wave_index": wave,
        "next_phase_name": next_phase_name,
        "next_phase_start_ms": next_phase_start_ms,
        "next_wave_index": next_wave_index,
        "next_wave_start_ms": next_wave_start_ms,
        "current_wave_start_ms": get_current_wave_start_ms(now_ms, state.started_at),
        "current_wave_deadline_ms": get_current_wave_deadline_ms(now_ms, state.started_at),
    }


def _player_unlock_options(state: MatchState, player: int, now_ms: int) -> list[str]:
    options = get_wave_options(now_ms, state.started_at)
    unlocked = state.unlocked_by_player.get(player, set())
    return sorted([k.value for k in options - unlocked])


def build_unlock_snapshot(state: MatchState, now_ms: int) -> dict:
    wave = get_current_wave_index(now_ms, state.started_at)
    phase_name = compute_phase(now_ms, state.started_at)[0]
    window_open = wave >= 0
    deadline = get_current_wave_deadline_ms(now_ms, state.started_at)

    players = {}
    for p in (1, 2):
        choice = state.pending_unlock_choice.get(p, {}).get(wave) if wave >= 0 else None
        players[str(p)] = {
            "unlocked": sorted([k.value for k in state.unlocked_by_player.get(p, set())]),
            "available_options": _player_unlock_options(state, p, now_ms),
            "wave_choice": choice.value if choice else None,
            "has_chosen": choice is not None,
            "auto_selected": wave >= 0 and wave in state.auto_unlock_processed_waves.get(p, set()),
            "can_choose_now": wave >= 0 and choice is None and state.status == MatchStatus.RUNNING,
            "waiting_for_timeout": wave >= 0 and choice is not None and state.status == MatchStatus.RUNNING,
            "choice_source": "none" if choice is None else ("auto" if wave in state.auto_unlock_processed_waves.get(p, set()) else "manual"),
        }

    return {
        "phase": phase_name,
        "fully_unlocked": state.started_at is not None and (now_ms - state.started_at) / 1000 >= 130,
        "window_open": window_open,
        "current_wave": wave,
        "wave_start_ms": get_current_wave_start_ms(now_ms, state.started_at),
        "wave_deadline_ms": deadline,
        "current_wave_remaining_ms": get_current_wave_remaining_ms(now_ms, state.started_at),
        "wave_timeout": deadline is not None and now_ms >= deadline,
        "wave_options": sorted([k.value for k in get_wave_options(now_ms, state.started_at)]),
        "next_wave_index": None if wave >= 3 else wave + 1,
        "next_wave_start_ms": None if state.started_at is None or wave >= 3 else state.started_at + [50_000, 70_000, 90_000, 110_000][wave + 1],
        "players": players,
    }


def build_recent_events(state: MatchState) -> list[dict]:
    return [{"type": e.event_type, "ts_ms": e.ts_ms, "payload": e.payload} for e in state.event_log[-20:]]


def build_board_snapshot(state: MatchState, now_ms: int, runtime: bool = False) -> dict:
    cells = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
    living = [p for p in state.pieces.values() if p.alive]
    for piece in living:
        target_cells = get_piece_runtime_cells(piece, now_ms) if runtime else {(piece.x, piece.y)}
        for cell_x, cell_y in target_cells:
            cells[cell_y][cell_x] = {
                "piece_id": piece.id,
                "owner": piece.owner,
                "kind": piece.kind.value,
                "moving": piece.is_moving,
            }
    return {
        "cells": cells,
        "mode": "runtime" if runtime else "logical",
        "stats": {
            "alive_total": len(living),
            "alive_by_player": {
                "1": len([p for p in living if p.owner == 1]),
                "2": len([p for p in living if p.owner == 2]),
            },
        },
    }


def build_match_snapshot(state: MatchState, now_ms: int) -> dict:
    return {
        "match_meta": {
            "match_id": state.match_id,
            "status": state.status.value,
            "winner": state.winner,
            "reason": state.reason,
            "created_at": state.created_at,
            "started_at": state.started_at,
            "now_ms": now_ms,
            "version": state.version,
        },
        "players": state.players,
        "phase": build_phase_snapshot(state, now_ms),
        "unlock": build_unlock_snapshot(state, now_ms),
        "board": build_board_snapshot(state, now_ms, runtime=False),
        "runtime_board": build_board_snapshot(state, now_ms, runtime=True),
        "pieces": [build_piece_snapshot(state, p, now_ms) for p in state.pieces.values()],
        "events": build_recent_events(state),
        "command_log": state.command_log[-50:],
    }

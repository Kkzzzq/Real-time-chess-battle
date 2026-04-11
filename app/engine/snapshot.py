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


def _viewer_commandability(state: MatchState, piece: Piece, now_ms: int, viewer_seat: int | None) -> tuple[bool | None, str | None]:
    if viewer_seat is None:
        return None, None
    if viewer_seat != piece.owner:
        return False, "not_piece_owner"
    disabled_reason = _piece_disabled_reason(state, piece, now_ms)
    return disabled_reason is None, disabled_reason


def build_piece_snapshot(state: MatchState, piece: Piece, now_ms: int, viewer_seat: int | None = None) -> dict:
    px, py = get_piece_display_position(piece, now_ms)
    remain_move = max(0, (piece.move_end_at or 0) - now_ms) if piece.is_moving else 0
    remain_cd = max(0, piece.cooldown_end_at - now_ms)
    seg = get_piece_segment_state(piece, now_ms)
    disabled_reason = _piece_disabled_reason(state, piece, now_ms)
    viewer_can_command, viewer_disabled_reason = _viewer_commandability(state, piece, now_ms, viewer_seat)
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
            "viewer_can_command": viewer_can_command,
            "viewer_disabled_reason": viewer_disabled_reason,
            "note": "can_command is owner_view; use commandability.viewer_* when a viewer/player_id is provided.",
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
    wave_seconds = state.custom_unlock_windows or [50, 70, 90, 110]
    name, deadline, wave = compute_phase(now_ms, state.started_at, state)
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
            first_wave_ms = wave_seconds[0] * 1000
            next_phase_name, next_phase_start_ms = "unlock_wave", state.started_at + first_wave_ms
            next_wave_index, next_wave_start_ms = 0, state.started_at + first_wave_ms
        elif name == "unlock_wave":
            if wave + 1 < len(wave_seconds):
                next_phase_name, next_phase_start_ms = "midgame", state.started_at + (wave_seconds[wave] + 20) * 1000
                next_wave_index = wave + 1
                next_wave_start_ms = state.started_at + wave_seconds[next_wave_index] * 1000
            else:
                next_phase_name, next_phase_start_ms = "midgame", state.started_at + 130_000
        elif name == "midgame":
            latest = get_latest_wave_index(now_ms, state.started_at, state)
            if latest + 1 < len(wave_seconds):
                next_wave_index = latest + 1
                next_wave_start_ms = state.started_at + wave_seconds[next_wave_index] * 1000
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
        "current_wave_start_ms": get_current_wave_start_ms(now_ms, state.started_at, state),
        "current_wave_deadline_ms": get_current_wave_deadline_ms(now_ms, state.started_at, state),
    }


def _player_unlock_options(state: MatchState, player: int, now_ms: int) -> list[str]:
    options = get_wave_options(now_ms, state.started_at, state)
    unlocked = state.unlocked_by_player.get(player, set())
    return sorted([k.value for k in options - unlocked])


def build_unlock_snapshot(state: MatchState, now_ms: int) -> dict:
    wave = get_current_wave_index(now_ms, state.started_at, state)
    phase_name = compute_phase(now_ms, state.started_at, state)[0]
    window_open = wave >= 0
    deadline = get_current_wave_deadline_ms(now_ms, state.started_at, state)

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
        "wave_start_ms": get_current_wave_start_ms(now_ms, state.started_at, state),
        "wave_deadline_ms": deadline,
        "current_wave_remaining_ms": get_current_wave_remaining_ms(now_ms, state.started_at, state),
        "wave_timeout": deadline is not None and now_ms >= deadline,
        "wave_options": sorted([k.value for k in get_wave_options(now_ms, state.started_at, state)]),
        "next_wave_index": None if wave + 1 >= len(state.custom_unlock_windows or [50, 70, 90, 110]) else wave + 1,
        "next_wave_start_ms": None if state.started_at is None or wave + 1 >= len(state.custom_unlock_windows or [50, 70, 90, 110]) else state.started_at + (state.custom_unlock_windows or [50, 70, 90, 110])[wave + 1] * 1000,
        "players": players,
    }


def build_recent_events(state: MatchState) -> list[dict]:
    return [{"type": e.event_type, "ts_ms": e.ts_ms, "payload": e.payload} for e in state.event_log[-20:]]


def _empty_cell() -> dict:
    return {"occupants": [], "primary_occupant": None}


def build_board_snapshot(state: MatchState, now_ms: int, runtime: bool = False) -> dict:
    cells = [[_empty_cell() for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
    living = [p for p in state.pieces.values() if p.alive]
    for piece in living:
        target_cells = get_piece_runtime_cells(piece, now_ms) if runtime else {(piece.x, piece.y)}
        occ = {
            "piece_id": piece.id,
            "owner": piece.owner,
            "kind": piece.kind.value,
            "moving": piece.is_moving,
        }
        for cell_x, cell_y in target_cells:
            cell = cells[cell_y][cell_x]
            cell["occupants"].append(occ)

    for row in cells:
        for cell in row:
            if cell["occupants"]:
                sorted_occ = sorted(cell["occupants"], key=lambda o: (not o["moving"], o["piece_id"]))
                cell["occupants"] = sorted_occ
                cell["primary_occupant"] = sorted_occ[0]

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


def _snapshot_players(state: MatchState) -> dict[str, dict]:
    players: dict[str, dict] = {}
    effective_host_player_id = state.host_player_id
    if effective_host_player_id is None and state.host_seat in state.players:
        effective_host_player_id = state.players[state.host_seat].get("player_id")
    for seat, info in state.players.items():
        player_id = info.get("player_id")
        players[str(seat)] = {
            "seat": seat,
            "player_id": player_id,
            "name": info.get("name"),
            "ready": bool(info.get("ready", False)),
            "online": bool(info.get("online", False)),
            "is_host": (state.host_seat == seat) or (effective_host_player_id is not None and player_id == effective_host_player_id),
        }
    return players


def build_match_snapshot(state: MatchState, now_ms: int, viewer_seat: int | None = None) -> dict:
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
            "ruleset": {
                "ruleset_name": state.ruleset_name,
                "allow_draw": state.allow_draw,
                "tick_ms": state.tick_ms,
                "custom_unlock_windows": state.custom_unlock_windows,
            },
        },
        "players": _snapshot_players(state),
        "phase": build_phase_snapshot(state, now_ms),
        "unlock": build_unlock_snapshot(state, now_ms),
        "board": build_board_snapshot(state, now_ms, runtime=False),
        "runtime_board": build_board_snapshot(state, now_ms, runtime=True),
        "pieces": [build_piece_snapshot(state, p, now_ms, viewer_seat=viewer_seat) for p in state.pieces.values()],
        "events": build_recent_events(state),
        "command_log": state.command_log[-50:],
    }

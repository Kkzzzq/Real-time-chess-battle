from __future__ import annotations

from app.domain.models import MatchState, Piece
from app.engine.occupancy import get_piece_runtime_cells
from app.engine.phase import (
    compute_phase,
    get_current_wave_index,
    get_current_wave_remaining_ms,
    get_wave_options,
)
from app.engine.timeline import get_piece_display_position, get_piece_segment_state


def _piece_disabled_reason(piece: Piece, now_ms: int) -> str | None:
    if not piece.alive:
        return "dead"
    if piece.is_moving:
        return "moving"
    if piece.cooldown_end_at > now_ms:
        return "cooldown"
    return None


def build_piece_snapshot(piece: Piece, now_ms: int) -> dict:
    px, py = get_piece_display_position(piece, now_ms)
    remain_move = max(0, (piece.move_end_at or 0) - now_ms) if piece.is_moving else 0
    remain_cd = max(0, piece.cooldown_end_at - now_ms)
    seg = get_piece_segment_state(piece, now_ms)
    disabled_reason = _piece_disabled_reason(piece, now_ms)
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
    return {
        "name": name,
        "deadline_ms": deadline,
        "remaining_ms": None if deadline is None else max(0, deadline - now_ms),
        "wave_index": wave,
    }


def build_unlock_snapshot(state: MatchState, now_ms: int) -> dict:
    wave = get_current_wave_index(now_ms, state.started_at)
    options = get_wave_options(now_ms, state.started_at)
    return {
        "fully_unlocked": state.started_at is not None and (now_ms - state.started_at) / 1000 >= 130,
        "current_wave": wave,
        "current_wave_remaining_ms": get_current_wave_remaining_ms(now_ms, state.started_at),
        "wave_options": sorted([k.value for k in options]),
        "players": {
            str(p): {
                "unlocked": sorted([k.value for k in state.unlocked_by_player.get(p, set())]),
                "wave_choice": None if wave < 0 else (state.pending_unlock_choice.get(p, {}).get(wave).value if state.pending_unlock_choice.get(p, {}).get(wave) else None),
            }
            for p in (1, 2)
        },
    }


def build_recent_events(state: MatchState) -> list[dict]:
    return [{"type": e.event_type, "ts_ms": e.ts_ms, "payload": e.payload} for e in state.event_log[-20:]]


def build_board_snapshot(state: MatchState, now_ms: int) -> dict:
    living = [p for p in state.pieces.values() if p.alive]
    return {
        "alive_total": len(living),
        "alive_by_player": {
            "1": len([p for p in living if p.owner == 1]),
            "2": len([p for p in living if p.owner == 2]),
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
        "board": build_board_snapshot(state, now_ms),
        "pieces": [build_piece_snapshot(p, now_ms) for p in state.pieces.values()],
        "events": build_recent_events(state),
        "command_log": state.command_log[-50:],
    }

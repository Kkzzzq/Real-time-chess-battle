from __future__ import annotations

from app.domain.models import MatchState, Piece
from app.engine.phase import compute_phase
from app.engine.timeline import get_piece_display_position


def build_piece_snapshot(piece: Piece, now_ms: int) -> dict:
    px, py = get_piece_display_position(piece, now_ms)
    remain_move = max(0, (piece.move_end_at or 0) - now_ms) if piece.is_moving else 0
    remain_cd = max(0, piece.cooldown_end_at - now_ms)
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
        "move_remaining_ms": remain_move,
        "cooldown_remaining_ms": remain_cd,
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
    return {
        str(p): sorted([k.value for k in state.unlocked_by_player.get(p, set())])
        for p in (1, 2)
    }


def build_recent_events(state: MatchState) -> list[dict]:
    return [{"type": e.event_type, "ts_ms": e.ts_ms, "payload": e.payload} for e in state.event_log[-20:]]


def build_match_snapshot(state: MatchState, now_ms: int) -> dict:
    return {
        "match_id": state.match_id,
        "status": state.status.value,
        "winner": state.winner,
        "reason": state.reason,
        "now_ms": now_ms,
        "phase": build_phase_snapshot(state, now_ms),
        "unlocked": build_unlock_snapshot(state, now_ms),
        "pieces": [build_piece_snapshot(p, now_ms) for p in state.pieces.values()],
        "events": build_recent_events(state),
        "version": state.version,
    }

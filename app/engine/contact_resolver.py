from __future__ import annotations

from app.domain.events import EVENT_CAPTURE, GameEvent
from app.domain.models import MatchState, Piece
from app.engine.occupancy import get_piece_runtime_cells
from app.engine.timeline import get_piece_segment_state, terminate_move


def _mark_dead(piece: Piece, now_ms: int, reason: str) -> None:
    piece.alive = False
    piece.captured_at = now_ms
    piece.death_reason = reason
    terminate_move(piece, now_ms)


def apply_capture(state: MatchState, winner: Piece | None, loser: Piece, now_ms: int, reason: str = "capture") -> None:
    if not loser.alive:
        return
    _mark_dead(loser, now_ms, reason)
    state.last_capture_at = now_ms
    payload = {"target": loser.id, "reason": reason}
    if winner is not None:
        payload["by"] = winner.id
    state.add_event(GameEvent(EVENT_CAPTURE, now_ms, payload))


def _moving_pieces(state: MatchState) -> list[Piece]:
    return [p for p in state.pieces.values() if p.alive and p.is_moving]


def _moving_vs_static_contacts(state: MatchState, now_ms: int) -> list[tuple[Piece, Piece]]:
    pairs: list[tuple[Piece, Piece]] = []
    for mover in _moving_pieces(state):
        runtime_cells = get_piece_runtime_cells(mover, now_ms)
        for static in state.pieces.values():
            if not static.alive or static.is_moving or static.owner == mover.owner:
                continue
            if (static.x, static.y) in runtime_cells:
                pairs.append((mover, static))
    return pairs


def _is_head_on(a: Piece, b: Piece, now_ms: int) -> bool:
    sa = get_piece_segment_state(a, now_ms)
    sb = get_piece_segment_state(b, now_ms)
    return sa["segment_start"] == sb["segment_end"] and sa["segment_end"] == sb["segment_start"]


def _moving_vs_moving_contacts(state: MatchState, now_ms: int) -> list[tuple[Piece, Piece, str]]:
    moving = _moving_pieces(state)
    out: list[tuple[Piece, Piece, str]] = []
    for i in range(len(moving)):
        for j in range(i + 1, len(moving)):
            a, b = moving[i], moving[j]
            if a.owner == b.owner:
                continue
            a_cells = get_piece_runtime_cells(a, now_ms)
            b_cells = get_piece_runtime_cells(b, now_ms)
            if not a_cells.intersection(b_cells):
                continue
            reason = "head_on" if _is_head_on(a, b, now_ms) else "same_cell"
            out.append((a, b, reason))
    return out


def _resolve_moving_duel(a: Piece, b: Piece) -> tuple[Piece | None, Piece | None]:
    if a.move_start_at is None or b.move_start_at is None:
        return None, None
    if a.move_start_at < b.move_start_at:
        return a, b
    if b.move_start_at < a.move_start_at:
        return b, a
    return None, None


def resolve_contacts(state: MatchState, now_ms: int) -> None:
    for mover, static in _moving_vs_static_contacts(state, now_ms):
        if mover.alive and static.alive:
            apply_capture(state, mover, static, now_ms, reason="move_vs_static")

    for a, b, mode in _moving_vs_moving_contacts(state, now_ms):
        if not a.alive or not b.alive:
            continue
        winner, loser = _resolve_moving_duel(a, b)
        if winner and loser:
            apply_capture(state, winner, loser, now_ms, reason=f"move_vs_move_{mode}")
        else:
            apply_capture(state, None, a, now_ms, reason="mutual_destroy")
            apply_capture(state, None, b, now_ms, reason="mutual_destroy")

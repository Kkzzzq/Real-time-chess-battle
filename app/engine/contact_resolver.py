from __future__ import annotations

from app.domain.enums import PieceType
from app.domain.events import EVENT_CAPTURE, GameEvent
from app.domain.models import MatchState, Piece
from app.engine.timeline import get_piece_display_position


def apply_capture(state: MatchState, winner: Piece, loser: Piece, now_ms: int) -> None:
    if not loser.alive:
        return
    loser.alive = False
    loser.is_moving = False
    if loser.kind == PieceType.GENERAL:
        loser.path_points = []
    state.last_capture_at = now_ms
    state.add_event(GameEvent(EVENT_CAPTURE, now_ms, {"by": winner.id, "target": loser.id}))


def detect_move_vs_static_contacts(state: MatchState, now_ms: int) -> list[tuple[Piece, Piece]]:
    pairs = []
    for m in [p for p in state.pieces.values() if p.alive and p.is_moving]:
        mx, my = get_piece_display_position(m, now_ms)
        cell = (round(mx), round(my))
        for s in state.pieces.values():
            if not s.alive or s.is_moving or s.owner == m.owner:
                continue
            if (s.x, s.y) == cell:
                pairs.append((m, s))
    return pairs


def resolve_same_cell_contact(a: Piece, b: Piece) -> tuple[Piece | None, Piece | None]:
    if a.move_start_at is None or b.move_start_at is None:
        return None, None
    if a.move_start_at < b.move_start_at:
        return a, b
    if b.move_start_at < a.move_start_at:
        return b, a
    return None, None


def resolve_head_on_contact(a: Piece, b: Piece) -> tuple[Piece | None, Piece | None]:
    return resolve_same_cell_contact(a, b)


def detect_move_vs_move_contacts(state: MatchState, now_ms: int) -> list[tuple[Piece, Piece]]:
    moving = [p for p in state.pieces.values() if p.alive and p.is_moving]
    pairs: list[tuple[Piece, Piece]] = []
    for i in range(len(moving)):
        for j in range(i + 1, len(moving)):
            a, b = moving[i], moving[j]
            if a.owner == b.owner:
                continue
            ax, ay = get_piece_display_position(a, now_ms)
            bx, by = get_piece_display_position(b, now_ms)
            if round(ax) == round(bx) and round(ay) == round(by):
                pairs.append((a, b))
    return pairs


def resolve_contacts(state: MatchState, now_ms: int) -> None:
    for m, s in detect_move_vs_static_contacts(state, now_ms):
        apply_capture(state, m, s, now_ms)
    for a, b in detect_move_vs_move_contacts(state, now_ms):
        winner, loser = resolve_same_cell_contact(a, b)
        if winner and loser:
            apply_capture(state, winner, loser, now_ms)
        else:
            a.alive = False
            b.alive = False
            state.last_capture_at = now_ms
            state.add_event(GameEvent(EVENT_CAPTURE, now_ms, {"mutual": [a.id, b.id]}))

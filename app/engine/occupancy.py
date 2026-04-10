from __future__ import annotations

from app.domain.models import MatchState, Piece
from app.engine.timeline import get_piece_segment_state


def get_piece_runtime_cells(piece: Piece, now_ms: int) -> set[tuple[int, int]]:
    if not piece.alive:
        return set()
    if not piece.is_moving:
        return {(piece.x, piece.y)}

    seg = get_piece_segment_state(piece, now_ms)
    start = tuple(seg["segment_start"])
    end = tuple(seg["segment_end"])
    local = seg["local_progress"]

    if local <= 0.0:
        return {start}
    if local >= 1.0:
        return {end}
    return {start, end}


def get_cell_owner(state: MatchState, x: int, y: int, now_ms: int, ignore_piece_ids: set[str] | None = None) -> Piece | None:
    ignore_piece_ids = ignore_piece_ids or set()
    for piece in state.pieces.values():
        if piece.id in ignore_piece_ids or not piece.alive:
            continue
        if (x, y) in get_piece_runtime_cells(piece, now_ms):
            return piece
    return None


def is_cell_blocked(
    state: MatchState,
    x: int,
    y: int,
    now_ms: int,
    ignore_piece_ids: set[str] | None = None,
) -> bool:
    return get_cell_owner(state, x, y, now_ms, ignore_piece_ids) is not None


def get_path_blockers(
    state: MatchState,
    path: list[tuple[int, int]],
    now_ms: int,
    ignore_piece_ids: set[str] | None = None,
) -> list[tuple[tuple[int, int], Piece]]:
    blockers: list[tuple[tuple[int, int], Piece]] = []
    for cell in path:
        owner = get_cell_owner(state, cell[0], cell[1], now_ms, ignore_piece_ids)
        if owner is not None:
            blockers.append((cell, owner))
    return blockers

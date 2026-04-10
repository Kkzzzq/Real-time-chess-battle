from __future__ import annotations

from app.domain.models import MatchState, Piece


def start_move(piece: Piece, path: list[tuple[int, int]], now_ms: int, duration_ms: int) -> None:
    piece.is_moving = True
    piece.move_start_at = now_ms
    piece.move_end_at = now_ms + duration_ms
    piece.move_total_ms = duration_ms
    piece.path_points = path
    piece.start_x, piece.start_y = piece.x, piece.y
    piece.target_x, piece.target_y = path[-1]
    piece.last_command_at = now_ms


def _interp(path: list[tuple[int, int]], progress: float, sx: int, sy: int) -> tuple[float, float]:
    if not path:
        return float(sx), float(sy)
    points = [(sx, sy), *path]
    seg_count = len(points) - 1
    if seg_count <= 0:
        return float(sx), float(sy)
    p = min(max(progress, 0.0), 0.999999)
    idx = int(p * seg_count)
    local = p * seg_count - idx
    x1, y1 = points[idx]
    x2, y2 = points[idx + 1]
    return x1 + (x2 - x1) * local, y1 + (y2 - y1) * local


def get_piece_display_position(piece: Piece, now_ms: int) -> tuple[float, float]:
    if not piece.is_moving or piece.move_start_at is None or piece.move_end_at is None or piece.move_total_ms <= 0:
        return float(piece.x), float(piece.y)
    if now_ms >= piece.move_end_at:
        return float(piece.target_x), float(piece.target_y)
    progress = (now_ms - piece.move_start_at) / piece.move_total_ms
    return _interp(piece.path_points, progress, piece.start_x, piece.start_y)


def is_piece_arrived(piece: Piece, now_ms: int) -> bool:
    return bool(piece.is_moving and piece.move_end_at is not None and now_ms >= piece.move_end_at)


def finish_move(piece: Piece, now_ms: int) -> None:
    piece.x, piece.y = piece.target_x, piece.target_y
    piece.is_moving = False
    piece.move_start_at = None
    piece.move_end_at = None
    piece.path_points = []


def advance_piece(piece: Piece, now_ms: int) -> bool:
    return is_piece_arrived(piece, now_ms)


def advance_all_pieces(state: MatchState, now_ms: int) -> list[Piece]:
    return [p for p in state.pieces.values() if p.alive and advance_piece(p, now_ms)]

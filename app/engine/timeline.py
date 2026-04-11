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
    piece.current_segment_index = 0


def get_path_with_start(piece: Piece) -> list[tuple[int, int]]:
    return [(piece.start_x, piece.start_y), *piece.path_points]


def get_piece_segment_state(piece: Piece, now_ms: int) -> dict:
    if not piece.is_moving or piece.move_start_at is None or piece.move_end_at is None or piece.move_total_ms <= 0:
        return {
            "moving": False,
            "segment_index": -1,
            "segment_count": 0,
            "segment_start": (piece.x, piece.y),
            "segment_end": (piece.x, piece.y),
            "local_progress": 1.0,
            "left_start_cell": True,
            "entered_target_cell": True,
        }

    points = get_path_with_start(piece)
    seg_count = max(0, len(points) - 1)
    if seg_count == 0:
        return {
            "moving": True,
            "segment_index": 0,
            "segment_count": 0,
            "segment_start": points[0],
            "segment_end": points[0],
            "local_progress": 1.0,
            "left_start_cell": True,
            "entered_target_cell": True,
        }

    if now_ms >= piece.move_end_at:
        idx = seg_count - 1
        local = 1.0
    else:
        progress = max(0.0, min(0.999999, (now_ms - piece.move_start_at) / piece.move_total_ms))
        idx = int(progress * seg_count)
        local = progress * seg_count - idx

    seg_start = points[idx]
    seg_end = points[idx + 1]
    return {
        "moving": True,
        "segment_index": idx,
        "segment_count": seg_count,
        "segment_start": seg_start,
        "segment_end": seg_end,
        "local_progress": local,
        "left_start_cell": idx > 0 or local > 0.0,
        "entered_target_cell": idx == seg_count - 1 and local >= 1.0,
    }


def get_piece_display_position(piece: Piece, now_ms: int) -> tuple[float, float]:
    seg = get_piece_segment_state(piece, now_ms)
    if not seg["moving"]:
        return float(piece.x), float(piece.y)
    x1, y1 = seg["segment_start"]
    x2, y2 = seg["segment_end"]
    local = seg["local_progress"]
    return x1 + (x2 - x1) * local, y1 + (y2 - y1) * local


def is_piece_arrived(piece: Piece, now_ms: int) -> bool:
    return bool(piece.is_moving and piece.move_end_at is not None and now_ms >= piece.move_end_at)


def finish_move(piece: Piece, now_ms: int) -> None:
    piece.x, piece.y = piece.target_x, piece.target_y
    piece.is_moving = False
    piece.move_start_at = None
    piece.move_end_at = None
    piece.path_points = []
    piece.current_segment_index = -1
    piece.last_resolved_at = now_ms


def terminate_move(piece: Piece, now_ms: int) -> None:
    piece.is_moving = False
    piece.move_start_at = None
    piece.move_end_at = None
    piece.path_points = []
    piece.current_segment_index = -1
    piece.last_resolved_at = now_ms


def advance_piece(piece: Piece, now_ms: int) -> bool:
    if not piece.is_moving:
        return False
    piece.current_segment_index = get_piece_segment_state(piece, now_ms)["segment_index"]
    return is_piece_arrived(piece, now_ms)


def advance_all_pieces(state: MatchState, now_ms: int) -> list[Piece]:
    return [p for p in state.pieces.values() if p.alive and advance_piece(p, now_ms)]

from __future__ import annotations

from app.core.ruleset import FIXED_MOVE_SECONDS
from app.domain.enums import PieceType
from app.domain.models import Piece


def build_path(piece: Piece, start: tuple[int, int], target: tuple[int, int]) -> list[tuple[int, int]]:
    if piece.kind == PieceType.CHARIOT:
        return build_rook_path(start, target)
    if piece.kind == PieceType.CANNON:
        return build_cannon_path(start, target)
    if piece.kind == PieceType.HORSE:
        return build_horse_path(start, target)
    if piece.kind == PieceType.ELEPHANT:
        return build_elephant_path(start, target)
    return build_single_step_path(start, target)


def build_rook_path(start: tuple[int, int], target: tuple[int, int]) -> list[tuple[int, int]]:
    x1, y1 = start
    x2, y2 = target
    path: list[tuple[int, int]] = []
    if x1 == x2:
        step = 1 if y2 > y1 else -1
        for y in range(y1 + step, y2 + step, step):
            path.append((x1, y))
    else:
        step = 1 if x2 > x1 else -1
        for x in range(x1 + step, x2 + step, step):
            path.append((x, y1))
    return path


def build_cannon_path(start: tuple[int, int], target: tuple[int, int]) -> list[tuple[int, int]]:
    return build_rook_path(start, target)


def build_horse_path(start: tuple[int, int], target: tuple[int, int]) -> list[tuple[int, int]]:
    x1, y1 = start
    x2, y2 = target
    dx, dy = x2 - x1, y2 - y1
    leg = (x1 + dx // 2, y1) if abs(dx) == 2 else (x1, y1 + dy // 2)
    return [leg, (x2, y2)]


def build_elephant_path(start: tuple[int, int], target: tuple[int, int]) -> list[tuple[int, int]]:
    x1, y1 = start
    x2, y2 = target
    eye = (x1 + (x2 - x1) // 2, y1 + (y2 - y1) // 2)
    return [eye, (x2, y2)]


def build_single_step_path(start: tuple[int, int], target: tuple[int, int]) -> list[tuple[int, int]]:
    return [target]


def get_move_duration_ms(piece: Piece, path_points: list[tuple[int, int]]) -> int:
    if piece.kind in FIXED_MOVE_SECONDS:
        return int(FIXED_MOVE_SECONDS[piece.kind] * 1000)
    return len(path_points) * 1000


def get_path_segments(path_points: list[tuple[int, int]], start: tuple[int, int], start_ms: int, end_ms: int) -> list[dict]:
    points = [start, *path_points]
    if len(points) < 2:
        return []
    total = end_ms - start_ms
    each = total / (len(points)-1)
    out=[]
    for i in range(len(points)-1):
        out.append({"index": i, "from": points[i], "to": points[i+1], "enter_ms": int(start_ms + i*each), "leave_ms": int(start_ms + (i+1)*each)})
    return out

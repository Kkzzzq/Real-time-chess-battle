from __future__ import annotations

from app.core.constants import BOARD_COLS, BOARD_ROWS
from app.core.ruleset import (
    BLACK_PALACE_X,
    BLACK_PALACE_Y,
    RED_PALACE_X,
    RED_PALACE_Y,
)
from app.domain.enums import PieceType
from app.domain.models import MatchState, Piece


def piece_at(state: MatchState, x: int, y: int, ignore: set[str] | None = None) -> Piece | None:
    ignore = ignore or set()
    for p in state.pieces.values():
        if p.alive and p.id not in ignore and p.x == x and p.y == y:
            return p
    return None


def count_between(state: MatchState, x1: int, y1: int, x2: int, y2: int, ignore: set[str] | None = None) -> int:
    ignore = ignore or set()
    count = 0
    if x1 == x2:
        lo, hi = sorted((y1, y2))
        for y in range(lo + 1, hi):
            if piece_at(state, x1, y, ignore):
                count += 1
    elif y1 == y2:
        lo, hi = sorted((x1, x2))
        for x in range(lo + 1, hi):
            if piece_at(state, x, y1, ignore):
                count += 1
    return count


def validate_move(piece: Piece, target: tuple[int, int], state: MatchState) -> tuple[bool, str]:
    tx, ty = target
    if not piece.alive:
        return False, "piece dead"
    if piece.is_moving:
        return False, "piece moving"
    if not (0 <= tx < BOARD_COLS and 0 <= ty < BOARD_ROWS):
        return False, "target out of board"
    if (piece.x, piece.y) == target:
        return False, "same cell"
    occ = piece_at(state, tx, ty)
    if occ and occ.owner == piece.owner:
        return False, "cannot capture ally"

    checker = {
        PieceType.SOLDIER: validate_soldier_move,
        PieceType.ADVISOR: validate_guard_move,
        PieceType.ELEPHANT: validate_elephant_move,
        PieceType.HORSE: validate_horse_move,
        PieceType.CHARIOT: validate_rook_move,
        PieceType.CANNON: validate_cannon_move,
        PieceType.GENERAL: validate_general_move,
    }[piece.kind]
    ok, msg = checker(piece, tx, ty, state)
    if not ok:
        return ok, msg
    if would_generals_face_after_move(piece, target, state):
        return False, "generals cannot face"
    return True, "ok"


def validate_soldier_move(piece: Piece, tx: int, ty: int, state: MatchState) -> tuple[bool, str]:
    dx, dy = tx - piece.x, ty - piece.y
    if abs(dx) + abs(dy) != 1:
        return False, "soldier one step"
    fwd = -1 if piece.owner == 1 else 1
    crossed = piece.y <= 4 if piece.owner == 1 else piece.y >= 5
    if dy == fwd and dx == 0:
        return True, "ok"
    if crossed and dy == 0 and abs(dx) == 1:
        return True, "ok"
    return False, "invalid soldier move"


def validate_guard_move(piece: Piece, tx: int, ty: int, state: MatchState) -> tuple[bool, str]:
    if abs(tx - piece.x) != 1 or abs(ty - piece.y) != 1:
        return False, "guard diagonal"
    palace_x = RED_PALACE_X if piece.owner == 1 else BLACK_PALACE_X
    palace_y = RED_PALACE_Y if piece.owner == 1 else BLACK_PALACE_Y
    if tx not in palace_x or ty not in palace_y:
        return False, "guard in palace"
    return True, "ok"


def validate_elephant_move(piece: Piece, tx: int, ty: int, state: MatchState) -> tuple[bool, str]:
    dx, dy = tx - piece.x, ty - piece.y
    if abs(dx) != 2 or abs(dy) != 2:
        return False, "elephant 2 diagonal"
    eye_x, eye_y = piece.x + dx // 2, piece.y + dy // 2
    if piece_at(state, eye_x, eye_y):
        return False, "elephant eye blocked"
    if piece.owner == 1 and ty < 5:
        return False, "elephant no river"
    if piece.owner == 2 and ty > 4:
        return False, "elephant no river"
    return True, "ok"


def validate_horse_move(piece: Piece, tx: int, ty: int, state: MatchState) -> tuple[bool, str]:
    dx, dy = tx - piece.x, ty - piece.y
    if (abs(dx), abs(dy)) not in {(2, 1), (1, 2)}:
        return False, "horse L"
    leg = (piece.x + dx // 2, piece.y) if abs(dx) == 2 else (piece.x, piece.y + dy // 2)
    if piece_at(state, leg[0], leg[1]):
        return False, "horse leg blocked"
    return True, "ok"


def validate_rook_move(piece: Piece, tx: int, ty: int, state: MatchState) -> tuple[bool, str]:
    if piece.x != tx and piece.y != ty:
        return False, "rook straight"
    if count_between(state, piece.x, piece.y, tx, ty, {piece.id}) != 0:
        return False, "rook blocked"
    return True, "ok"


def validate_cannon_move(piece: Piece, tx: int, ty: int, state: MatchState) -> tuple[bool, str]:
    if piece.x != tx and piece.y != ty:
        return False, "cannon straight"
    between = count_between(state, piece.x, piece.y, tx, ty, {piece.id})
    target = piece_at(state, tx, ty)
    if target is None and between == 0:
        return True, "ok"
    if target is not None and between == 1:
        return True, "ok"
    return False, "invalid cannon"


def validate_general_move(piece: Piece, tx: int, ty: int, state: MatchState) -> tuple[bool, str]:
    enemy = next(p for p in state.pieces.values() if p.alive and p.kind == PieceType.GENERAL and p.owner != piece.owner)
    if tx == enemy.x and ty == enemy.y and piece.x == enemy.x and count_between(state, piece.x, piece.y, enemy.x, enemy.y, {piece.id, enemy.id}) == 0:
        return True, "ok"
    if abs(tx - piece.x) + abs(ty - piece.y) != 1:
        return False, "general one orthogonal"
    palace_x = RED_PALACE_X if piece.owner == 1 else BLACK_PALACE_X
    palace_y = RED_PALACE_Y if piece.owner == 1 else BLACK_PALACE_Y
    if tx not in palace_x or ty not in palace_y:
        return False, "general in palace"
    return True, "ok"


def would_generals_face_after_move(piece: Piece, target: tuple[int, int], state: MatchState) -> bool:
    tx, ty = target
    enemy_general = next((p for p in state.pieces.values() if p.alive and p.kind == PieceType.GENERAL and p.owner != piece.owner), None)
    if enemy_general and (tx, ty) == (enemy_general.x, enemy_general.y):
        return False
    generals = {}
    for p in state.pieces.values():
        if not p.alive:
            continue
        x, y = (tx, ty) if p.id == piece.id else (p.x, p.y)
        if p.kind == PieceType.GENERAL:
            generals[p.owner] = (x, y, p.id)
    if 1 not in generals or 2 not in generals:
        return False
    x1, y1, g1 = generals[1]
    x2, y2, g2 = generals[2]
    if x1 != x2:
        return False
    return count_between(state, x1, y1, x2, y2, {piece.id, g1, g2}) == 0 and not (piece.id not in {g1, g2} and tx == x1 and min(y1, y2) < ty < max(y1, y2))


def list_legal_targets(piece: Piece, state: MatchState) -> list[tuple[int, int]]:
    legal = []
    for x in range(BOARD_COLS):
        for y in range(BOARD_ROWS):
            ok, _ = validate_move(piece, (x, y), state)
            if ok:
                legal.append((x, y))
    return legal

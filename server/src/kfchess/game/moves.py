"""Move definitions and validation for Real-time-chess-battle (中国象棋版)."""

from __future__ import annotations

from dataclasses import dataclass, field

from kfchess.game.board import Board
from kfchess.game.pieces import Piece, PieceType

PathPoint = tuple[float, float]


@dataclass
class _EnemyMoveInfo:
    dr: int
    dc: int
    start_r: int
    start_c: int
    forward_squares: list[tuple[int, int]]


@dataclass
class PathClearContext:
    own_forward_path: set[tuple[int, int]] = field(default_factory=set)
    moving_piece_ids: set[str] = field(default_factory=set)
    enemy_moves: list[_EnemyMoveInfo] = field(default_factory=list)


FOUR_PLAYER_ORIENTATIONS: dict[int, object] = {}


@dataclass
class Move:
    piece_id: str
    path: list[PathPoint]
    start_tick: int
    extra_move: Move | None = None

    def to_dict(self) -> dict:
        return {
            "piece_id": self.piece_id,
            "path": [list(p) for p in self.path],
            "start_tick": self.start_tick,
            "extra_move": self.extra_move.to_dict() if self.extra_move else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Move:
        return cls(
            piece_id=data["piece_id"],
            path=[tuple(p) for p in data["path"]],
            start_tick=data["start_tick"],
            extra_move=cls.from_dict(data["extra_move"]) if data.get("extra_move") else None,
        )

    @property
    def start_position(self) -> PathPoint:
        return self.path[0]

    @property
    def end_position(self) -> PathPoint:
        return self.path[-1]

    @property
    def num_squares(self) -> int:
        return len(self.path) - 1


@dataclass
class Cooldown:
    piece_id: str
    start_tick: int
    duration: int

    def to_dict(self) -> dict:
        return {
            "piece_id": self.piece_id,
            "start_tick": self.start_tick,
            "duration": self.duration,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Cooldown:
        return cls(
            piece_id=data["piece_id"],
            start_tick=data["start_tick"],
            duration=data["duration"],
        )

    def is_active(self, current_tick: int) -> bool:
        return current_tick < self.start_tick + self.duration


def build_path_clear_context(
    player: int,
    board: Board,
    active_moves: list[Move],
    current_tick: int,
    ticks_per_square: int,
) -> PathClearContext:
    del player, board, current_tick, ticks_per_square
    return PathClearContext(moving_piece_ids={m.piece_id for m in active_moves})


def compute_move_path(
    piece: Piece,
    board: Board,
    to_row: int,
    to_col: int,
    active_moves: list[Move],
    current_tick: int = 0,
    ticks_per_square: int = 30,
    path_context: PathClearContext | None = None,
) -> list[PathPoint] | None:
    del current_tick, ticks_per_square
    from_row, from_col = piece.grid_position
    if (from_row, from_col) == (to_row, to_col):
        return None
    if not board.is_valid_square(to_row, to_col):
        return None

    moving_ids = path_context.moving_piece_ids if path_context else {m.piece_id for m in active_moves}
    destination_piece = board.get_piece_at(to_row, to_col)
    if destination_piece is not None and destination_piece.player == piece.player and destination_piece.id not in moving_ids:
        return None

    match piece.type:
        case PieceType.SOLDIER | PieceType.PAWN:
            path = _compute_soldier_path(piece, board, from_row, from_col, to_row, to_col)
        case PieceType.HORSE | PieceType.KNIGHT:
            path = _compute_horse_path(piece, board, from_row, from_col, to_row, to_col, moving_ids)
        case PieceType.ELEPHANT | PieceType.BISHOP:
            path = _compute_elephant_path(piece, board, from_row, from_col, to_row, to_col, moving_ids)
        case PieceType.CHARIOT | PieceType.ROOK:
            path = _compute_chariot_path(piece, board, from_row, from_col, to_row, to_col, moving_ids)
        case PieceType.CANNON:
            path = _compute_cannon_path(piece, board, from_row, from_col, to_row, to_col, moving_ids)
        case PieceType.ADVISOR | PieceType.QUEEN:
            path = _compute_advisor_path(piece, board, from_row, from_col, to_row, to_col)
        case PieceType.GENERAL | PieceType.KING:
            path = _compute_general_path(piece, board, from_row, from_col, to_row, to_col, moving_ids)
        case _:
            path = None

    if path is None:
        return None
    if _would_generals_face_after_move(piece, board, to_row, to_col, moving_ids):
        return None
    return path


def should_promote_pawn(piece: Piece, board: Board, end_row: int, end_col: int) -> bool:
    del piece, board, end_row, end_col
    return False


def check_castling(
    piece: Piece,
    board: Board,
    to_row: int,
    to_col: int,
    active_moves: list[Move],
    cooldowns: list[Cooldown] | None = None,
    current_tick: int = 0,
    ticks_per_square: int = 30,
) -> tuple[Move, Move] | None:
    del piece, board, to_row, to_col, active_moves, cooldowns, current_tick, ticks_per_square
    return None


def _get_occupant(board: Board, row: int, col: int, moving_ids: set[str]) -> Piece | None:
    piece = board.get_piece_at(row, col)
    if piece is None:
        return None
    if piece.id in moving_ids:
        return None
    return piece


def _line_squares(from_row: int, from_col: int, to_row: int, to_col: int) -> list[tuple[int, int]]:
    squares: list[tuple[int, int]] = []
    if from_row == to_row:
        step = 1 if to_col > from_col else -1
        for c in range(from_col + step, to_col, step):
            squares.append((from_row, c))
    elif from_col == to_col:
        step = 1 if to_row > from_row else -1
        for r in range(from_row + step, to_row, step):
            squares.append((r, from_col))
    return squares


def _would_generals_face_after_move(piece: Piece, board: Board, to_row: int, to_col: int, moving_ids: set[str]) -> bool:
    generals: dict[int, tuple[int, int]] = {}
    for p in board.get_active_pieces():
        if p.captured:
            continue
        if p.type not in (PieceType.GENERAL, PieceType.KING):
            continue
        if p.id == piece.id:
            generals[p.player] = (to_row, to_col)
            continue
        if p.grid_position == (to_row, to_col) and p.player != piece.player:
            continue
        generals[p.player] = p.grid_position

    if 1 not in generals or 2 not in generals:
        return False
    red = generals[1]
    black = generals[2]
    if red[1] != black[1]:
        return False
    col = red[1]
    start = min(red[0], black[0]) + 1
    end = max(red[0], black[0])
    for row in range(start, end):
        occ = _get_occupant(board, row, col, moving_ids)
        if occ is None:
            continue
        if occ.id == piece.id:
            continue
        if occ.grid_position == (to_row, to_col) and occ.player != piece.player:
            continue
        return False
    return True


def _compute_soldier_path(piece: Piece, board: Board, from_row: int, from_col: int, to_row: int, to_col: int) -> list[PathPoint] | None:
    dr = to_row - from_row
    dc = to_col - from_col
    forward = -1 if piece.player == 1 else 1
    crossed = board.has_crossed_river(piece.player, from_row)
    allowed = {(forward, 0)}
    if crossed:
        allowed |= {(0, -1), (0, 1)}
    if (dr, dc) not in allowed:
        return None
    return [(from_row, from_col), (to_row, to_col)]


def _compute_horse_path(piece: Piece, board: Board, from_row: int, from_col: int, to_row: int, to_col: int, moving_ids: set[str]) -> list[PathPoint] | None:
    del piece
    dr = to_row - from_row
    dc = to_col - from_col
    if sorted((abs(dr), abs(dc))) != [1, 2]:
        return None
    if abs(dr) == 2:
        leg = (from_row + dr // 2, from_col)
    else:
        leg = (from_row, from_col + dc // 2)
    if _get_occupant(board, leg[0], leg[1], moving_ids) is not None:
        return None
    return [(from_row, from_col), leg, (to_row, to_col)]


def _compute_elephant_path(piece: Piece, board: Board, from_row: int, from_col: int, to_row: int, to_col: int, moving_ids: set[str]) -> list[PathPoint] | None:
    dr = to_row - from_row
    dc = to_col - from_col
    if abs(dr) != 2 or abs(dc) != 2:
        return None
    if not board.same_side_of_river(piece.player, to_row):
        return None
    eye = (from_row + dr // 2, from_col + dc // 2)
    if _get_occupant(board, eye[0], eye[1], moving_ids) is not None:
        return None
    return [(from_row, from_col), eye, (to_row, to_col)]


def _compute_advisor_path(piece: Piece, board: Board, from_row: int, from_col: int, to_row: int, to_col: int) -> list[PathPoint] | None:
    if abs(to_row - from_row) != 1 or abs(to_col - from_col) != 1:
        return None
    if not board.is_palace_square(piece.player, to_row, to_col):
        return None
    return [(from_row, from_col), (to_row, to_col)]


def _compute_general_path(piece: Piece, board: Board, from_row: int, from_col: int, to_row: int, to_col: int, moving_ids: set[str]) -> list[PathPoint] | None:
    destination_piece = board.get_piece_at(to_row, to_col)
    # 飞将：在同一列无阻挡时可以直接吃掉对方将/帅
    if destination_piece is not None and destination_piece.player != piece.player and destination_piece.type in (PieceType.GENERAL, PieceType.KING):
        if from_col != to_col:
            return None
        middle = _line_squares(from_row, from_col, to_row, to_col)
        blockers = [sq for sq in middle if _get_occupant(board, sq[0], sq[1], moving_ids) is not None]
        if blockers:
            return None
        return [(from_row, from_col), (to_row, to_col)]

    if abs(to_row - from_row) + abs(to_col - from_col) != 1:
        return None
    if not board.is_palace_square(piece.player, to_row, to_col):
        return None
    return [(from_row, from_col), (to_row, to_col)]


def _compute_chariot_path(piece: Piece, board: Board, from_row: int, from_col: int, to_row: int, to_col: int, moving_ids: set[str]) -> list[PathPoint] | None:
    del piece
    if from_row != to_row and from_col != to_col:
        return None
    middle = _line_squares(from_row, from_col, to_row, to_col)
    if any(_get_occupant(board, r, c, moving_ids) is not None for r, c in middle):
        return None
    return [(from_row, from_col), (to_row, to_col)]


def _compute_cannon_path(piece: Piece, board: Board, from_row: int, from_col: int, to_row: int, to_col: int, moving_ids: set[str]) -> list[PathPoint] | None:
    del piece
    if from_row != to_row and from_col != to_col:
        return None
    middle = _line_squares(from_row, from_col, to_row, to_col)
    blockers = sum(1 for r, c in middle if _get_occupant(board, r, c, moving_ids) is not None)
    destination_piece = _get_occupant(board, to_row, to_col, moving_ids)
    if destination_piece is None:
        if blockers != 0:
            return None
    else:
        if blockers != 1:
            return None
    return [(from_row, from_col), (to_row, to_col)]

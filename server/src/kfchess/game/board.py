"""Board representation for Real-time-chess-battle (中国象棋版)."""

from dataclasses import dataclass, field
from enum import Enum

from kfchess.game.pieces import Piece, PieceType


class BoardType(Enum):
    """Board layout type.

    兼容旧存量数据，保留 FOUR_PLAYER 枚举值；
    但本次改造后端只正式支持 STANDARD（9x10 中国象棋双人对局）。
    """

    STANDARD = "standard"
    FOUR_PLAYER = "four_player"


XQ_BACK_ROW = [
    PieceType.CHARIOT,
    PieceType.HORSE,
    PieceType.ELEPHANT,
    PieceType.ADVISOR,
    PieceType.GENERAL,
    PieceType.ADVISOR,
    PieceType.ELEPHANT,
    PieceType.HORSE,
    PieceType.CHARIOT,
]


@dataclass
class Board:
    """中国象棋棋盘。"""

    pieces: list[Piece] = field(default_factory=list)
    board_type: BoardType = BoardType.STANDARD
    width: int = 9
    height: int = 10

    _position_map: dict[tuple[int, int], Piece] | None = field(default=None, repr=False, compare=False)
    _id_map: dict[str, Piece] | None = field(default=None, repr=False, compare=False)
    _king_cache: dict[int, Piece | None] | None = field(default=None, repr=False, compare=False)

    @classmethod
    def create_standard(cls) -> "Board":
        pieces: list[Piece] = []

        # 黑方（player=2）在上方
        for col, piece_type in enumerate(XQ_BACK_ROW):
            pieces.append(Piece.create(piece_type, player=2, row=0, col=col))
        pieces.append(Piece.create(PieceType.CANNON, player=2, row=2, col=1))
        pieces.append(Piece.create(PieceType.CANNON, player=2, row=2, col=7))
        for col in (0, 2, 4, 6, 8):
            pieces.append(Piece.create(PieceType.SOLDIER, player=2, row=3, col=col))

        # 红方（player=1）在下方
        for col, piece_type in enumerate(XQ_BACK_ROW):
            pieces.append(Piece.create(piece_type, player=1, row=9, col=col))
        pieces.append(Piece.create(PieceType.CANNON, player=1, row=7, col=1))
        pieces.append(Piece.create(PieceType.CANNON, player=1, row=7, col=7))
        for col in (0, 2, 4, 6, 8):
            pieces.append(Piece.create(PieceType.SOLDIER, player=1, row=6, col=col))

        return cls(pieces=pieces, board_type=BoardType.STANDARD, width=9, height=10)

    @classmethod
    def create_4player(cls) -> "Board":
        raise ValueError("Real-time-chess-battle 当前版本只支持 2 人中国象棋棋盘")

    @classmethod
    def create_empty(cls, board_type: BoardType = BoardType.STANDARD) -> "Board":
        if board_type != BoardType.STANDARD:
            raise ValueError("仅支持 standard 中国象棋棋盘")
        return cls(pieces=[], board_type=board_type, width=9, height=10)

    def copy(self) -> "Board":
        return Board(
            pieces=[p.copy() for p in self.pieces],
            board_type=self.board_type,
            width=self.width,
            height=self.height,
        )

    def get_piece_by_id(self, piece_id: str) -> Piece | None:
        if self._id_map is None:
            self._build_id_map()
        return self._id_map.get(piece_id)

    def get_piece_at(self, row: int, col: int) -> Piece | None:
        if self._position_map is None:
            self._build_position_map()
        return self._position_map.get((row, col))

    def invalidate_position_map(self) -> None:
        self._position_map = None
        self._id_map = None
        self._king_cache = None

    def _build_position_map(self) -> None:
        self._position_map = {}
        for piece in self.pieces:
            if piece.captured:
                continue
            self._position_map[piece.grid_position] = piece

    def _build_id_map(self) -> None:
        self._id_map = {p.id: p for p in self.pieces}

    def _build_king_cache(self) -> None:
        self._king_cache = {}
        for piece in self.pieces:
            if piece.type in (PieceType.GENERAL, PieceType.KING) and not piece.captured:
                self._king_cache[piece.player] = piece

    def get_pieces_for_player(self, player: int) -> list[Piece]:
        return [p for p in self.pieces if p.player == player and not p.captured]

    def get_active_pieces(self) -> list[Piece]:
        return [p for p in self.pieces if not p.captured]

    def get_king(self, player: int) -> Piece | None:
        if self._king_cache is None:
            self._build_king_cache()
        return self._king_cache.get(player)

    def is_valid_square(self, row: int, col: int) -> bool:
        return 0 <= row < self.height and 0 <= col < self.width

    def is_palace_square(self, player: int, row: int, col: int) -> bool:
        if col < 3 or col > 5:
            return False
        if player == 1:
            return 7 <= row <= 9
        return 0 <= row <= 2

    def has_crossed_river(self, player: int, row: int) -> bool:
        return row <= 4 if player == 1 else row >= 5

    def same_side_of_river(self, player: int, row: int) -> bool:
        return row >= 5 if player == 1 else row <= 4

    def add_piece(self, piece: Piece) -> None:
        self.pieces.append(piece)
        self.invalidate_position_map()

    def remove_piece(self, piece_id: str) -> bool:
        for i, piece in enumerate(self.pieces):
            if piece.id == piece_id:
                del self.pieces[i]
                self.invalidate_position_map()
                return True
        return False

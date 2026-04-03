"""Piece definitions for Real-time-chess-battle (中国象棋版)."""

from dataclasses import dataclass, field
from enum import Enum


class PieceType(Enum):
    """Chinese chess piece types.

    为了减少历史代码的改动成本，这里保留了部分旧枚举名作为别名：
    - PAWN -> SOLDIER
    - KNIGHT -> HORSE
    - BISHOP -> ELEPHANT
    - ROOK -> CHARIOT
    - QUEEN -> ADVISOR
    - KING -> GENERAL
    """

    SOLDIER = "P"
    HORSE = "N"
    ELEPHANT = "E"
    CHARIOT = "R"
    ADVISOR = "A"
    GENERAL = "G"
    CANNON = "C"

    PAWN = "P"
    KNIGHT = "N"
    BISHOP = "E"
    ROOK = "R"
    QUEEN = "A"
    KING = "G"

    def __str__(self) -> str:
        return self.value


@dataclass
class Piece:
    """棋盘上的棋子。

    Attributes:
        id: 唯一 ID，格式为 "TYPE:PLAYER:START_ROW:START_COL"
        type: 棋子类型
        player: 玩家编号（1=红方，2=黑方）
        row: 当前行坐标（实时移动时可以是浮点）
        col: 当前列坐标（实时移动时可以是浮点）
        captured: 是否已被吃掉
        moved: 是否发生过移动（保留字段，兼容旧协议）
        cooldown_end_tick: 最近一次冷却结束 tick
    """

    id: str
    type: PieceType
    player: int
    row: float
    col: float
    captured: bool = False
    moved: bool = False
    cooldown_end_tick: int = 0

    _grid_cache: tuple[int, int] | None = field(default=None, repr=False, compare=False)
    _grid_cache_row: float = field(default=float("nan"), repr=False, compare=False)
    _grid_cache_col: float = field(default=float("nan"), repr=False, compare=False)

    @classmethod
    def create(cls, piece_type: PieceType, player: int, row: int, col: int) -> "Piece":
        piece_id = f"{piece_type.value}:{player}:{row}:{col}"
        return cls(
            id=piece_id,
            type=piece_type,
            player=player,
            row=float(row),
            col=float(col),
        )

    def copy(self) -> "Piece":
        return Piece(
            id=self.id,
            type=self.type,
            player=self.player,
            row=self.row,
            col=self.col,
            captured=self.captured,
            moved=self.moved,
            cooldown_end_tick=self.cooldown_end_tick,
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "player": self.player,
            "row": self.row,
            "col": self.col,
            "captured": self.captured,
            "moved": self.moved,
            "cooldown_end_tick": self.cooldown_end_tick,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Piece":
        return cls(
            id=data["id"],
            type=PieceType(data["type"]),
            player=data["player"],
            row=float(data["row"]),
            col=float(data["col"]),
            captured=data.get("captured", False),
            moved=data.get("moved", False),
            cooldown_end_tick=data.get("cooldown_end_tick", 0),
        )

    @property
    def position(self) -> tuple[float, float]:
        return (self.row, self.col)

    @property
    def grid_position(self) -> tuple[int, int]:
        if self._grid_cache is not None and self._grid_cache_row == self.row and self._grid_cache_col == self.col:
            return self._grid_cache
        result = (int(round(self.row)), int(round(self.col)))
        self._grid_cache = result
        self._grid_cache_row = self.row
        self._grid_cache_col = self.col
        return result

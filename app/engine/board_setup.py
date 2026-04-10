from __future__ import annotations

from app.domain.enums import PieceType
from app.domain.models import Piece


def _pid(player: int, kind: PieceType, idx: int) -> str:
    return f"p{player}_{kind.value}_{idx}"


def initial_pieces() -> dict[str, Piece]:
    pieces: dict[str, Piece] = {}

    def add(player: int, piece_type: PieceType, x: int, y: int, idx: int) -> None:
        piece = Piece(piece_id=_pid(player, piece_type, idx), player=player, piece_type=piece_type, x=x, y=y)
        pieces[piece.piece_id] = piece

    # Player 1 (red) bottom.
    for x, i in ((0, 1), (8, 2)):
        add(1, PieceType.CHARIOT, x, 9, i)
    for x, i in ((1, 1), (7, 2)):
        add(1, PieceType.HORSE, x, 9, i)
    for x, i in ((2, 1), (6, 2)):
        add(1, PieceType.ELEPHANT, x, 9, i)
    for x, i in ((3, 1), (5, 2)):
        add(1, PieceType.ADVISOR, x, 9, i)
    add(1, PieceType.GENERAL, 4, 9, 1)
    for x, i in ((1, 1), (7, 2)):
        add(1, PieceType.CANNON, x, 7, i)
    for idx, x in enumerate((0, 2, 4, 6, 8), start=1):
        add(1, PieceType.SOLDIER, x, 6, idx)

    # Player 2 (black) top.
    for x, i in ((0, 1), (8, 2)):
        add(2, PieceType.CHARIOT, x, 0, i)
    for x, i in ((1, 1), (7, 2)):
        add(2, PieceType.HORSE, x, 0, i)
    for x, i in ((2, 1), (6, 2)):
        add(2, PieceType.ELEPHANT, x, 0, i)
    for x, i in ((3, 1), (5, 2)):
        add(2, PieceType.ADVISOR, x, 0, i)
    add(2, PieceType.GENERAL, 4, 0, 1)
    for x, i in ((1, 1), (7, 2)):
        add(2, PieceType.CANNON, x, 2, i)
    for idx, x in enumerate((0, 2, 4, 6, 8), start=1):
        add(2, PieceType.SOLDIER, x, 3, idx)

    return pieces

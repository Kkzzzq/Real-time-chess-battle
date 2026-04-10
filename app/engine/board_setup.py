from __future__ import annotations

from app.domain.enums import PieceType
from app.domain.models import Piece


def _make_piece(owner: int, kind: PieceType, idx: int, x: int, y: int, spawn_index: int) -> Piece:
    pid = f"p{owner}_{kind.value}_{idx}"
    return Piece(
        id=pid,
        owner=owner,
        kind=kind,
        x=x,
        y=y,
        start_x=x,
        start_y=y,
        target_x=x,
        target_y=y,
        spawn_index=spawn_index,
    )


def create_standard_board() -> dict[str, Piece]:
    pieces: dict[str, Piece] = {}
    spawn = 0

    def add(owner: int, kind: PieceType, idx: int, x: int, y: int) -> None:
        nonlocal spawn
        spawn += 1
        p = _make_piece(owner, kind, idx, x, y, spawn)
        pieces[p.id] = p

    # black (player=2) top
    add(2, PieceType.CHARIOT, 1, 0, 0)
    add(2, PieceType.HORSE, 1, 1, 0)
    add(2, PieceType.ELEPHANT, 1, 2, 0)
    add(2, PieceType.ADVISOR, 1, 3, 0)
    add(2, PieceType.GENERAL, 1, 4, 0)
    add(2, PieceType.ADVISOR, 2, 5, 0)
    add(2, PieceType.ELEPHANT, 2, 6, 0)
    add(2, PieceType.HORSE, 2, 7, 0)
    add(2, PieceType.CHARIOT, 2, 8, 0)
    add(2, PieceType.CANNON, 1, 1, 2)
    add(2, PieceType.CANNON, 2, 7, 2)
    for i, x in enumerate([0, 2, 4, 6, 8], start=1):
        add(2, PieceType.SOLDIER, i, x, 3)

    # red (player=1) bottom
    add(1, PieceType.CHARIOT, 1, 0, 9)
    add(1, PieceType.HORSE, 1, 1, 9)
    add(1, PieceType.ELEPHANT, 1, 2, 9)
    add(1, PieceType.ADVISOR, 1, 3, 9)
    add(1, PieceType.GENERAL, 1, 4, 9)
    add(1, PieceType.ADVISOR, 2, 5, 9)
    add(1, PieceType.ELEPHANT, 2, 6, 9)
    add(1, PieceType.HORSE, 2, 7, 9)
    add(1, PieceType.CHARIOT, 2, 8, 9)
    add(1, PieceType.CANNON, 1, 1, 7)
    add(1, PieceType.CANNON, 2, 7, 7)
    for i, x in enumerate([0, 2, 4, 6, 8], start=1):
        add(1, PieceType.SOLDIER, i, x, 6)

    return pieces


def reset_board(state) -> None:
    state.pieces = create_standard_board()

from __future__ import annotations

from enum import Enum


class PieceType(str, Enum):
    SOLDIER = "soldier"
    ADVISOR = "advisor"
    ELEPHANT = "elephant"
    HORSE = "horse"
    CANNON = "cannon"
    CHARIOT = "chariot"
    GENERAL = "general"


COOLDOWN_SECONDS: dict[PieceType, float] = {
    PieceType.SOLDIER: 10.0,
    PieceType.ADVISOR: 8.0,
    PieceType.ELEPHANT: 15.0,
    PieceType.HORSE: 20.0,
    PieceType.CANNON: 20.0,
    PieceType.CHARIOT: 30.0,
    PieceType.GENERAL: 3.0,
}

AUTO_UNLOCK_PRIORITY: list[PieceType] = [
    PieceType.CANNON,
    PieceType.HORSE,
    PieceType.CHARIOT,
    PieceType.ELEPHANT,
    PieceType.ADVISOR,
    PieceType.GENERAL,
]

UNLOCK_WAVES: dict[int, set[PieceType]] = {
    50: {PieceType.HORSE, PieceType.CANNON, PieceType.CHARIOT},
    70: {PieceType.HORSE, PieceType.CANNON, PieceType.CHARIOT, PieceType.ELEPHANT},
    90: {PieceType.HORSE, PieceType.CANNON, PieceType.CHARIOT, PieceType.ELEPHANT, PieceType.ADVISOR},
    110: set(PieceType),
}

ALL_PLAYERS = (1, 2)

BOARD_WIDTH = 9
BOARD_HEIGHT = 10

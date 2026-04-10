from __future__ import annotations

from app.domain.enums import PieceType

COOLDOWN_SECONDS: dict[PieceType, float] = {
    PieceType.SOLDIER: 10.0,
    PieceType.ADVISOR: 8.0,
    PieceType.ELEPHANT: 15.0,
    PieceType.HORSE: 20.0,
    PieceType.CANNON: 20.0,
    PieceType.CHARIOT: 30.0,
    PieceType.GENERAL: 3.0,
}

# 1 grid = 1 second. Horse/Elephant are two-segment, fixed 2 seconds.
FIXED_MOVE_SECONDS: dict[PieceType, float] = {
    PieceType.SOLDIER: 1.0,
    PieceType.ADVISOR: 1.0,
    PieceType.ELEPHANT: 2.0,
    PieceType.HORSE: 2.0,
    PieceType.GENERAL: 1.0,
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

RED_PALACE_X = {3, 4, 5}
RED_PALACE_Y = {7, 8, 9}
BLACK_PALACE_X = {3, 4, 5}
BLACK_PALACE_Y = {0, 1, 2}

RED_CROSS_RIVER_Y = 4
BLACK_CROSS_RIVER_Y = 5

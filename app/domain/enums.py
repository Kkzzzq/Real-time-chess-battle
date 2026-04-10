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


class MatchStatus(str, Enum):
    WAITING = "waiting"
    RUNNING = "running"
    ENDED = "ended"


ALL_PLAYERS = (1, 2)

from __future__ import annotations

from app.domain.enums import MatchStatus


_ALLOWED_ROOM_TRANSITIONS: dict[MatchStatus, set[MatchStatus]] = {
    MatchStatus.WAITING: {MatchStatus.RUNNING},
    MatchStatus.RUNNING: {MatchStatus.ENDED},
    MatchStatus.ENDED: set(),
}


class RoomStateMachine:
    @staticmethod
    def can_transition(current: MatchStatus, target: MatchStatus) -> bool:
        return target in _ALLOWED_ROOM_TRANSITIONS.get(current, set())

    @staticmethod
    def require_transition(current: MatchStatus, target: MatchStatus) -> None:
        if not RoomStateMachine.can_transition(current, target):
            raise ValueError(f"illegal room transition: {current.value} -> {target.value}")

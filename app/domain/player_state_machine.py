from __future__ import annotations

from enum import Enum


class PlayerLifecycle(str, Enum):
    JOINED = "joined"
    READY = "ready"
    RUNNING = "running"
    OFFLINE = "offline"
    LEFT = "left"
    RECONNECTED = "reconnected"


_ALLOWED_PLAYER_TRANSITIONS: dict[PlayerLifecycle, set[PlayerLifecycle]] = {
    PlayerLifecycle.JOINED: {PlayerLifecycle.READY, PlayerLifecycle.OFFLINE, PlayerLifecycle.LEFT},
    PlayerLifecycle.READY: {PlayerLifecycle.RUNNING, PlayerLifecycle.OFFLINE, PlayerLifecycle.LEFT},
    PlayerLifecycle.RUNNING: {PlayerLifecycle.OFFLINE, PlayerLifecycle.LEFT},
    PlayerLifecycle.OFFLINE: {PlayerLifecycle.RECONNECTED, PlayerLifecycle.LEFT},
    PlayerLifecycle.RECONNECTED: {PlayerLifecycle.RUNNING, PlayerLifecycle.READY, PlayerLifecycle.LEFT},
    PlayerLifecycle.LEFT: set(),
}


class PlayerStateMachine:
    @staticmethod
    def can_transition(current: PlayerLifecycle, target: PlayerLifecycle) -> bool:
        return target in _ALLOWED_PLAYER_TRANSITIONS.get(current, set())

    @staticmethod
    def require_transition(current: PlayerLifecycle, target: PlayerLifecycle) -> None:
        if not PlayerStateMachine.can_transition(current, target):
            raise ValueError(f"illegal player transition: {current.value} -> {target.value}")

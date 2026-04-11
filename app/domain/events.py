from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GameEvent:
    event_type: str
    ts_ms: int
    payload: dict[str, Any] = field(default_factory=dict)


EVENT_MATCH_CREATED = "match_created"
EVENT_PLAYER_JOINED = "player_joined"
EVENT_PLAYER_READY = "player_ready"
EVENT_PLAYER_LEFT = "player_left"
EVENT_PLAYER_OFFLINE = "player_offline"
EVENT_HOST_CHANGED = "host_changed"
EVENT_MATCH_STARTED = "match_started"
EVENT_PHASE_CHANGED = "phase_changed"
EVENT_UNLOCK_WINDOW_OPENED = "unlock_window_opened"
EVENT_UNLOCK_CHOSEN = "unlock_chosen"
EVENT_UNLOCK_AUTO_APPLIED = "unlock_auto_applied"
EVENT_MOVE_COMMAND_ACCEPTED = "move_command_accepted"
EVENT_MOVE_STARTED = "move_started"
EVENT_MOVE_PROGRESS = "move_progress"
EVENT_MOVE_FINISHED = "move_finished"
EVENT_CAPTURE = "capture"
EVENT_COOLDOWN_STARTED = "cooldown_started"
EVENT_PIECE_READY = "piece_ready"
EVENT_RESIGN = "resign"
EVENT_GAME_OVER = "game_over"
EVENT_DRAW = "draw"

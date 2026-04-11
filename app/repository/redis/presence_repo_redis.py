from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class RedisPresenceRepo:
    presence: dict[str, dict[str, dict]] = field(default_factory=dict)

    def mark_online(self, match_id: str, player_id: str) -> None:
        room = self.presence.setdefault(match_id, {})
        room[player_id] = {"online": True, "heartbeat_ms": int(time.time() * 1000)}

    def mark_offline(self, match_id: str, player_id: str) -> None:
        room = self.presence.setdefault(match_id, {})
        room[player_id] = {"online": False, "heartbeat_ms": int(time.time() * 1000)}

    def touch_heartbeat(self, match_id: str, player_id: str) -> None:
        room = self.presence.setdefault(match_id, {})
        item = room.setdefault(player_id, {"online": True, "heartbeat_ms": 0})
        item["heartbeat_ms"] = int(time.time() * 1000)

    def get_presence(self, match_id: str) -> dict[str, dict]:
        return dict(self.presence.get(match_id, {}))

    def get_active_players(self, match_id: str) -> list[str]:
        room = self.presence.get(match_id, {})
        return [player_id for player_id, meta in room.items() if meta.get("online")]

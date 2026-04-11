from __future__ import annotations

<<<<<<< HEAD
import json
import time

try:
    from redis import Redis
except Exception:  # pragma: no cover - optional dependency in dev env
    Redis = object  # type: ignore[misc,assignment]

from app.repository.redis.cache_keys import presence_key


class RedisPresenceRepo:
    def __init__(self, client: Redis):
        self.client = client

    def _load_presence(self, match_id: str) -> dict[str, dict]:
        raw = self.client.get(presence_key(match_id))
        if not raw:
            return {}
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        return json.loads(raw)

    def _save_presence(self, match_id: str, payload: dict[str, dict]) -> None:
        self.client.set(presence_key(match_id), json.dumps(payload, ensure_ascii=False))

    def mark_online(self, match_id: str, player_id: str) -> None:
        data = self._load_presence(match_id)
        data[player_id] = {"online": True, "heartbeat_ms": int(time.time() * 1000)}
        self._save_presence(match_id, data)

    def mark_offline(self, match_id: str, player_id: str) -> None:
        data = self._load_presence(match_id)
        data[player_id] = {"online": False, "heartbeat_ms": int(time.time() * 1000)}
        self._save_presence(match_id, data)

    def touch_heartbeat(self, match_id: str, player_id: str) -> None:
        data = self._load_presence(match_id)
        item = data.setdefault(player_id, {"online": True, "heartbeat_ms": 0})
        item["heartbeat_ms"] = int(time.time() * 1000)
        self._save_presence(match_id, data)

    def get_presence(self, match_id: str) -> dict[str, dict]:
        return self._load_presence(match_id)

    def get_active_players(self, match_id: str) -> list[str]:
        data = self._load_presence(match_id)
        return [pid for pid, meta in data.items() if meta.get("online")]
=======
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
>>>>>>> origin/main

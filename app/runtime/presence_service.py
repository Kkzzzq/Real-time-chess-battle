from __future__ import annotations

from dataclasses import dataclass

from app.repository.redis.presence_repo_redis import RedisPresenceRepo


@dataclass
class PresenceService:
    presence_repo: RedisPresenceRepo

    def on_ws_connected(self, match_id: str, player_id: str) -> None:
        self.presence_repo.mark_online(match_id, player_id)

    def on_ws_disconnected(self, match_id: str, player_id: str) -> None:
        self.presence_repo.mark_offline(match_id, player_id)

    def heartbeat(self, match_id: str, player_id: str) -> None:
        self.presence_repo.touch_heartbeat(match_id, player_id)

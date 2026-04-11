from __future__ import annotations

from dataclasses import dataclass

from app.domain.models import MatchState
from app.repository.base import MatchRepo
from app.repository.redis.presence_repo_redis import RedisPresenceRepo
from app.repository.redis.runtime_repo_redis import RedisRuntimeRepo


@dataclass
class PersistenceService:
    """Coordinates metadata persistence and runtime cache writes.

    Current implementation bridges legacy MatchRepo with Redis-style runtime repos.
    """

    match_repo: MatchRepo
    runtime_repo: RedisRuntimeRepo
    presence_repo: RedisPresenceRepo

    def on_match_created(self, state: MatchState) -> None:
        self.match_repo.save_match(state)
        self.runtime_repo.save_runtime_state(state.match_id, state.to_public_json())

    def on_player_joined(self, state: MatchState, player_id: str) -> None:
        self.match_repo.save_match(state)
        self.runtime_repo.save_runtime_state(state.match_id, state.to_public_json())
        self.presence_repo.mark_online(state.match_id, player_id)

    def on_match_updated(self, state: MatchState) -> None:
        self.match_repo.save_match(state)
        self.runtime_repo.save_runtime_state(state.match_id, state.to_public_json())

    def on_match_deleted(self, match_id: str) -> None:
        self.match_repo.delete_match(match_id)
        self.runtime_repo.delete_runtime_state(match_id)

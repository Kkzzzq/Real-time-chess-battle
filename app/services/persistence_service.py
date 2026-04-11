from __future__ import annotations

from dataclasses import dataclass
<<<<<<< HEAD
from typing import Any

from app.domain.models import MatchState
from app.engine.snapshot import build_match_snapshot
from app.repository.base import MatchRepo
=======

from app.domain.models import MatchState
from app.repository.base import MatchRepo
from app.repository.redis.presence_repo_redis import RedisPresenceRepo
from app.repository.redis.runtime_repo_redis import RedisRuntimeRepo
>>>>>>> origin/main


@dataclass
class PersistenceService:
<<<<<<< HEAD
    match_repo: MatchRepo
    runtime_repo: Any = None
    presence_repo: Any = None
    session_cache_repo: Any = None
    mysql_match_repo: Any = None
    mysql_player_repo: Any = None
    mysql_event_repo: Any = None
    mysql_session_repo: Any = None

    def persist_match_state(self, state: MatchState) -> None:
        self.match_repo.save_match(state)
        if self.runtime_repo is not None:
            self.runtime_repo.save_runtime_state(state.match_id, build_match_snapshot(state, state.now_ms))
        if self.mysql_match_repo is not None:
            self.mysql_match_repo.upsert_from_state(state)
        if self.mysql_player_repo is not None:
            self.mysql_player_repo.sync_players_from_state(state)

    def persist_session(self, *, match_id: str, player_id: str, token: str, issued_at_ms: int, expires_at_ms: int) -> None:
        ttl_seconds = max(1, (expires_at_ms - issued_at_ms) // 1000)
        payload = {
            "match_id": match_id,
            "player_id": player_id,
            "player_token": token,
            "issued_at_ms": issued_at_ms,
            "expires_at_ms": expires_at_ms,
        }
        if self.session_cache_repo is not None:
            self.session_cache_repo.put_session(player_id, payload, ttl_seconds)
        if self.mysql_session_repo is not None:
            self.mysql_session_repo.upsert_session(
                player_id=player_id,
                match_id=match_id,
                token_value=token,
                issued_at_ms=issued_at_ms,
                expires_at_ms=expires_at_ms,
            )

    def mark_online(self, match_id: str, player_id: str) -> None:
        if self.presence_repo is not None:
            self.presence_repo.mark_online(match_id, player_id)

    def mark_offline(self, match_id: str, player_id: str) -> None:
        if self.presence_repo is not None:
            self.presence_repo.mark_offline(match_id, player_id)

    def archive_incremental_events(self, state: MatchState, from_index: int) -> None:
        if self.mysql_event_repo is None:
            return
        for event in state.event_log[from_index:]:
            self.mysql_event_repo.append_event(state.match_id, event)
=======
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
>>>>>>> origin/main

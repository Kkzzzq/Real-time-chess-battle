from __future__ import annotations

from typing import Protocol

from app.domain.models import MatchState


class MatchMetaRepo(Protocol):
    """Persistent metadata for matches (status/timestamps/winner)."""

    def save_match_meta(self, state: MatchState) -> None: ...

    def get_match_meta(self, match_id: str) -> MatchState | None: ...

    def list_match_meta(self) -> list[MatchState]: ...

    def delete_match_meta(self, match_id: str) -> None: ...


class RuntimeStateRepo(Protocol):
    """High-frequency runtime state storage abstraction (Redis target)."""

    def save_runtime_state(self, state: MatchState) -> None: ...

    def get_runtime_state(self, match_id: str) -> MatchState | None: ...

    def delete_runtime_state(self, match_id: str) -> None: ...


class EventRepo(Protocol):
    """Archiveable event store abstraction."""

    def append_event(self, match_id: str, event_type: str, payload: dict) -> None: ...


class PlayerRepo(Protocol):
    """Player lifecycle data abstraction."""

    def upsert_players(self, state: MatchState) -> None: ...


class SessionRepo(Protocol):
    """Session persistence abstraction (token metadata)."""

    def upsert_session(self, *, player_id: str, match_id: str, token_value: str, issued_at_ms: int, expires_at_ms: int) -> None: ...

    def get_session(self, player_id: str): ...



class MatchRepo(Protocol):
    """Legacy all-in-one repository interface used by current services.

    Kept for backward compatibility while moving toward split repos.
    """

    def save_match(self, state: MatchState) -> None: ...

    def get_match(self, match_id: str) -> MatchState | None: ...

    def list_matches(self) -> list[MatchState]: ...

    def delete_match(self, match_id: str) -> None: ...

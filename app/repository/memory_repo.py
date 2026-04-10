from __future__ import annotations

from app.domain.models import MatchState


class MemoryRepo:
    def __init__(self) -> None:
        self._matches: dict[str, MatchState] = {}

    def save_match(self, state: MatchState) -> None:
        self._matches[state.match_id] = state

    def get_match(self, match_id: str) -> MatchState | None:
        return self._matches.get(match_id)

    def list_matches(self) -> list[MatchState]:
        return list(self._matches.values())

    def delete_match(self, match_id: str) -> None:
        self._matches.pop(match_id, None)

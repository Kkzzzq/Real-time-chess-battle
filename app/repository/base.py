from __future__ import annotations

from typing import Protocol

from app.domain.models import MatchState


class MatchRepo(Protocol):
    def save_match(self, state: MatchState) -> None: ...

    def get_match(self, match_id: str) -> MatchState | None: ...

    def list_matches(self) -> list[MatchState]: ...

    def delete_match(self, match_id: str) -> None: ...

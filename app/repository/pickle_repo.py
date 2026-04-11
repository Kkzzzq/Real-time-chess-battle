from __future__ import annotations

import pickle
from pathlib import Path

from app.domain.models import MatchState


class PickleRepo:
    def __init__(self, path: str = '.data/matches.pkl') -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._matches: dict[str, MatchState] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            with self.path.open('rb') as f:
                data = pickle.load(f)
                if isinstance(data, dict):
                    self._matches = data
        except Exception:
            self._matches = {}

    def _flush(self) -> None:
        with self.path.open('wb') as f:
            pickle.dump(self._matches, f)

    def save_match(self, state: MatchState) -> None:
        self._matches[state.match_id] = state
        self._flush()

    def get_match(self, match_id: str) -> MatchState | None:
        return self._matches.get(match_id)

    def list_matches(self) -> list[MatchState]:
        return list(self._matches.values())

    def delete_match(self, match_id: str) -> None:
        self._matches.pop(match_id, None)
        self._flush()

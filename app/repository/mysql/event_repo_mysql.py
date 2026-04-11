from __future__ import annotations

from dataclasses import dataclass, field

from app.repository.mysql.models import MatchEventRecord


@dataclass
class MySQLEventRepo:
    events_by_match: dict[str, list[MatchEventRecord]] = field(default_factory=dict)

    def append_event(self, event: MatchEventRecord) -> None:
        self.events_by_match.setdefault(event.match_id, []).append(event)

    def list_events(self, match_id: str) -> list[MatchEventRecord]:
        return list(self.events_by_match.get(match_id, []))

    def archive_match_events(self, match_id: str) -> int:
        return len(self.events_by_match.get(match_id, []))

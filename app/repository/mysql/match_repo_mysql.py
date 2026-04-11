from __future__ import annotations

from dataclasses import dataclass, field

from app.repository.mysql.models import MatchRecord


@dataclass
class MySQLMatchRepo:
    """In-memory scaffold that mirrors expected MySQL repository methods."""

    records: dict[str, MatchRecord] = field(default_factory=dict)

    def create_match_record(self, record: MatchRecord) -> None:
        self.records[record.match_id] = record

    def get_match_record(self, match_id: str) -> MatchRecord | None:
        return self.records.get(match_id)

    def update_match_status(self, match_id: str, status: str) -> None:
        rec = self.records.get(match_id)
        if rec is not None:
            rec.status = status

    def finish_match(self, match_id: str, winner: int | None, reason: str | None) -> None:
        rec = self.records.get(match_id)
        if rec is not None:
            rec.status = "ended"

    def list_matches(self) -> list[MatchRecord]:
        return list(self.records.values())

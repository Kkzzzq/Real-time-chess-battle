from __future__ import annotations

<<<<<<< HEAD
import json

from sqlalchemy.orm import Session

from app.domain.enums import MatchStatus
from app.domain.models import MatchState
from app.repository.mysql.models import MatchRecord


class MySQLMatchRepo:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def upsert_from_state(self, state: MatchState) -> None:
        with self.session_factory() as db:
            rec = db.get(MatchRecord, state.match_id)
            if rec is None:
                rec = MatchRecord(match_id=state.match_id, created_at=state.created_at, ruleset_name=state.ruleset_name, status=state.status.value)
                db.add(rec)
            rec.status = state.status.value
            rec.ruleset_name = state.ruleset_name
            rec.started_at = state.started_at
            rec.ended_at = state.now_ms if state.status == MatchStatus.ENDED else rec.ended_at
            rec.winner = state.winner
            rec.result_reason = state.reason
            rec.allow_draw = state.allow_draw
            rec.tick_ms = state.tick_ms
            rec.host_player_id = state.host_player_id
            rec.ruleset_snapshot_json = json.dumps(
                {
                    "ruleset_name": state.ruleset_name,
                    "allow_draw": state.allow_draw,
                    "tick_ms": state.tick_ms,
                    "custom_unlock_windows": state.custom_unlock_windows,
                },
                ensure_ascii=False,
            )
            db.commit()

    def get_match_record(self, match_id: str) -> MatchRecord | None:
        with self.session_factory() as db:
            return db.get(MatchRecord, match_id)

    def update_match_status(self, match_id: str, status: str) -> None:
        with self.session_factory() as db:
            rec = db.get(MatchRecord, match_id)
            if rec is None:
                return
            rec.status = status
            db.commit()

    def list_matches(self, db: Session | None = None) -> list[MatchRecord]:
        if db is not None:
            return list(db.query(MatchRecord).all())
        with self.session_factory() as session:
            return list(session.query(MatchRecord).all())
=======
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
>>>>>>> origin/main

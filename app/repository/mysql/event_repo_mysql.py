from __future__ import annotations

import json

from app.domain.events import GameEvent
from app.repository.mysql.models import MatchEventRecord


class MySQLEventRepo:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def append_event(self, match_id: str, event: GameEvent) -> None:
        with self.session_factory() as db:
            db.add(
                MatchEventRecord(
                    match_id=match_id,
                    event_type=event.event_type,
                    ts_ms=event.ts_ms,
                    payload_json=json.dumps(event.payload, ensure_ascii=False),
                )
            )
            db.commit()

    def append_many(self, match_id: str, events: list[GameEvent]) -> None:
        if not events:
            return
        with self.session_factory() as db:
            for event in events:
                db.add(
                    MatchEventRecord(
                        match_id=match_id,
                        event_type=event.event_type,
                        ts_ms=event.ts_ms,
                        payload_json=json.dumps(event.payload, ensure_ascii=False),
                    )
                )
            db.commit()

    def list_events(self, match_id: str, limit: int = 200) -> list[MatchEventRecord]:
        with self.session_factory() as db:
            q = db.query(MatchEventRecord).filter(MatchEventRecord.match_id == match_id).order_by(MatchEventRecord.id.desc()).limit(limit)
            return list(reversed(q.all()))

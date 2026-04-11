from __future__ import annotations

from dataclasses import dataclass

from app.domain.models import MatchState
from app.repository.mysql.event_repo_mysql import MySQLEventRepo
from app.repository.mysql.match_repo_mysql import MySQLMatchRepo
from app.repository.mysql.models import MatchEventRecord


@dataclass
class MatchArchiveService:
    match_repo: MySQLMatchRepo
    event_repo: MySQLEventRepo

    def archive_finished_match(self, state: MatchState) -> int:
        rec = self.match_repo.get_match_record(state.match_id)
        if rec is not None:
            self.match_repo.finish_match(state.match_id, state.winner, state.result_reason)
        for event in state.event_log:
            self.event_repo.append_event(
                MatchEventRecord(
                    match_id=state.match_id,
                    event_type=event.type,
                    ts_ms=event.ts_ms,
                    payload_json=str(event.payload),
                )
            )
        return len(state.event_log)

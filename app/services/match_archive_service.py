from __future__ import annotations

from dataclasses import dataclass

from app.domain.models import MatchState
from app.repository.mysql.event_repo_mysql import MySQLEventRepo
from app.repository.mysql.match_repo_mysql import MySQLMatchRepo
from app.repository.mysql.player_repo_mysql import MySQLPlayerRepo


@dataclass
class MatchArchiveService:
    match_repo: MySQLMatchRepo
    event_repo: MySQLEventRepo
    player_repo: MySQLPlayerRepo

    def archive_finished_match(self, state: MatchState) -> int:
        self.match_repo.upsert_from_state(state)
        self.player_repo.sync_players_from_state(state)
        self.event_repo.append_many(state.match_id, state.event_log)
        return len(state.event_log)

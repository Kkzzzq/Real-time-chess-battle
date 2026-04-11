from __future__ import annotations

from dataclasses import dataclass, field

from app.repository.mysql.models import PlayerSessionRecord


@dataclass
class MySQLSessionRepo:
    sessions: dict[str, PlayerSessionRecord] = field(default_factory=dict)

    def upsert_session(self, session: PlayerSessionRecord) -> None:
        self.sessions[session.player_id] = session

    def get_session(self, player_id: str) -> PlayerSessionRecord | None:
        return self.sessions.get(player_id)

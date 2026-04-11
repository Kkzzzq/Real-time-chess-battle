from __future__ import annotations

from app.domain.models import MatchState
from app.repository.mysql.models import PlayerRecord


class MySQLPlayerRepo:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def sync_players_from_state(self, state: MatchState) -> None:
        with self.session_factory() as db:
            db.query(PlayerRecord).filter(PlayerRecord.match_id == state.match_id).delete(synchronize_session=False)
            for seat, info in state.players.items():
                db.add(
                    PlayerRecord(
                        player_id=str(info.get("player_id")),
                        match_id=state.match_id,
                        seat=int(seat),
                        name=str(info.get("name", "player")),
                        is_host=state.host_seat == seat,
                        ready=bool(info.get("ready", False)),
                        online=bool(info.get("online", False)),
                        joined_at=state.created_at,
                        left_at=None,
                    )
                )
            db.commit()

    def list_players_by_match(self, match_id: str) -> list[PlayerRecord]:
        with self.session_factory() as db:
            return list(db.query(PlayerRecord).filter(PlayerRecord.match_id == match_id).order_by(PlayerRecord.seat.asc()).all())

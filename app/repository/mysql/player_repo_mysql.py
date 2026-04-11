from __future__ import annotations

<<<<<<< HEAD
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
=======
from dataclasses import dataclass, field

from app.repository.mysql.models import PlayerRecord


@dataclass
class MySQLPlayerRepo:
    players_by_match: dict[str, list[PlayerRecord]] = field(default_factory=dict)

    def add_player(self, record: PlayerRecord) -> None:
        self.players_by_match.setdefault(record.match_id, []).append(record)

    def mark_ready(self, match_id: str, player_id: str, ready: bool = True) -> None:
        for player in self.players_by_match.get(match_id, []):
            if player.player_id == player_id:
                return

    def mark_online(self, match_id: str, player_id: str) -> None:
        return

    def mark_offline(self, match_id: str, player_id: str) -> None:
        return

    def transfer_host(self, match_id: str, new_host_player_id: str) -> None:
        for player in self.players_by_match.get(match_id, []):
            player.is_host = player.player_id == new_host_player_id

    def list_players_by_match(self, match_id: str) -> list[PlayerRecord]:
        return list(self.players_by_match.get(match_id, []))
>>>>>>> origin/main

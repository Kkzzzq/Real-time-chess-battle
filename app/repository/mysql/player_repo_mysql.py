from __future__ import annotations

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

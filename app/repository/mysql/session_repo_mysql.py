from __future__ import annotations

from app.repository.mysql.models import PlayerSessionRecord


class MySQLSessionRepo:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def upsert_session(self, *, player_id: str, match_id: str, token_value: str, issued_at_ms: int, expires_at_ms: int) -> None:
        with self.session_factory() as db:
            rec = db.get(PlayerSessionRecord, player_id)
            if rec is None:
                rec = PlayerSessionRecord(
                    player_id=player_id,
                    match_id=match_id,
                    token_value=token_value,
                    issued_at_ms=issued_at_ms,
                    expires_at_ms=expires_at_ms,
                )
                db.add(rec)
            else:
                rec.match_id = match_id
                rec.token_value = token_value
                rec.issued_at_ms = issued_at_ms
                rec.expires_at_ms = expires_at_ms
            db.commit()

    def get_session(self, player_id: str) -> PlayerSessionRecord | None:
        with self.session_factory() as db:
            return db.get(PlayerSessionRecord, player_id)

    def revoke_session(self, player_id: str) -> None:
        with self.session_factory() as db:
            db.query(PlayerSessionRecord).filter(PlayerSessionRecord.player_id == player_id).delete(synchronize_session=False)
            db.commit()

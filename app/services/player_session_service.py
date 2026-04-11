from __future__ import annotations

import secrets
import time
import uuid
from dataclasses import dataclass

from app.services.persistence_service import PersistenceService


@dataclass(frozen=True)
class PlayerSession:
    player_id: str
    player_token: str
    player_token_expires_at: int
    issued_at_ms: int


class PlayerSessionService:
    def __init__(self, token_ttl_seconds: int, persistence_service: PersistenceService | None = None) -> None:
        self.token_ttl_seconds = token_ttl_seconds
        self.persistence_service = persistence_service

    def issue_session(self, match_id: str, now_ms: int | None = None) -> PlayerSession:
        ts = now_ms if now_ms is not None else int(time.time() * 1000)
        session = PlayerSession(
            player_id=uuid.uuid4().hex[:8],
            player_token=secrets.token_urlsafe(24),
            player_token_expires_at=ts + self.token_ttl_seconds * 1000,
            issued_at_ms=ts,
        )
        if self.persistence_service is not None:
            self.persistence_service.persist_session(
                match_id=match_id,
                player_id=session.player_id,
                token=session.player_token,
                issued_at_ms=session.issued_at_ms,
                expires_at_ms=session.player_token_expires_at,
            )
        return session

    def validate_session(
        self,
        *,
        match_id: str,
        player_id: str,
        token: str,
        expected_token: str,
        expires_at: int | None,
        now_ms: int | None = None,
    ) -> None:
        if token != expected_token:
            raise ValueError("player auth failed")
        ts = now_ms if now_ms is not None else int(time.time() * 1000)
        if expires_at is not None and ts > int(expires_at):
            raise ValueError("player token expired")

        if self.persistence_service and self.persistence_service.session_cache_repo:
            cached = self.persistence_service.session_cache_repo.get_session(player_id)
            if cached is not None and cached.get("match_id") != match_id:
                raise ValueError("player session mismatch")

    def rotate_session(self, match_id: str, player_id: str, now_ms: int | None = None) -> PlayerSession:
        ts = now_ms if now_ms is not None else int(time.time() * 1000)
        rotated = PlayerSession(
            player_id=player_id,
            player_token=secrets.token_urlsafe(24),
            player_token_expires_at=ts + self.token_ttl_seconds * 1000,
            issued_at_ms=ts,
        )
        if self.persistence_service is not None:
            self.persistence_service.persist_session(
                match_id=match_id,
                player_id=player_id,
                token=rotated.player_token,
                issued_at_ms=rotated.issued_at_ms,
                expires_at_ms=rotated.player_token_expires_at,
            )
        return rotated

    def revoke_session(self, player_id: str) -> None:
        if self.persistence_service and self.persistence_service.session_cache_repo:
            self.persistence_service.session_cache_repo.invalidate_session(player_id)
        if self.persistence_service and self.persistence_service.mysql_session_repo:
            self.persistence_service.mysql_session_repo.revoke_session(player_id)

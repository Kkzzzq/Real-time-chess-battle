from __future__ import annotations

import secrets
import time
import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class PlayerSession:
    player_id: str
    player_token: str
    player_token_expires_at: int


class PlayerSessionService:
    def __init__(self, token_ttl_seconds: int) -> None:
        self.token_ttl_seconds = token_ttl_seconds

    def issue(self, now_ms: int | None = None) -> PlayerSession:
        ts = now_ms if now_ms is not None else int(time.time() * 1000)
        return PlayerSession(
            player_id=uuid.uuid4().hex[:8],
            player_token=secrets.token_urlsafe(24),
            player_token_expires_at=ts + self.token_ttl_seconds * 1000,
        )

    def validate(self, *, token: str, expected_token: str, expires_at: int | None, now_ms: int | None = None) -> None:
        if token != expected_token:
            raise ValueError("player auth failed")
        ts = now_ms if now_ms is not None else int(time.time() * 1000)
        if expires_at is not None and ts > int(expires_at):
            raise ValueError("player token expired")

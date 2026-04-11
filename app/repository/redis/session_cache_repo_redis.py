from __future__ import annotations

import json

try:
    from redis import Redis
except Exception:  # pragma: no cover - optional dependency in dev env
    Redis = object  # type: ignore[misc,assignment]

from app.repository.redis.cache_keys import player_session_key


class RedisSessionCacheRepo:
    def __init__(self, client: Redis):
        self.client = client

    def put_session(self, player_id: str, session_payload: dict, ttl_seconds: int) -> None:
        self.client.setex(player_session_key(player_id), ttl_seconds, json.dumps(session_payload, ensure_ascii=False))

    def get_session(self, player_id: str) -> dict | None:
        raw = self.client.get(player_session_key(player_id))
        if not raw:
            return None
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        return json.loads(raw)

    def invalidate_session(self, player_id: str) -> None:
        self.client.delete(player_session_key(player_id))

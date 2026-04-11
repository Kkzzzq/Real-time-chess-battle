from __future__ import annotations

import json

try:
    from redis import Redis
except Exception:  # pragma: no cover - optional dependency in dev env
    Redis = object  # type: ignore[misc,assignment]

from app.repository.redis.cache_keys import runtime_state_key


class RedisRuntimeRepo:
    def __init__(self, client: Redis):
        self.client = client

    def load_runtime_state(self, match_id: str) -> dict | None:
        raw = self.client.get(runtime_state_key(match_id))
        if not raw:
            return None
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        return json.loads(raw)

    def save_runtime_state(self, match_id: str, snapshot: dict) -> None:
        self.client.set(runtime_state_key(match_id), json.dumps(snapshot, ensure_ascii=False))

    def delete_runtime_state(self, match_id: str) -> None:
        self.client.delete(runtime_state_key(match_id))

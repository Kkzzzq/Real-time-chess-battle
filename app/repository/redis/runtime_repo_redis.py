from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RedisRuntimeRepo:
    """In-memory scaffold mimicking Redis runtime operations."""

    snapshots: dict[str, dict] = field(default_factory=dict)

    def load_runtime_state(self, match_id: str) -> dict | None:
        return self.snapshots.get(match_id)

    def save_runtime_state(self, match_id: str, snapshot: dict) -> None:
        self.snapshots[match_id] = snapshot

    def delete_runtime_state(self, match_id: str) -> None:
        self.snapshots.pop(match_id, None)

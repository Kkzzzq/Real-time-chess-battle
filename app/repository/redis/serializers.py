from __future__ import annotations

import json
from typing import Any

from app.domain.models import MatchState
from app.engine.snapshot import build_match_snapshot


class RuntimeStateSerializer:
    @staticmethod
    def dumps(state: MatchState) -> str:
        return json.dumps(build_match_snapshot(state, state.now_ms), ensure_ascii=False)

    @staticmethod
    def dumps_snapshot(snapshot: dict[str, Any]) -> str:
        return json.dumps(snapshot, ensure_ascii=False)

    @staticmethod
    def dumps_event(event_type: str, payload: dict[str, Any]) -> str:
        return json.dumps({"type": event_type, "payload": payload}, ensure_ascii=False)

from __future__ import annotations

import json
from typing import Any

from app.domain.models import MatchState
<<<<<<< HEAD
from app.engine.snapshot import build_match_snapshot
=======
>>>>>>> origin/main


class RuntimeStateSerializer:
    @staticmethod
    def dumps(state: MatchState) -> str:
<<<<<<< HEAD
        return json.dumps(build_match_snapshot(state, state.now_ms), ensure_ascii=False)

    @staticmethod
    def dumps_snapshot(snapshot: dict[str, Any]) -> str:
        return json.dumps(snapshot, ensure_ascii=False)
=======
        return json.dumps(state.to_public_json(), ensure_ascii=False)
>>>>>>> origin/main

    @staticmethod
    def dumps_event(event_type: str, payload: dict[str, Any]) -> str:
        return json.dumps({"type": event_type, "payload": payload}, ensure_ascii=False)

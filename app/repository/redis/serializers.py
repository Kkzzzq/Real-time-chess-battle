from __future__ import annotations

import json
from typing import Any

from app.domain.models import MatchState


class RuntimeStateSerializer:
    @staticmethod
    def dumps(state: MatchState) -> str:
        return json.dumps(state.to_public_json(), ensure_ascii=False)

    @staticmethod
    def dumps_event(event_type: str, payload: dict[str, Any]) -> str:
        return json.dumps({"type": event_type, "payload": payload}, ensure_ascii=False)

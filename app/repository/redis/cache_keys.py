from __future__ import annotations


def runtime_state_key(match_id: str) -> str:
    return f"rtcb:match:{match_id}:runtime"


def presence_key(match_id: str) -> str:
    return f"rtcb:match:{match_id}:presence"


def event_stream_key(match_id: str) -> str:
    return f"rtcb:match:{match_id}:events"


def player_session_key(player_id: str) -> str:
    return f"rtcb:player:{player_id}:session"

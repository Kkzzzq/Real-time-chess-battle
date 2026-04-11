from __future__ import annotations

"""Database metadata placeholders for the MySQL repository layer.

This project currently runs with Memory/Pickle repos. These definitions provide
an explicit module boundary for future SQLAlchemy integration.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class DBTable:
    name: str


MATCH_RECORD = DBTable(name="match_records")
PLAYER_RECORD = DBTable(name="player_records")
MATCH_EVENT_RECORD = DBTable(name="match_event_records")
PLAYER_SESSION_RECORD = DBTable(name="player_session_records")

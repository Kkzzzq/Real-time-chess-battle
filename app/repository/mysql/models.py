from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MatchRecord:
    match_id: str
    status: str
    ruleset_name: str


@dataclass
class PlayerRecord:
    player_id: str
    match_id: str
    seat: int
    is_host: bool


@dataclass
class MatchEventRecord:
    match_id: str
    event_type: str
    ts_ms: int
    payload_json: str


@dataclass
class PlayerSessionRecord:
    player_id: str
    match_id: str
    token_hash: str
    expires_at_ms: int

from __future__ import annotations

import secrets
import time
import uuid

from app.domain.enums import MatchStatus, PieceType
from app.domain.events import (
    EVENT_HOST_CHANGED,
    EVENT_MATCH_CREATED,
    EVENT_MATCH_STARTED,
    EVENT_PLAYER_JOINED,
    EVENT_PLAYER_LEFT,
    EVENT_PLAYER_OFFLINE,
    EVENT_PLAYER_READY,
    GameEvent,
)
from app.domain.models import MatchState
from app.engine.board_setup import create_standard_board
from app.repository.memory_repo import MemoryRepo


class RoomService:
    def __init__(self, repo: MemoryRepo) -> None:
        self.repo = repo

    def create_match(
        self,
        ruleset_name: str = "standard",
        allow_draw: bool = True,
        tick_ms: int = 100,
        custom_unlock_windows: list[int] | None = None,
    ) -> MatchState:
        if ruleset_name != "standard":
            raise ValueError("unsupported ruleset_name, only 'standard' is currently supported")
        if custom_unlock_windows is not None:
            normalized = sorted(set(custom_unlock_windows))
            if len(normalized) != len(custom_unlock_windows):
                raise ValueError("custom_unlock_windows must not contain duplicates")
            if len(normalized) == 0:
                raise ValueError("custom_unlock_windows must not be empty")
            if any(w < 0 or w >= 130 for w in normalized):
                raise ValueError("custom_unlock_windows must be within [0, 129]")
            custom_unlock_windows = normalized

        now = int(time.time() * 1000)
        state = MatchState(
            match_id=uuid.uuid4().hex[:12],
            created_at=now,
            now_ms=now,
            pieces=create_standard_board(),
            unlocked_by_player={1: {PieceType.SOLDIER}, 2: {PieceType.SOLDIER}},
            ruleset_name=ruleset_name,
            allow_draw=allow_draw,
            tick_ms=tick_ms,
            custom_unlock_windows=custom_unlock_windows,
        )
        state.add_event(GameEvent(EVENT_MATCH_CREATED, now, {"match_id": state.match_id}))
        self.repo.save_match(state)
        return state

    def join_match(self, match_id: str, player_name: str) -> dict:
        now_ms = int(time.time() * 1000)
        state = self.repo.get_match(match_id)
        if state is None:
            raise ValueError("match not found")
        if state.status != MatchStatus.WAITING:
            raise ValueError("match already started")
        seat = 1 if 1 not in state.players else 2
        if seat in state.players:
            raise ValueError("match full")
        player = {
            "player_id": uuid.uuid4().hex[:8],
            "player_token": secrets.token_urlsafe(24),
            "name": player_name,
            "ready": False,
            "online": True,
            "is_host": len(state.players) == 0,
        }
        state.players[seat] = player
        state.now_ms = now_ms
        state.add_event(GameEvent(EVENT_PLAYER_JOINED, now_ms, {"seat": seat, "name": player_name}))
        self.repo.save_match(state)
        return {"seat": seat, "player_id": player["player_id"], "player_token": player["player_token"], **player}

    def reconnect_match(self, match_id: str, player_id: str, player_token: str) -> dict:
        state = self.repo.get_match(match_id)
        if state is None:
            raise ValueError("match not found")
        now_ms = int(time.time() * 1000)
        for seat, info in state.players.items():
            if info.get("player_id") == player_id and info.get("player_token") == player_token:
                info["online"] = True
                state.now_ms = now_ms
                self.repo.save_match(state)
                return {
                    "seat": seat,
                    "player_id": info.get("player_id"),
                    "player_token": info.get("player_token"),
                    "name": info.get("name"),
                    "ready": bool(info.get("ready", False)),
                    "online": bool(info.get("online", False)),
                    "is_host": bool(info.get("is_host", False)),
                }
        raise ValueError("player auth failed")

    def _reassign_host_if_needed(self, state: MatchState, now_ms: int) -> None:
        hosts = [s for s, info in state.players.items() if info.get("is_host")]
        if hosts:
            return
        if not state.players:
            return
        new_host = sorted(state.players.keys())[0]
        state.players[new_host]["is_host"] = True
        state.add_event(GameEvent(EVENT_HOST_CHANGED, now_ms, {"seat": new_host}))

    def leave_match(self, match_id: str, player_id: str) -> MatchState:
        state = self.repo.get_match(match_id)
        if not state:
            raise ValueError("match not found")
        now_ms = int(time.time() * 1000)

        for seat, info in list(state.players.items()):
            if info.get("player_id") != player_id:
                continue
            if state.status == MatchStatus.WAITING:
                was_host = bool(info.get("is_host"))
                del state.players[seat]
                state.add_event(GameEvent(EVENT_PLAYER_LEFT, now_ms, {"seat": seat, "player_id": player_id}))
                if was_host:
                    self._reassign_host_if_needed(state, now_ms)
            else:
                info["online"] = False
                state.add_event(GameEvent(EVENT_PLAYER_OFFLINE, now_ms, {"seat": seat, "player_id": player_id}))
            if not state.players:
                self.repo.delete_match(match_id)
                return state
            self.repo.save_match(state)
            return state
        raise ValueError("player not in match")

    def ready_match(self, match_id: str, player_id: str) -> MatchState:
        state = self.repo.get_match(match_id)
        if not state:
            raise ValueError("match not found")
        now_ms = int(time.time() * 1000)
        for seat, info in state.players.items():
            if info.get("player_id") == player_id:
                if info.get("ready"):
                    raise ValueError("already ready")
                info["ready"] = True
                state.add_event(GameEvent(EVENT_PLAYER_READY, now_ms, {"seat": seat, "player_id": player_id}))
                self.repo.save_match(state)
                return state
        raise ValueError("player not found")

    def start_match(self, match_id: str) -> MatchState:
        state = self.repo.get_match(match_id)
        if not state:
            raise ValueError("match not found")
        if state.status == MatchStatus.RUNNING:
            raise ValueError("match already running")
        if state.status == MatchStatus.ENDED:
            raise ValueError("match already ended")
        if len(state.players) < 2:
            raise ValueError("need two players")
        if not all(p.get("ready") for p in state.players.values()):
            raise ValueError("players not ready")
        now = int(time.time() * 1000)
        state.started_at = now
        state.now_ms = now
        state.status = MatchStatus.RUNNING
        state.last_action_at = now
        state.last_capture_at = now
        state.add_event(GameEvent(EVENT_MATCH_STARTED, now, {}))
        self.repo.save_match(state)
        return state

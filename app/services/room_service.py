from __future__ import annotations

import logging
import os
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
from app.repository.base import MatchRepo


logger = logging.getLogger(__name__)
TOKEN_TTL_SECONDS = int(os.getenv("PLAYER_TOKEN_TTL_SECONDS", "86400"))


TOKEN_TTL_SECONDS = int(os.getenv("PLAYER_TOKEN_TTL_SECONDS", "86400"))

class RoomService:
    def __init__(self, repo: MatchRepo) -> None:
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
            if any(w < 50 or w >= 130 for w in normalized):
                raise ValueError("custom_unlock_windows must be within [50, 129]")
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
        logger.info("audit action=create_match match_id=%s ruleset=%s", state.match_id, ruleset_name)
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
        expires_at = now_ms + TOKEN_TTL_SECONDS * 1000
        player = {
            "player_id": uuid.uuid4().hex[:8],
            "player_token": secrets.token_urlsafe(24),
            "player_token_expires_at": expires_at,
            "name": player_name,
            "ready": False,
            "online": True,
        }
        state.players[seat] = player
        if state.host_seat is None:
            state.host_seat = seat
            state.creator_player_id = player["player_id"]
        state.now_ms = now_ms
        state.add_event(GameEvent(EVENT_PLAYER_JOINED, now_ms, {"seat": seat, "name": player_name}))
        self.repo.save_match(state)
        logger.info("audit action=join match_id=%s seat=%s player_id=%s", match_id, seat, player["player_id"])
        return {"seat": seat, "player_id": player["player_id"], "player_token": player["player_token"], "player_token_expires_at": expires_at, **player}

    def reconnect_match(self, match_id: str, player_id: str, player_token: str) -> dict:
        state = self.repo.get_match(match_id)
        if state is None:
            raise ValueError("match not found")
        now_ms = int(time.time() * 1000)
        for seat, info in state.players.items():
            if info.get("player_id") == player_id and info.get("player_token") == player_token:
                exp = info.get("player_token_expires_at")
                if exp is not None and now_ms > int(exp):
                    raise ValueError("player token expired")
                info["online"] = True
                state.now_ms = now_ms
                self.repo.save_match(state)
                logger.info("audit action=reconnect match_id=%s seat=%s player_id=%s", match_id, seat, player_id)
                return {
                    "seat": seat,
                    "player_id": info.get("player_id"),
                    "player_token": info.get("player_token"),
                    "player_token_expires_at": info.get("player_token_expires_at"),
                    "name": info.get("name"),
                    "ready": bool(info.get("ready", False)),
                    "online": bool(info.get("online", False)),
                    "is_host": state.host_seat == seat,
                }
        raise ValueError("player auth failed")

    def _reassign_host_if_needed(self, state: MatchState, now_ms: int) -> None:
        if state.host_seat in state.players:
            return
        if not state.players:
            state.host_seat = None
            return
        new_host = sorted(state.players.keys())[0]
        state.host_seat = new_host
        state.add_event(GameEvent(EVENT_HOST_CHANGED, now_ms, {"seat": new_host}))
        logger.info("audit action=host_changed match_id=%s new_host_seat=%s", state.match_id, new_host)

    def leave_match(self, match_id: str, player_id: str) -> MatchState:
        state = self.repo.get_match(match_id)
        if not state:
            raise ValueError("match not found")
        now_ms = int(time.time() * 1000)

        for seat, info in list(state.players.items()):
            if info.get("player_id") != player_id:
                continue
            if state.status == MatchStatus.WAITING:
                del state.players[seat]
                state.add_event(GameEvent(EVENT_PLAYER_LEFT, now_ms, {"seat": seat, "player_id": player_id}))
                self._reassign_host_if_needed(state, now_ms)
            else:
                info["online"] = False
                state.add_event(GameEvent(EVENT_PLAYER_OFFLINE, now_ms, {"seat": seat, "player_id": player_id}))
            if not state.players:
                self.repo.delete_match(match_id)
                logger.info("audit action=leave_delete_room match_id=%s player_id=%s", match_id, player_id)
                return state
            self.repo.save_match(state)
            logger.info("audit action=leave match_id=%s seat=%s player_id=%s", match_id, seat, player_id)
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
                logger.info("audit action=ready match_id=%s seat=%s player_id=%s", match_id, seat, player_id)
                return state
        raise ValueError("player not found")

    def start_match(self, match_id: str, requester_player_id: str) -> MatchState:
        state = self.repo.get_match(match_id)
        if not state:
            raise ValueError("match not found")
        requester_seat = None
        for seat, info in state.players.items():
            if info.get("player_id") == requester_player_id:
                requester_seat = seat
                if not info.get("online", True):
                    raise ValueError("player offline")
                if state.host_seat != seat:
                    raise ValueError("only host can start")
                break
        if requester_seat is None:
            raise ValueError("player not found")
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
        logger.info("audit action=start match_id=%s by_player_id=%s host_seat=%s", match_id, requester_player_id, state.host_seat)
        return state

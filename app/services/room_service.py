from __future__ import annotations

import logging
import os
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
from app.domain.player_state_machine import PlayerLifecycle, PlayerStateMachine
from app.domain.room_state_machine import RoomStateMachine
from app.engine.board_setup import create_standard_board
from app.repository.base import MatchRepo
from app.services.persistence_service import PersistenceService
from app.services.player_session_service import PlayerSessionService

logger = logging.getLogger(__name__)
TOKEN_TTL_SECONDS = int(os.getenv("PLAYER_TOKEN_TTL_SECONDS", "86400"))


class RoomService:
    def __init__(
        self,
        repo: MatchRepo,
        session_service: PlayerSessionService | None = None,
        persistence_service: PersistenceService | None = None,
    ) -> None:
        self.repo = repo
        self.persistence_service = persistence_service
        self.session_service = session_service or PlayerSessionService(TOKEN_TTL_SECONDS, persistence_service=persistence_service)

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
        self._persist(state)
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
        issued = self.session_service.issue_session(match_id=match_id, now_ms=now_ms)
        player = {
            "player_id": issued.player_id,
            "player_token": issued.player_token,
            "player_token_expires_at": issued.player_token_expires_at,
            "name": player_name,
            "ready": False,
            "online": True,
            "lifecycle": PlayerLifecycle.JOINED.value,
        }
        state.players[seat] = player
        if state.host_seat is None:
            state.host_seat = seat
            state.host_player_id = player["player_id"]
            state.creator_player_id = player["player_id"]
        state.now_ms = now_ms
        state.add_event(GameEvent(EVENT_PLAYER_JOINED, now_ms, {"seat": seat, "name": player_name}))
        self._persist(state)
        if self.persistence_service is not None:
            self.persistence_service.mark_online(match_id, player["player_id"])
        logger.info("audit action=join match_id=%s seat=%s player_id=%s", match_id, seat, player["player_id"])
        return self._build_player_join_payload(state, seat)

    def reconnect_match(self, match_id: str, player_id: str, player_token: str) -> dict:
        state = self.repo.get_match(match_id)
        if state is None:
            raise ValueError("match not found")
        now_ms = int(time.time() * 1000)
        for seat, info in state.players.items():
            if info.get("player_id") == player_id and info.get("player_token") == player_token:
                self.session_service.validate_session(
                    match_id=match_id,
                    player_id=player_id,
                    token=player_token,
                    expected_token=str(info.get("player_token", "")),
                    expires_at=info.get("player_token_expires_at"),
                    now_ms=now_ms,
                )
                lifecycle = PlayerLifecycle(info.get("lifecycle", PlayerLifecycle.JOINED.value))
                if lifecycle == PlayerLifecycle.OFFLINE:
                    PlayerStateMachine.require_transition(lifecycle, PlayerLifecycle.RECONNECTED)
                    info["lifecycle"] = PlayerLifecycle.RECONNECTED.value
                info["online"] = True
                state.now_ms = now_ms
                self._persist(state)
                if self.persistence_service is not None:
                    self.persistence_service.mark_online(match_id, player_id)
                logger.info("audit action=reconnect match_id=%s seat=%s player_id=%s", match_id, seat, player_id)
                return self._build_player_join_payload(state, seat)
        raise ValueError("player auth failed")

    def _reassign_host_if_needed(self, state: MatchState, now_ms: int) -> None:
        if state.host_seat in state.players:
            state.host_player_id = state.players[state.host_seat].get("player_id")
            return
        if not state.players:
            state.host_seat = None
            state.host_player_id = None
            return
        new_host = sorted(state.players.keys())[0]
        state.host_seat = new_host
        state.host_player_id = state.players[new_host].get("player_id")
        state.add_event(GameEvent(EVENT_HOST_CHANGED, now_ms, {"seat": new_host}))
        logger.info("audit action=host_changed match_id=%s new_host_seat=%s", state.match_id, new_host)

    def _build_player_join_payload(self, state: MatchState, seat: int) -> dict:
        info = state.players.get(seat)
        if not info:
            raise ValueError("player not found")
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


    def _persist(self, state: MatchState) -> None:
        if self.persistence_service is not None:
            self.persistence_service.persist_match_state(state)
        else:
            self.repo.save_match(state)

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
                lifecycle = PlayerLifecycle(info.get("lifecycle", PlayerLifecycle.RUNNING.value))
                PlayerStateMachine.require_transition(lifecycle, PlayerLifecycle.OFFLINE)
                info["online"] = False
                info["lifecycle"] = PlayerLifecycle.OFFLINE.value
                if self.persistence_service is not None:
                    self.persistence_service.mark_offline(match_id, player_id)
                state.add_event(GameEvent(EVENT_PLAYER_OFFLINE, now_ms, {"seat": seat, "player_id": player_id}))
            if not state.players:
                self.repo.delete_match(match_id)
                logger.info("audit action=leave_delete_room match_id=%s player_id=%s", match_id, player_id)
                return state
            self._persist(state)
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
                lifecycle = PlayerLifecycle(info.get("lifecycle", PlayerLifecycle.JOINED.value))
                PlayerStateMachine.require_transition(lifecycle, PlayerLifecycle.READY)
                info["ready"] = True
                info["lifecycle"] = PlayerLifecycle.READY.value
                state.add_event(GameEvent(EVENT_PLAYER_READY, now_ms, {"seat": seat, "player_id": player_id}))
                self._persist(state)
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
        RoomStateMachine.require_transition(state.status, MatchStatus.RUNNING)
        state.started_at = now
        state.now_ms = now
        state.status = MatchStatus.RUNNING
        for info in state.players.values():
            lifecycle = PlayerLifecycle(info.get("lifecycle", PlayerLifecycle.READY.value))
            if PlayerStateMachine.can_transition(lifecycle, PlayerLifecycle.RUNNING):
                info["lifecycle"] = PlayerLifecycle.RUNNING.value
        state.last_action_at = now
        state.last_capture_at = now
        state.add_event(GameEvent(EVENT_MATCH_STARTED, now, {}))
        self._persist(state)
        logger.info("audit action=start match_id=%s by_player_id=%s host_seat=%s", match_id, requester_player_id, state.host_seat)
        return state

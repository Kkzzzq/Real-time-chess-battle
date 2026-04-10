from __future__ import annotations

import time
import uuid

from app.domain.enums import MatchStatus, PieceType
from app.domain.events import EVENT_MATCH_CREATED, EVENT_MATCH_STARTED, EVENT_PLAYER_JOINED, GameEvent
from app.domain.models import MatchState
from app.engine.board_setup import create_standard_board
from app.repository.memory_repo import MemoryRepo


class RoomService:
    def __init__(self, repo: MemoryRepo) -> None:
        self.repo = repo

    def create_match(self) -> MatchState:
        now = int(time.time() * 1000)
        state = MatchState(
            match_id=uuid.uuid4().hex[:12],
            created_at=now,
            now_ms=now,
            pieces=create_standard_board(),
            unlocked_by_player={1: {PieceType.SOLDIER}, 2: {PieceType.SOLDIER}},
        )
        state.add_event(GameEvent(EVENT_MATCH_CREATED, now, {"match_id": state.match_id}))
        self.repo.save_match(state)
        return state

    def join_match(self, match_id: str, player_name: str) -> dict:
        state = self.repo.get_match(match_id)
        if state is None:
            raise ValueError("match not found")
        if state.status != MatchStatus.WAITING:
            raise ValueError("match already started")
        seat = 1 if 1 not in state.players else 2
        if seat in state.players:
            raise ValueError("match full")
        player = {
            "id": uuid.uuid4().hex[:8],
            "name": player_name,
            "ready": False,
            "online": True,
            "is_host": len(state.players) == 0,
        }
        state.players[seat] = player
        state.add_event(GameEvent(EVENT_PLAYER_JOINED, state.now_ms, {"seat": seat, "name": player_name}))
        self.repo.save_match(state)
        return {"seat": seat, **player}

    def leave_match(self, match_id: str, player_id: str) -> MatchState:
        state = self.repo.get_match(match_id)
        if not state:
            raise ValueError("match not found")
        for seat, info in list(state.players.items()):
            if info.get("id") != player_id:
                continue
            if state.status == MatchStatus.WAITING:
                del state.players[seat]
            else:
                info["online"] = False
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
        for info in state.players.values():
            if info.get("id") == player_id:
                if info.get("ready"):
                    raise ValueError("already ready")
                info["ready"] = True
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

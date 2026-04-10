from __future__ import annotations

import time

from app.core.ruleset import COOLDOWN_SECONDS
from app.domain.enums import MatchStatus
from app.domain.events import EVENT_COOLDOWN_STARTED, EVENT_MOVE_FINISHED, EVENT_PHASE_CHANGED, EVENT_PIECE_READY, GameEvent
from app.engine.contact_resolver import resolve_contacts
from app.engine.endgame import check_draw_conditions, check_general_dead
from app.engine.phase import compute_phase
from app.engine.snapshot import build_match_snapshot
from app.engine.timeline import advance_all_pieces, finish_move
from app.engine.unlock_service import UnlockService
from app.repository.memory_repo import MemoryRepo


class MatchService:
    def __init__(self, repo: MemoryRepo) -> None:
        self.repo = repo

    def tick_once(self, match_id: str, now_ms: int | None = None) -> dict | None:
        state = self.repo.get_match(match_id)
        if state is None:
            return None
        if now_ms is None:
            now_ms = int(time.time() * 1000)
        state.now_ms = now_ms
        if state.status != MatchStatus.RUNNING:
            return build_match_snapshot(state, now_ms)
        self.advance_match(state, now_ms)
        return build_match_snapshot(state, now_ms)

    def advance_match(self, state, now_ms: int) -> None:
        old_phase = state.phase_name
        name, deadline, wave = compute_phase(now_ms, state.started_at)
        state.phase_name, state.phase_deadline_ms, state.wave_index = name, deadline, wave
        if old_phase != name:
            state.add_event(GameEvent(EVENT_PHASE_CHANGED, now_ms, {"from": old_phase, "to": name}))
        UnlockService.apply_auto_unlocks(state, now_ms)
        resolve_contacts(state, now_ms)
        arrived = advance_all_pieces(state, now_ms)
        for p in arrived:
            if not p.alive:
                continue
            finish_move(p, now_ms)
            p.cooldown_end_at = now_ms + int(COOLDOWN_SECONDS[p.kind] * 1000)
            state.add_event(GameEvent(EVENT_MOVE_FINISHED, now_ms, {"piece_id": p.id, "x": p.x, "y": p.y}))
            state.add_event(GameEvent(EVENT_COOLDOWN_STARTED, now_ms, {"piece_id": p.id, "cooldown_end_at": p.cooldown_end_at}))
        self.emit_piece_ready_events(state, now_ms)
        check_general_dead(state, now_ms)
        check_draw_conditions(state, now_ms)

    def emit_piece_ready_events(self, state, now_ms: int) -> None:
        for p in state.pieces.values():
            if p.alive and (not p.is_moving) and p.cooldown_end_at == now_ms:
                state.add_event(GameEvent(EVENT_PIECE_READY, now_ms, {"piece_id": p.id}))

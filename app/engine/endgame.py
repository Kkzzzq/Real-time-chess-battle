from __future__ import annotations

from app.core.constants import DRAW_CHECK_START, NO_ACTION_DRAW_SECONDS, NO_CAPTURE_DRAW_SECONDS
from app.domain.enums import MatchStatus, PieceType
from app.domain.events import EVENT_DRAW, EVENT_GAME_OVER, EVENT_RESIGN, GameEvent
from app.domain.models import MatchState


def finish_match(state: MatchState, winner: int | None, reason: str, now_ms: int) -> None:
    if state.status == MatchStatus.ENDED:
        return
    state.status = MatchStatus.ENDED
    state.winner = winner
    state.reason = reason
    state.add_event(GameEvent(EVENT_GAME_OVER if winner else EVENT_DRAW, now_ms, {"winner": winner, "reason": reason}))


def check_general_dead(state: MatchState, now_ms: int) -> None:
    alive = [p for p in state.pieces.values() if p.alive and p.kind == PieceType.GENERAL]
    if len(alive) == 2:
        return
    if len(alive) == 1:
        finish_match(state, alive[0].owner, "general captured", now_ms)
    else:
        finish_match(state, None, "both generals dead", now_ms)


def check_draw_conditions(state: MatchState, now_ms: int) -> None:
    if not state.allow_draw:
        return
    if state.started_at is None or state.status == MatchStatus.ENDED:
        return
    elapsed = (now_ms - state.started_at) / 1000
    if elapsed < DRAW_CHECK_START:
        return
    if state.last_action_at is not None and (now_ms - state.last_action_at) / 1000 >= NO_ACTION_DRAW_SECONDS:
        finish_match(state, None, "no legal action for 60s", now_ms)
        return
    if state.last_capture_at is not None and (now_ms - state.last_capture_at) / 1000 >= NO_CAPTURE_DRAW_SECONDS:
        finish_match(state, None, "no capture for 90s", now_ms)


def apply_resign(player: int, state: MatchState, now_ms: int) -> None:
    if state.status == MatchStatus.ENDED:
        return
    winner = 1 if player == 2 else 2
    state.add_event(GameEvent(EVENT_RESIGN, now_ms, {"player": player}))
    finish_match(state, winner, "resign", now_ms)

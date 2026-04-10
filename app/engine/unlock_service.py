from __future__ import annotations

from app.core.constants import FULL_UNLOCK_AT
from app.core.ruleset import AUTO_UNLOCK_PRIORITY
from app.domain.enums import PieceType
from app.domain.events import EVENT_UNLOCK_AUTO_APPLIED, EVENT_UNLOCK_CHOSEN, GameEvent
from app.domain.models import MatchState
from app.engine.phase import get_current_wave_index, get_wave_options


class UnlockService:
    @staticmethod
    def get_unlocked_kinds(player: int, state: MatchState) -> set[PieceType]:
        return state.unlocked_by_player.setdefault(player, {PieceType.SOLDIER})

    @staticmethod
    def get_current_unlock_options(player: int, state: MatchState, now_ms: int) -> list[PieceType]:
        options = get_wave_options(now_ms, state.started_at)
        unlocked = UnlockService.get_unlocked_kinds(player, state)
        return sorted(options - unlocked, key=lambda x: x.value)

    @staticmethod
    def choose_unlock(player: int, kind: PieceType, state: MatchState, now_ms: int) -> tuple[bool, str]:
        idx = get_current_wave_index(now_ms, state.started_at)
        if idx < 0:
            return False, "unlock window not open"
        options = set(UnlockService.get_current_unlock_options(player, state, now_ms))
        if kind not in options:
            return False, "invalid unlock choice"
        UnlockService.get_unlocked_kinds(player, state).add(kind)
        state.pending_unlock_choice.setdefault(player, {})[idx] = kind
        state.add_event(GameEvent(EVENT_UNLOCK_CHOSEN, now_ms, {"player": player, "kind": kind.value, "wave": idx}))
        return True, "ok"

    @staticmethod
    def apply_auto_unlocks(state: MatchState, now_ms: int) -> None:
        if state.started_at is None:
            return
        elapsed = (now_ms - state.started_at) / 1000
        if elapsed >= FULL_UNLOCK_AT:
            UnlockService.unlock_remaining_at_130(state)
            return
        idx = get_current_wave_index(now_ms, state.started_at)
        if idx < 0:
            return
        for player in (1, 2):
            if idx in state.pending_unlock_choice.setdefault(player, {}):
                continue
            options = UnlockService.get_current_unlock_options(player, state, now_ms)
            pick = next((k for k in AUTO_UNLOCK_PRIORITY if k in options), None)
            if pick is None:
                state.pending_unlock_choice[player][idx] = PieceType.SOLDIER
                continue
            UnlockService.get_unlocked_kinds(player, state).add(pick)
            state.pending_unlock_choice[player][idx] = pick
            state.add_event(GameEvent(EVENT_UNLOCK_AUTO_APPLIED, now_ms, {"player": player, "kind": pick.value, "wave": idx}))

    @staticmethod
    def unlock_remaining_at_130(state: MatchState) -> None:
        for player in (1, 2):
            state.unlocked_by_player[player] = set(PieceType)

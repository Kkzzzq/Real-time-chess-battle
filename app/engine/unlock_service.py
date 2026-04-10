from __future__ import annotations

from app.core.constants import FULL_UNLOCK_AT
from app.core.ruleset import AUTO_UNLOCK_PRIORITY
from app.domain.enums import PieceType
from app.domain.events import EVENT_UNLOCK_AUTO_APPLIED, EVENT_UNLOCK_CHOSEN, GameEvent
from app.domain.models import MatchState
from app.engine.phase import (
    get_current_wave_index,
    get_wave_options,
    get_wave_options_by_index,
    is_wave_timeout,
)


class UnlockService:
    @staticmethod
    def get_unlocked_kinds(player: int, state: MatchState) -> set[PieceType]:
        return state.unlocked_by_player.setdefault(player, {PieceType.SOLDIER})

    @staticmethod
    def get_player_wave_choice(player: int, wave: int, state: MatchState) -> PieceType | None:
        return state.pending_unlock_choice.setdefault(player, {}).get(wave)

    @staticmethod
    def has_player_chosen_wave(player: int, wave: int, state: MatchState) -> bool:
        return UnlockService.get_player_wave_choice(player, wave, state) is not None

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
        if UnlockService.has_player_chosen_wave(player, idx, state):
            return False, "already chosen in this wave"
        options = set(UnlockService.get_current_unlock_options(player, state, now_ms))
        if kind not in options:
            return False, "invalid unlock choice"
        UnlockService.get_unlocked_kinds(player, state).add(kind)
        state.pending_unlock_choice.setdefault(player, {})[idx] = kind
        state.add_event(GameEvent(EVENT_UNLOCK_CHOSEN, now_ms, {"player": player, "kind": kind.value, "wave": idx}))
        return True, "ok"

    @staticmethod
    def apply_auto_unlock_for_wave(player: int, wave: int, state: MatchState, now_ms: int) -> None:
        if UnlockService.has_player_chosen_wave(player, wave, state):
            return
        processed = state.auto_unlock_processed_waves.setdefault(player, set())
        if wave in processed:
            return
        options = sorted(get_wave_options_by_index(wave) - UnlockService.get_unlocked_kinds(player, state), key=lambda k: k.value)
        pick = next((k for k in AUTO_UNLOCK_PRIORITY if k in options), None)
        if pick is None:
            pick = PieceType.SOLDIER
        UnlockService.get_unlocked_kinds(player, state).add(pick)
        state.pending_unlock_choice.setdefault(player, {})[wave] = pick
        processed.add(wave)
        state.add_event(GameEvent(EVENT_UNLOCK_AUTO_APPLIED, now_ms, {"player": player, "kind": pick.value, "wave": wave}))

    @staticmethod
    def lock_full_unlock_at_130(state: MatchState, now_ms: int) -> None:
        for player in (1, 2):
            if state.unlocked_by_player.get(player) != set(PieceType):
                state.unlocked_by_player[player] = set(PieceType)
                state.add_event(GameEvent(EVENT_UNLOCK_AUTO_APPLIED, now_ms, {"player": player, "kind": "all", "wave": "full_unlock"}))

    @staticmethod
    def apply_auto_unlocks(state: MatchState, now_ms: int) -> None:
        if state.started_at is None:
            return
        elapsed = (now_ms - state.started_at) / 1000
        if elapsed >= FULL_UNLOCK_AT:
            UnlockService.lock_full_unlock_at_130(state, now_ms)
            return

        for wave in range(4):
            if not is_wave_timeout(now_ms, state.started_at, wave):
                continue
            for player in (1, 2):
                UnlockService.apply_auto_unlock_for_wave(player, wave, state, now_ms)

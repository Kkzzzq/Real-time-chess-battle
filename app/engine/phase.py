from __future__ import annotations

from app.core.constants import FULL_UNLOCK_AT, SEAL_DURATION, SOLDIER_ONLY_END
from app.core.ruleset import UNLOCK_WAVES
from app.domain.enums import PieceType
from app.domain.models import MatchState

DEFAULT_WAVE_OPEN_SECONDS = [50, 70, 90, 110]
DEFAULT_WAVE_WINDOW_SECONDS = 20


def _get_wave_open_seconds(state: MatchState | None) -> list[int]:
    if state and state.custom_unlock_windows:
        return sorted(state.custom_unlock_windows)
    return DEFAULT_WAVE_OPEN_SECONDS


def _wave_count(state: MatchState | None) -> int:
    return len(_get_wave_open_seconds(state))


def _wave_window_seconds(state: MatchState | None) -> int:
    return DEFAULT_WAVE_WINDOW_SECONDS


def _wave_start_second(index: int, state: MatchState | None) -> int:
    wave_seconds = _get_wave_open_seconds(state)
    return wave_seconds[index]


def get_current_wave_index(now_ms: int, started_at: int | None, state: MatchState | None = None) -> int:
    if started_at is None:
        return -1
    elapsed = (now_ms - started_at) / 1000
    window = _wave_window_seconds(state)
    for idx, start in enumerate(_get_wave_open_seconds(state)):
        if start <= elapsed < start + window:
            return idx
    return -1


def get_latest_wave_index(now_ms: int, started_at: int | None, state: MatchState | None = None) -> int:
    if started_at is None:
        return -1
    elapsed = (now_ms - started_at) / 1000
    latest = -1
    for idx, start in enumerate(_get_wave_open_seconds(state)):
        if elapsed >= start:
            latest = idx
    return latest


def get_current_wave_start_ms(now_ms: int, started_at: int | None, state: MatchState | None = None) -> int | None:
    idx = get_current_wave_index(now_ms, started_at, state)
    if idx < 0 or started_at is None:
        return None
    return started_at + _wave_start_second(idx, state) * 1000


def get_current_wave_deadline_ms(now_ms: int, started_at: int | None, state: MatchState | None = None) -> int | None:
    start = get_current_wave_start_ms(now_ms, started_at, state)
    if start is None:
        return None
    return start + _wave_window_seconds(state) * 1000


def get_current_wave_remaining_ms(now_ms: int, started_at: int | None, state: MatchState | None = None) -> int:
    deadline = get_current_wave_deadline_ms(now_ms, started_at, state)
    if deadline is None:
        return 0
    return max(0, deadline - now_ms)


def is_wave_timeout(now_ms: int, started_at: int | None, wave_index: int, state: MatchState | None = None) -> bool:
    if started_at is None or wave_index < 0 or wave_index >= _wave_count(state):
        return False
    deadline = started_at + (_wave_start_second(wave_index, state) + _wave_window_seconds(state)) * 1000
    return now_ms >= deadline


def compute_phase(now_ms: int, started_at: int | None, state: MatchState | None = None) -> tuple[str, int | None, int]:
    if started_at is None:
        return "waiting", None, -1
    elapsed = (now_ms - started_at) / 1000
    if elapsed < SEAL_DURATION:
        return "sealed", started_at + SEAL_DURATION * 1000, -1
    if elapsed < SOLDIER_ONLY_END:
        return "soldier_only", started_at + SOLDIER_ONLY_END * 1000, -1
    if elapsed >= FULL_UNLOCK_AT:
        return "fully_unlocked", None, _wave_count(state) - 1
    wave = get_current_wave_index(now_ms, started_at, state)
    if wave >= 0:
        deadline = started_at + (_wave_start_second(wave, state) + _wave_window_seconds(state)) * 1000
        return "unlock_wave", deadline, wave
    return "midgame", started_at + FULL_UNLOCK_AT * 1000, get_latest_wave_index(now_ms, started_at, state)


def get_phase_name(now_ms: int, started_at: int | None, state: MatchState | None = None) -> str:
    return compute_phase(now_ms, started_at, state)[0]


def get_phase_deadline(now_ms: int, started_at: int | None, state: MatchState | None = None) -> int | None:
    return compute_phase(now_ms, started_at, state)[1]


def is_unlock_window_open(now_ms: int, started_at: int | None, state: MatchState | None = None) -> bool:
    return get_current_wave_index(now_ms, started_at, state) >= 0


def is_piece_kind_allowed_by_phase(player: int, kind: PieceType, state: MatchState, now_ms: int) -> bool:
    if state.started_at is None:
        return False
    elapsed = (now_ms - state.started_at) / 1000
    if elapsed < SEAL_DURATION:
        return False
    if elapsed < SOLDIER_ONLY_END:
        return kind == PieceType.SOLDIER
    return kind in state.unlocked_by_player.get(player, {PieceType.SOLDIER})


def get_wave_options(now_ms: int, started_at: int | None, state: MatchState | None = None) -> set[PieceType]:
    idx = get_current_wave_index(now_ms, started_at, state)
    if idx < 0:
        return set()
    return get_wave_options_by_index(idx, state)


def get_wave_options_by_index(wave_index: int, state: MatchState | None = None) -> set[PieceType]:
    if wave_index < 0 or wave_index >= _wave_count(state):
        return set()
    second = _wave_start_second(wave_index, state)
    if second in UNLOCK_WAVES:
        return UNLOCK_WAVES[second]
    # fallback: closest prior configured wave from default map
    available = sorted(UNLOCK_WAVES.keys())
    prior = [s for s in available if s <= second]
    if prior:
        return UNLOCK_WAVES[prior[-1]]
    return UNLOCK_WAVES[available[0]]

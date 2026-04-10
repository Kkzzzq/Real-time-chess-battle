from __future__ import annotations

from app.core.constants import FULL_UNLOCK_AT, SEAL_DURATION, SOLDIER_ONLY_END
from app.core.ruleset import UNLOCK_WAVES
from app.domain.enums import PieceType
from app.domain.models import MatchState

WAVE_OPEN_SECONDS = [50, 70, 90, 110]
WAVE_WINDOW_SECONDS = 20


def _wave_start_second(index: int) -> int:
    return WAVE_OPEN_SECONDS[index]


def get_current_wave_index(now_ms: int, started_at: int | None) -> int:
    if started_at is None:
        return -1
    elapsed = (now_ms - started_at) / 1000
    for idx, start in enumerate(WAVE_OPEN_SECONDS):
        if start <= elapsed < start + WAVE_WINDOW_SECONDS:
            return idx
    return -1


def get_latest_wave_index(now_ms: int, started_at: int | None) -> int:
    if started_at is None:
        return -1
    elapsed = (now_ms - started_at) / 1000
    latest = -1
    for idx, start in enumerate(WAVE_OPEN_SECONDS):
        if elapsed >= start:
            latest = idx
    return latest


def get_current_wave_start_ms(now_ms: int, started_at: int | None) -> int | None:
    idx = get_current_wave_index(now_ms, started_at)
    if idx < 0 or started_at is None:
        return None
    return started_at + _wave_start_second(idx) * 1000


def get_current_wave_deadline_ms(now_ms: int, started_at: int | None) -> int | None:
    start = get_current_wave_start_ms(now_ms, started_at)
    if start is None:
        return None
    return start + WAVE_WINDOW_SECONDS * 1000


def get_current_wave_remaining_ms(now_ms: int, started_at: int | None) -> int:
    deadline = get_current_wave_deadline_ms(now_ms, started_at)
    if deadline is None:
        return 0
    return max(0, deadline - now_ms)


def is_wave_timeout(now_ms: int, started_at: int | None, wave_index: int) -> bool:
    if started_at is None or wave_index < 0:
        return False
    deadline = started_at + (WAVE_OPEN_SECONDS[wave_index] + WAVE_WINDOW_SECONDS) * 1000
    return now_ms >= deadline


def compute_phase(now_ms: int, started_at: int | None) -> tuple[str, int | None, int]:
    if started_at is None:
        return "waiting", None, -1
    elapsed = (now_ms - started_at) / 1000
    if elapsed < SEAL_DURATION:
        return "sealed", started_at + SEAL_DURATION * 1000, -1
    if elapsed < SOLDIER_ONLY_END:
        return "soldier_only", started_at + SOLDIER_ONLY_END * 1000, -1
    if elapsed >= FULL_UNLOCK_AT:
        return "fully_unlocked", None, len(WAVE_OPEN_SECONDS) - 1
    wave = get_current_wave_index(now_ms, started_at)
    if wave >= 0:
        deadline = started_at + (WAVE_OPEN_SECONDS[wave] + WAVE_WINDOW_SECONDS) * 1000
        return "unlock_wave", deadline, wave
    return "midgame", started_at + FULL_UNLOCK_AT * 1000, get_latest_wave_index(now_ms, started_at)


def get_phase_name(now_ms: int, started_at: int | None) -> str:
    return compute_phase(now_ms, started_at)[0]


def get_phase_deadline(now_ms: int, started_at: int | None) -> int | None:
    return compute_phase(now_ms, started_at)[1]


def is_unlock_window_open(now_ms: int, started_at: int | None) -> bool:
    return get_current_wave_index(now_ms, started_at) >= 0


def is_piece_kind_allowed_by_phase(player: int, kind: PieceType, state: MatchState, now_ms: int) -> bool:
    if state.started_at is None:
        return False
    elapsed = (now_ms - state.started_at) / 1000
    if elapsed < SEAL_DURATION:
        return False
    if elapsed < SOLDIER_ONLY_END:
        return kind == PieceType.SOLDIER
    return kind in state.unlocked_by_player.get(player, {PieceType.SOLDIER})


def get_wave_options(now_ms: int, started_at: int | None) -> set[PieceType]:
    idx = get_current_wave_index(now_ms, started_at)
    if idx < 0:
        return set()
    return UNLOCK_WAVES[WAVE_OPEN_SECONDS[idx]]


def get_wave_options_by_index(wave_index: int) -> set[PieceType]:
    if wave_index < 0:
        return set()
    return UNLOCK_WAVES[WAVE_OPEN_SECONDS[wave_index]]

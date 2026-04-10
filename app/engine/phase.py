from __future__ import annotations

from app.core.constants import FULL_UNLOCK_AT, SEAL_DURATION, SOLDIER_ONLY_END
from app.core.ruleset import UNLOCK_WAVES
from app.domain.enums import PieceType
from app.domain.models import MatchState


WAVE_TIMES = [50, 70, 90, 110]


def compute_phase(now_ms: int, started_at: int | None) -> tuple[str, int | None, int]:
    if started_at is None:
        return "waiting", None, -1
    elapsed = (now_ms - started_at) / 1000
    if elapsed < SEAL_DURATION:
        return "sealed", started_at + SEAL_DURATION * 1000, -1
    if elapsed < SOLDIER_ONLY_END:
        return "soldier_only", started_at + SOLDIER_ONLY_END * 1000, -1
    if elapsed >= FULL_UNLOCK_AT:
        return "fully_unlocked", None, len(WAVE_TIMES) - 1
    idx = get_current_wave_index(now_ms, started_at)
    deadline = started_at + (WAVE_TIMES[idx] + 20) * 1000
    return "unlock_wave", deadline, idx


def get_phase_name(now_ms: int, started_at: int | None) -> str:
    return compute_phase(now_ms, started_at)[0]


def get_phase_deadline(now_ms: int, started_at: int | None) -> int | None:
    return compute_phase(now_ms, started_at)[1]


def get_current_wave_index(now_ms: int, started_at: int | None) -> int:
    if started_at is None:
        return -1
    elapsed = (now_ms - started_at) / 1000
    if elapsed < 50:
        return -1
    if elapsed < 70:
        return 0
    if elapsed < 90:
        return 1
    if elapsed < 110:
        return 2
    return 3


def is_unlock_window_open(now_ms: int, started_at: int | None) -> bool:
    return get_phase_name(now_ms, started_at) == "unlock_wave"


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
    return UNLOCK_WAVES[WAVE_TIMES[idx]]

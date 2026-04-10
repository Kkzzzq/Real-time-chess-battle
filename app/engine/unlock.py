from __future__ import annotations

from app.domain.enums import ALL_PLAYERS, AUTO_UNLOCK_PRIORITY, PieceType, UNLOCK_WAVES
from app.domain.models import MatchState


class UnlockManager:
    @staticmethod
    def wave_options(elapsed: float) -> set[PieceType]:
        for sec in sorted(UNLOCK_WAVES, reverse=True):
            if elapsed >= sec:
                return UNLOCK_WAVES[sec]
        return set()

    @staticmethod
    def can_move_piece_type(state: MatchState, player: int, piece_type: PieceType, now: float) -> bool:
        elapsed = now - state.started_at
        if elapsed < 30:
            return False
        if 30 <= elapsed < 50:
            return piece_type == PieceType.SOLDIER
        return piece_type in state.unlocks[player].unlocked

    @staticmethod
    def choose_unlock(state: MatchState, player: int, piece_type: PieceType, now: float) -> tuple[bool, str]:
        elapsed = now - state.started_at
        options = UnlockManager.wave_options(elapsed)
        if not options:
            return False, "当前不在可选解锁窗口"
        if piece_type not in options:
            return False, "该棋种不在当前可选池"
        unlock_state = state.unlocks[player]
        wave_key = max(sec for sec in UNLOCK_WAVES if elapsed >= sec)
        if wave_key in unlock_state.selected_waves:
            return False, "该波次已经选择过"
        unlock_state.unlocked.add(piece_type)
        unlock_state.selected_waves.add(wave_key)
        return True, f"已解锁 {piece_type.value}"

    @staticmethod
    def resolve_auto_unlocks(state: MatchState, now: float) -> None:
        elapsed = now - state.started_at
        if elapsed >= 130:
            for player in ALL_PLAYERS:
                state.unlocks[player].unlocked.update(set(PieceType))
            return

        for wave_time, options in UNLOCK_WAVES.items():
            if elapsed < wave_time + 20:
                continue
            for player in ALL_PLAYERS:
                unlock = state.unlocks[player]
                if wave_time in unlock.selected_waves:
                    continue
                for pt in AUTO_UNLOCK_PRIORITY:
                    if pt in options and pt not in unlock.unlocked:
                        unlock.unlocked.add(pt)
                        break
                unlock.selected_waves.add(wave_time)

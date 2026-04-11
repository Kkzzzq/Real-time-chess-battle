from __future__ import annotations

from app.domain.enums import MatchStatus, PieceType
from app.domain.events import EVENT_MOVE_COMMAND_ACCEPTED, EVENT_MOVE_STARTED, GameEvent
from app.engine import path_planner, timeline
from app.engine.endgame import apply_resign
from app.engine.move_rules import validate_move
from app.engine.phase import is_piece_kind_allowed_by_phase
from app.engine.unlock_service import UnlockService
from app.repository.memory_repo import MemoryRepo


class CommandService:
    def __init__(self, repo: MemoryRepo) -> None:
        self.repo = repo

    def _append_command(self, state, payload: dict) -> None:
        state.command_log.append(payload)
        state.command_log = state.command_log[-200:]

    def _resolve_player_seat(self, state, player_id: str) -> tuple[int | None, str | None]:
        for seat, info in state.players.items():
            if info.get("id") == player_id:
                if not info.get("online", True):
                    return None, "player offline"
                return seat, None
        return None, "player not found"

    def handle_move_command(self, match_id: str, player_id: str, piece_id: str, target: tuple[int, int], now_ms: int) -> tuple[bool, str]:
        state = self.repo.get_match(match_id)
        if state is None:
            return False, "match not found"
        if state.status != MatchStatus.RUNNING:
            return False, "match not running"
        player, player_err = self._resolve_player_seat(state, player_id)
        if player_err:
            return False, player_err
        assert player is not None
        piece = state.pieces.get(piece_id)
        if piece is None or not piece.alive:
            return False, "piece not found"
        if piece.owner != player:
            return False, "not your piece"
        if piece.cooldown_end_at > now_ms:
            return False, "piece cooldown"
        if piece.is_moving:
            return False, "piece moving"
        if not is_piece_kind_allowed_by_phase(player, piece.kind, state, now_ms):
            return False, "kind locked by phase"
        if piece.kind not in state.unlocked_by_player[player]:
            return False, "kind not unlocked"
        ok, msg = validate_move(piece, target, state, now_ms)
        if not ok:
            return False, msg

        path = path_planner.build_path(piece, (piece.x, piece.y), target)
        duration_ms = path_planner.get_move_duration_ms(piece, path)
        timeline.start_move(piece, path, now_ms, duration_ms)
        state.last_action_at = now_ms
        self._append_command(
            state,
            {"type": "move", "piece_id": piece_id, "target": target, "player": player, "player_id": player_id, "ts": now_ms},
        )
        state.add_event(GameEvent(EVENT_MOVE_COMMAND_ACCEPTED, now_ms, {"piece_id": piece_id, "target": target}))
        state.add_event(GameEvent(EVENT_MOVE_STARTED, now_ms, {"piece_id": piece_id, "duration_ms": duration_ms}))
        self.repo.save_match(state)
        return True, "ok"

    def handle_unlock_command(self, match_id: str, player_id: str, kind: PieceType, now_ms: int) -> tuple[bool, str]:
        state = self.repo.get_match(match_id)
        if state is None:
            return False, "match not found"
        if state.status != MatchStatus.RUNNING:
            return False, "match not running"
        player, player_err = self._resolve_player_seat(state, player_id)
        if player_err:
            return False, player_err
        assert player is not None
        ok, msg = UnlockService.choose_unlock(player, kind, state, now_ms)
        if ok:
            self._append_command(state, {"type": "unlock", "player": player, "player_id": player_id, "kind": kind.value, "ts": now_ms})
            self.repo.save_match(state)
        return ok, msg

    def handle_resign_command(self, match_id: str, player_id: str, now_ms: int) -> tuple[bool, str]:
        state = self.repo.get_match(match_id)
        if state is None:
            return False, "match not found"
        if state.status != MatchStatus.RUNNING:
            return False, "match already ended" if state.status == MatchStatus.ENDED else "match not running"
        player, player_err = self._resolve_player_seat(state, player_id)
        if player_err:
            return False, player_err
        assert player is not None
        apply_resign(player, state, now_ms)
        self._append_command(state, {"type": "resign", "player": player, "player_id": player_id, "ts": now_ms})
        self.repo.save_match(state)
        return True, "ok"

from __future__ import annotations

import time

from app.domain.enums import ALL_PLAYERS, COOLDOWN_SECONDS, PieceType
from app.domain.models import CommandResult, MatchState, UnlockState
from app.engine.board_setup import initial_pieces
from app.engine.collision import CollisionResolver
from app.engine.rules import RulesEngine
from app.engine.unlock import UnlockManager


class MatchGame:
    def __init__(self, match_id: str) -> None:
        now = time.time()
        self.state = MatchState(
            match_id=match_id,
            started_at=now,
            pieces=initial_pieces(),
            unlocks={1: UnlockState(), 2: UnlockState()},
            last_action_at=now,
            last_capture_at=now,
        )

    def tick(self, now: float | None = None) -> None:
        now = now or time.time()
        if self.is_over:
            return
        self.state.tick_index += 1

        UnlockManager.resolve_auto_unlocks(self.state, now)

        arrived = []
        for piece in self.state.pieces.values():
            if piece.alive and piece.moving and piece.move_end_at is not None and piece.move_end_at <= now:
                arrived.append(piece)

        outcome = CollisionResolver.resolve_arrivals(self.state, arrived)
        if outcome.captured:
            self.state.last_capture_at = now

        for piece in arrived:
            if piece.alive and piece.target is not None:
                piece.x, piece.y = piece.target
                piece.cooldown_until = now + COOLDOWN_SECONDS[piece.piece_type]
            piece.moving = False
            piece.target = None
            piece.move_start_at = None
            piece.move_end_at = None
            piece.move_start_pos = None

        self._resolve_winner(now)
        self._resolve_draw(now)

    @property
    def is_over(self) -> bool:
        return self.state.winner is not None or self.state.draw

    def command_move(self, player: int, piece_id: str, target_x: int, target_y: int, now: float | None = None) -> CommandResult:
        now = now or time.time()
        self.tick(now)
        if self.is_over:
            return CommandResult(False, "对局已结束")

        piece = self.state.pieces.get(piece_id)
        if piece is None or not piece.alive:
            return CommandResult(False, "棋子不存在")
        if piece.player != player:
            return CommandResult(False, "不能操作对方棋子")
        if not UnlockManager.can_move_piece_type(self.state, player, piece.piece_type, now):
            return CommandResult(False, "该棋种当前未解锁")

        result = RulesEngine.validate_move(self.state, player, piece_id, target_x, target_y, now)
        if not result.ok or result.movement is None:
            return CommandResult(False, result.message)

        piece.moving = True
        piece.move_start_at = now
        piece.move_end_at = now + result.movement.duration
        piece.move_start_pos = (piece.x, piece.y)
        piece.target = (target_x, target_y)
        self.state.last_action_at = now
        return CommandResult(True, "移动指令已生效")

    def command_unlock(self, player: int, piece_type: PieceType, now: float | None = None) -> CommandResult:
        now = now or time.time()
        self.tick(now)
        if self.is_over:
            return CommandResult(False, "对局已结束")
        ok, msg = UnlockManager.choose_unlock(self.state, player, piece_type, now)
        return CommandResult(ok, msg)

    def command_resign(self, player: int, now: float | None = None) -> CommandResult:
        now = now or time.time()
        if self.is_over:
            return CommandResult(False, "对局已结束")
        self.state.resigned_player = player
        self.state.winner = 2 if player == 1 else 1
        self.state.ended_at = now
        return CommandResult(True, "已认输")

    def _resolve_winner(self, now: float) -> None:
        alive_generals = {
            p.player
            for p in self.state.pieces.values()
            if p.alive and p.piece_type == PieceType.GENERAL
        }
        if len(alive_generals) == 1:
            self.state.winner = next(iter(alive_generals))
            self.state.ended_at = now

    def _resolve_draw(self, now: float) -> None:
        elapsed = now - self.state.started_at
        if elapsed < 150:
            return
        if self.state.last_action_at is not None and now - self.state.last_action_at >= 60:
            self.state.draw = True
            self.state.draw_reason = "连续60秒双方无新合法出手"
            self.state.ended_at = now
            return
        if self.state.last_capture_at is not None and now - self.state.last_capture_at >= 90:
            self.state.draw = True
            self.state.draw_reason = "连续90秒无吃子"
            self.state.ended_at = now

    def enriched_snapshot(self, now: float | None = None) -> dict[str, object]:
        now = now or time.time()
        self.tick(now)
        elapsed = now - self.state.started_at
        if elapsed < 30:
            stage = "sealed"
            next_wave = 30
            unlock_options: dict[str, list[str]] = {}
        elif elapsed < 50:
            stage = "soldier_only"
            next_wave = 50
            unlock_options = {}
        else:
            stage = "unlocking"
            next_wave = min((w for w in (50, 70, 90, 110, 130) if elapsed < w), default=None)
            options = UnlockManager.wave_options(elapsed)
            unlock_options = {str(p): sorted([pt.value for pt in options]) for p in ALL_PLAYERS}

        data = self.state.to_dict(now)
        data.update(
            {
                "stage": stage,
                "countdown_to_next": None if next_wave is None else round(next_wave - elapsed, 3),
                "unlock_options": unlock_options,
            }
        )
        return data

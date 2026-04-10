from __future__ import annotations

from app.domain.enums import PieceType
from app.engine.game import MatchGame
from app.engine.rules import RulesEngine
from app.engine.unlock import UnlockManager


def make_game() -> MatchGame:
    game = MatchGame("test")
    game.state.started_at = 0.0
    game.state.last_action_at = 0.0
    game.state.last_capture_at = 0.0
    return game


def test_soldier_locked_before_30s_and_open_after_30s() -> None:
    game = make_game()
    soldier_id = "p1_soldier_1"
    early = game.command_move(1, soldier_id, 0, 5, now=10.0)
    assert early.ok is False
    assert "未解锁" in early.message

    later = game.command_move(1, soldier_id, 0, 5, now=30.0)
    assert later.ok is True


def test_auto_unlock_prefers_cannon_at_first_wave() -> None:
    game = make_game()
    UnlockManager.resolve_auto_unlocks(game.state, now=70.0)
    assert PieceType.CANNON in game.state.unlocks[1].unlocked
    assert PieceType.CANNON in game.state.unlocks[2].unlocked


def test_horse_leg_blocked_is_illegal() -> None:
    game = make_game()
    game.state.unlocks[1].unlocked.add(PieceType.HORSE)
    result = game.command_move(1, "p1_horse_1", 3, 8, now=80.0)
    assert result.ok is False
    assert "马腿" in result.message


def test_flying_general_capture_is_legal_when_file_is_clear() -> None:
    game = make_game()
    game.state.unlocks[1].unlocked.add(PieceType.GENERAL)
    game.state.unlocks[2].unlocked.add(PieceType.GENERAL)

    for piece in list(game.state.pieces.values()):
        if piece.x == 4 and piece.piece_type != PieceType.GENERAL:
            piece.alive = False

    validation = RulesEngine.validate_move(game.state, 1, "p1_general_1", 4, 0, now=120.0)
    assert validation.ok is True
    assert validation.movement is not None


def test_general_cannot_face_each_other_after_non_general_move() -> None:
    game = make_game()
    game.state.unlocks[1].unlocked.add(PieceType.CHARIOT)
    for piece in list(game.state.pieces.values()):
        if piece.x == 4 and piece.y not in (0, 9):
            piece.alive = False
    # place a rook between generals then move it away should be illegal due to face-to-face
    rook = game.state.pieces["p1_chariot_1"]
    rook.x, rook.y = 4, 5
    result = game.command_move(1, rook.piece_id, 3, 5, now=90.0)
    assert result.ok is False
    assert "照面" in result.message

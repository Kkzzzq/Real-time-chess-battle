"""Targeted backend tests for the xiangqi migration."""

from kfchess.game.board import Board
from kfchess.game.engine import GameEngine
from kfchess.game.moves import compute_move_path
from kfchess.game.pieces import Piece, PieceType
from kfchess.game.state import Speed


def test_standard_board_is_xiangqi_layout():
    board = Board.create_standard()
    assert board.width == 9
    assert board.height == 10
    assert board.get_piece_at(0, 4).type == PieceType.GENERAL
    assert board.get_piece_at(2, 1).type == PieceType.CANNON
    assert board.get_piece_at(6, 0).type == PieceType.SOLDIER
    assert board.get_piece_at(9, 4).type == PieceType.GENERAL


def test_horse_leg_block_rule():
    board = Board.create_empty()
    horse = Piece.create(PieceType.HORSE, player=1, row=9, col=1)
    blocker = Piece.create(PieceType.SOLDIER, player=1, row=8, col=1)
    board.add_piece(horse)
    board.add_piece(blocker)
    assert compute_move_path(horse, board, 7, 0, []) is None


def test_cannon_capture_requires_screen():
    board = Board.create_empty()
    cannon = Piece.create(PieceType.CANNON, player=1, row=7, col=1)
    screen = Piece.create(PieceType.SOLDIER, player=1, row=5, col=1)
    target = Piece.create(PieceType.SOLDIER, player=2, row=3, col=1)
    board.add_piece(cannon)
    board.add_piece(screen)
    board.add_piece(target)
    path = compute_move_path(cannon, board, 3, 1, [])
    assert path == [(7, 1), (3, 1)]


def test_general_cannot_leave_palace():
    board = Board.create_empty()
    general = Piece.create(PieceType.GENERAL, player=1, row=9, col=4)
    board.add_piece(general)
    assert compute_move_path(general, board, 9, 6, []) is None


from kfchess.game.board import BoardType


def test_game_engine_rejects_four_player_board():
    try:
        GameEngine.create_game(speed=Speed.STANDARD, players={1: 'u:a', 2: 'u:b'}, board_type=BoardType.FOUR_PLAYER)
    except ValueError:
        assert True
    else:
        assert False

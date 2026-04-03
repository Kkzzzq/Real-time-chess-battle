"""Collision detection for Real-time-chess-battle (中国象棋版)."""

import math
from dataclasses import dataclass

from kfchess.game.moves import Cooldown, Move
from kfchess.game.pieces import Piece

CAPTURE_DISTANCE = 0.4


@dataclass
class Capture:
    capturing_piece_id: str
    captured_piece_id: str
    position: tuple[float, float]


def get_interpolated_position(
    piece: Piece,
    active_moves: list[Move] | None,
    current_tick: int,
    ticks_per_square: int,
    *,
    move: Move | None = None,
) -> tuple[float, float]:
    active_move = move
    if active_move is None and active_moves is not None:
        for m in active_moves:
            if m.piece_id == piece.id:
                active_move = m
                break

    if active_move is None:
        return (piece.row, piece.col)

    ticks_elapsed = current_tick - active_move.start_tick
    if ticks_elapsed < 0:
        return (piece.row, piece.col)

    path = active_move.path
    total_squares = len(path) - 1
    if total_squares <= 0:
        return (piece.row, piece.col)

    total_ticks = total_squares * ticks_per_square
    if ticks_elapsed >= total_ticks:
        return (float(path[-1][0]), float(path[-1][1]))

    progress = ticks_elapsed / ticks_per_square
    segment_index = int(progress)
    segment_progress = progress - segment_index
    if segment_index >= total_squares:
        return (float(path[-1][0]), float(path[-1][1]))

    start_row, start_col = path[segment_index]
    end_row, end_col = path[segment_index + 1]
    interp_row = start_row + (end_row - start_row) * segment_progress
    interp_col = start_col + (end_col - start_col) * segment_progress
    return (interp_row, interp_col)


def detect_collisions(
    pieces: list[Piece],
    active_moves: list[Move],
    current_tick: int,
    ticks_per_square: int,
) -> list[Capture]:
    captures: list[Capture] = []
    move_by_piece: dict[str, Move] = {m.piece_id: m for m in active_moves}

    moving: list[tuple[Piece, tuple[float, float]]] = []
    stationary: list[tuple[Piece, tuple[float, float]]] = []
    for piece in pieces:
        if piece.captured:
            continue
        pos = get_interpolated_position(piece, None, current_tick, ticks_per_square, move=move_by_piece.get(piece.id))
        if piece.id in move_by_piece:
            moving.append((piece, pos))
        else:
            stationary.append((piece, pos))

    def check_pair(piece_a: Piece, pos_a: tuple[float, float], piece_b: Piece, pos_b: tuple[float, float]) -> None:
        if piece_a.player == piece_b.player:
            return
        dr = pos_a[0] - pos_b[0]
        dc = pos_a[1] - pos_b[1]
        if abs(dr) >= CAPTURE_DISTANCE or abs(dc) >= CAPTURE_DISTANCE:
            return
        dist = math.sqrt(dr * dr + dc * dc)
        if dist >= CAPTURE_DISTANCE:
            return

        winner, loser = _determine_capture_winner(piece_a, piece_b, move_by_piece)
        collision_pos = ((pos_a[0] + pos_b[0]) / 2, (pos_a[1] + pos_b[1]) / 2)
        if winner and loser:
            captures.append(Capture(capturing_piece_id=winner.id, captured_piece_id=loser.id, position=collision_pos))
        elif winner is None and loser is None:
            captures.append(Capture(capturing_piece_id="", captured_piece_id=piece_a.id, position=collision_pos))
            captures.append(Capture(capturing_piece_id="", captured_piece_id=piece_b.id, position=collision_pos))

    for i, (piece_a, pos_a) in enumerate(moving):
        for piece_b, pos_b in moving[i + 1:]:
            check_pair(piece_a, pos_a, piece_b, pos_b)
    for piece_a, pos_a in moving:
        for piece_b, pos_b in stationary:
            check_pair(piece_a, pos_a, piece_b, pos_b)

    return captures


def _determine_capture_winner(piece_a: Piece, piece_b: Piece, move_by_piece: dict[str, Move]) -> tuple[Piece | None, Piece | None]:
    move_a = move_by_piece.get(piece_a.id)
    move_b = move_by_piece.get(piece_b.id)
    a_moving = move_a is not None
    b_moving = move_b is not None

    if a_moving and not b_moving:
        return (piece_a, piece_b)
    if b_moving and not a_moving:
        return (piece_b, piece_a)
    if not a_moving and not b_moving:
        return (None, None)

    assert move_a is not None and move_b is not None
    if move_a.start_tick < move_b.start_tick:
        return (piece_a, piece_b)
    if move_b.start_tick < move_a.start_tick:
        return (piece_b, piece_a)
    return (None, None)


def is_piece_moving(piece_id: str, active_moves: list[Move]) -> bool:
    return any(m.piece_id == piece_id for m in active_moves)


def is_piece_on_cooldown(piece_id: str, cooldowns: list[Cooldown], current_tick: int) -> bool:
    for cd in cooldowns:
        if cd.piece_id == piece_id and cd.is_active(current_tick):
            return True
    return False

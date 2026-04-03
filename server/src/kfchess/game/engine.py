"""Core game engine for Real-time-chess-battle (中国象棋版)."""

import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum

from kfchess.game.board import Board, BoardType
from kfchess.game.collision import detect_collisions, get_interpolated_position, is_piece_moving, is_piece_on_cooldown
from kfchess.game.moves import Cooldown, Move, PathClearContext, build_path_clear_context, check_castling, compute_move_path, should_promote_pawn
from kfchess.game.pieces import Piece, PieceType
from kfchess.game.state import CAMPAIGN_DRAW_NO_MOVE_TICKS, GameState, GameStatus, ReplayMove, Speed, WinReason

logger = logging.getLogger(__name__)


class GameEventType(Enum):
    MOVE_STARTED = "move_started"
    MOVE_COMPLETED = "move_completed"
    CAPTURE = "capture"
    PROMOTION = "promotion"
    COOLDOWN_STARTED = "cooldown_started"
    COOLDOWN_ENDED = "cooldown_ended"
    GAME_STARTED = "game_started"
    GAME_OVER = "game_over"
    DRAW = "draw"


@dataclass
class GameEvent:
    type: GameEventType
    tick: int
    data: dict


class GameEngine:
    @staticmethod
    def create_game(speed: Speed, players: dict[int, str], board_type: BoardType = BoardType.STANDARD, game_id: str | None = None) -> GameState:
        if game_id is None:
            game_id = str(uuid.uuid4())[:8].upper()
        if board_type != BoardType.STANDARD:
            raise ValueError("Real-time-chess-battle 当前只支持 standard 双人中国象棋")
        if len(players) != 2:
            raise ValueError("中国象棋标准对局需要且仅需要 2 名玩家")
        return GameState(game_id=game_id, board=Board.create_standard(), speed=speed, players=players, status=GameStatus.WAITING)

    @staticmethod
    def create_game_from_board(speed: Speed, players: dict[int, str], board: Board, game_id: str | None = None) -> GameState:
        if game_id is None:
            game_id = str(uuid.uuid4())[:8].upper()
        return GameState(game_id=game_id, board=board, speed=speed, players=players, status=GameStatus.WAITING)

    @staticmethod
    def set_player_ready(state: GameState, player: int) -> tuple[GameState, list[GameEvent]]:
        events: list[GameEvent] = []
        if state.status != GameStatus.WAITING or player not in state.players:
            return state, events
        state.ready_players.add(player)
        for player_num, player_id in state.players.items():
            if player_id.startswith(("bot:", "c:")):
                state.ready_players.add(player_num)
        all_ready = all(p in state.ready_players for p in state.players.keys())
        if all_ready and len(state.players) == 2:
            state.status = GameStatus.PLAYING
            state.started_at = datetime.now(UTC)
            state.current_tick = 0
            state.last_move_tick = 0
            state.last_capture_tick = 0
            events.append(GameEvent(type=GameEventType.GAME_STARTED, tick=0, data={"players": state.players}))
        return state, events

    @staticmethod
    def validate_move(state: GameState, player: int, piece_id: str, to_row: int, to_col: int, *, ignore_cooldown: bool = False, path_context: PathClearContext | None = None) -> Move | None:
        if state.status != GameStatus.PLAYING:
            return None
        general = state.board.get_king(player)
        if general is None or general.captured:
            return None
        piece = state.board.get_piece_by_id(piece_id)
        if piece is None or piece.player != player or piece.captured:
            return None
        if is_piece_moving(piece_id, state.active_moves):
            return None
        if not ignore_cooldown and is_piece_on_cooldown(piece_id, state.cooldowns, state.current_tick):
            return None

        config = state.config
        castling = check_castling(piece, state.board, to_row, to_col, state.active_moves, cooldowns=state.cooldowns, current_tick=state.current_tick, ticks_per_square=config.ticks_per_square)
        if castling is not None:
            king_move, rook_move = castling
            king_move.start_tick = state.current_tick + 1
            rook_move.start_tick = state.current_tick + 1
            return king_move

        path = compute_move_path(piece, state.board, to_row, to_col, state.active_moves, current_tick=state.current_tick, ticks_per_square=config.ticks_per_square, path_context=path_context)
        if path is None:
            return None
        return Move(piece_id=piece_id, path=path, start_tick=state.current_tick + 1)

    @staticmethod
    def apply_move(state: GameState, move: Move) -> tuple[GameState, list[GameEvent]]:
        events: list[GameEvent] = []
        state.active_moves.append(move)
        piece = state.board.get_piece_by_id(move.piece_id)
        if piece is not None:
            end_row, end_col = move.end_position
            state.replay_moves.append(ReplayMove(tick=state.current_tick, piece_id=move.piece_id, to_row=int(end_row), to_col=int(end_col), player=piece.player))
            state.last_move_tick = state.current_tick
        events.append(GameEvent(type=GameEventType.MOVE_STARTED, tick=state.current_tick, data={"piece_id": move.piece_id, "path": move.path}))
        return state, events

    @staticmethod
    def tick(state: GameState) -> tuple[GameState, list[GameEvent]]:
        if state.status != GameStatus.PLAYING:
            return state, []
        events: list[GameEvent] = []
        state.current_tick += 1
        state.board.invalidate_position_map()
        config = state.config

        captures = detect_collisions(state.board.pieces, state.active_moves, state.current_tick, config.ticks_per_square)
        for capture in captures:
            captured_piece = state.board.get_piece_by_id(capture.captured_piece_id)
            if captured_piece is None:
                continue
            captured_piece.captured = True
            state.last_capture_tick = state.current_tick
            state.active_moves = [m for m in state.active_moves if m.piece_id != capture.captured_piece_id]
            state.cooldowns = [c for c in state.cooldowns if c.piece_id != capture.captured_piece_id]
            events.append(GameEvent(type=GameEventType.CAPTURE, tick=state.current_tick, data={"capturing_piece_id": capture.capturing_piece_id, "captured_piece_id": capture.captured_piece_id, "position": capture.position}))

        completed_moves: list[Move] = []
        for move in state.active_moves:
            total_ticks = move.num_squares * config.ticks_per_square
            if state.current_tick - move.start_tick >= total_ticks:
                completed_moves.append(move)

        for move in completed_moves:
            piece = state.board.get_piece_by_id(move.piece_id)
            if piece is not None and not piece.captured:
                end_row, end_col = move.end_position
                piece.row = float(end_row)
                piece.col = float(end_col)
                piece.moved = True
                state.cooldowns.append(Cooldown(piece_id=piece.id, start_tick=state.current_tick, duration=config.cooldown_ticks))
                events.append(GameEvent(type=GameEventType.MOVE_COMPLETED, tick=state.current_tick, data={"piece_id": move.piece_id, "position": (end_row, end_col)}))
                events.append(GameEvent(type=GameEventType.COOLDOWN_STARTED, tick=state.current_tick, data={"piece_id": piece.id, "duration": config.cooldown_ticks}))
                if should_promote_pawn(piece, state.board, int(end_row), int(end_col)):
                    events.append(GameEvent(type=GameEventType.PROMOTION, tick=state.current_tick, data={"piece_id": piece.id}))
            state.active_moves = [m for m in state.active_moves if m.piece_id != move.piece_id]

        active_cooldowns = []
        for cooldown in state.cooldowns:
            if cooldown.is_active(state.current_tick):
                active_cooldowns.append(cooldown)
            else:
                piece = state.board.get_piece_by_id(cooldown.piece_id)
                if piece is not None:
                    piece.cooldown_end_tick = state.current_tick
                    events.append(GameEvent(type=GameEventType.COOLDOWN_ENDED, tick=state.current_tick, data={"piece_id": piece.id}))
        state.cooldowns = active_cooldowns

        winner, win_reason = GameEngine.check_winner(state)
        if winner is not None:
            state.status = GameStatus.FINISHED
            state.finished_at = datetime.now(UTC)
            state.winner = winner
            state.win_reason = win_reason
            if winner == 0:
                events.append(GameEvent(type=GameEventType.DRAW, tick=state.current_tick, data={}))
            else:
                events.append(GameEvent(type=GameEventType.GAME_OVER, tick=state.current_tick, data={"winner": winner}))
        return state, events

    @staticmethod
    def check_winner(state: GameState) -> tuple[int | None, WinReason | None]:
        config = state.config
        players_with_general: list[int] = []
        for player_num in state.players.keys():
            general = state.board.get_king(player_num)
            if general is not None and not general.captured:
                players_with_general.append(player_num)
        if len(players_with_general) == 1:
            return players_with_general[0], WinReason.KING_CAPTURED
        if len(players_with_general) == 0:
            return 0, WinReason.DRAW
        if state.is_campaign:
            if state.current_tick - state.last_move_tick >= CAMPAIGN_DRAW_NO_MOVE_TICKS:
                return 0, WinReason.DRAW
            return None, None
        if state.current_tick < config.min_draw_ticks:
            return None, None
        if state.current_tick - state.last_move_tick >= config.draw_no_move_ticks or state.current_tick - state.last_capture_tick >= config.draw_no_capture_ticks:
            return 0, WinReason.DRAW
        return None, None

    @staticmethod
    def get_legal_moves(state: GameState, player: int) -> list[tuple[str, int, int]]:
        return GameEngine.get_legal_moves_fast(state, player)

    @staticmethod
    def get_legal_moves_fast(state: GameState, player: int, *, ignore_cooldown: bool = False) -> list[tuple[str, int, int]]:
        legal_moves: list[tuple[str, int, int]] = []
        general = state.board.get_king(player)
        if general is None or general.captured:
            return legal_moves
        config = state.config
        ctx = build_path_clear_context(player, state.board, state.active_moves, state.current_tick, config.ticks_per_square)
        for piece in state.board.get_pieces_for_player(player):
            if piece.captured or piece.id in ctx.moving_piece_ids:
                continue
            if not ignore_cooldown and is_piece_on_cooldown(piece.id, state.cooldowns, state.current_tick):
                continue
            for to_row, to_col in _get_piece_candidates(piece, state.board):
                path = compute_move_path(piece, state.board, to_row, to_col, state.active_moves, current_tick=state.current_tick, ticks_per_square=config.ticks_per_square, path_context=ctx)
                if path is not None:
                    legal_moves.append((piece.id, to_row, to_col))
        return legal_moves

    @staticmethod
    def get_piece_state(state: GameState, piece_id: str) -> dict | None:
        piece = state.board.get_piece_by_id(piece_id)
        if piece is None:
            return None
        config = state.config
        interp_pos = get_interpolated_position(piece, state.active_moves, state.current_tick, config.ticks_per_square)
        on_cooldown = is_piece_on_cooldown(piece_id, state.cooldowns, state.current_tick)
        cooldown_remaining = 0
        if on_cooldown:
            for cd in state.cooldowns:
                if cd.piece_id == piece_id:
                    cooldown_remaining = max(0, (cd.start_tick + cd.duration) - state.current_tick)
                    break
        return {
            "id": piece.id,
            "type": piece.type.value,
            "player": piece.player,
            "row": interp_pos[0],
            "col": interp_pos[1],
            "captured": piece.captured,
            "moving": is_piece_moving(piece_id, state.active_moves),
            "on_cooldown": on_cooldown,
            "cooldown_remaining": cooldown_remaining,
        }


def _get_piece_candidates(piece: Piece, board: Board) -> list[tuple[int, int]]:
    from_row, from_col = piece.grid_position
    candidates: list[tuple[int, int]] = []
    if piece.type in (PieceType.SOLDIER, PieceType.PAWN):
        forward = -1 if piece.player == 1 else 1
        candidates.append((from_row + forward, from_col))
        if board.has_crossed_river(piece.player, from_row):
            candidates.extend([(from_row, from_col - 1), (from_row, from_col + 1)])
    elif piece.type in (PieceType.HORSE, PieceType.KNIGHT):
        for dr, dc in [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]:
            candidates.append((from_row + dr, from_col + dc))
    elif piece.type in (PieceType.ELEPHANT, PieceType.BISHOP):
        for dr, dc in [(-2, -2), (-2, 2), (2, -2), (2, 2)]:
            candidates.append((from_row + dr, from_col + dc))
    elif piece.type in (PieceType.ADVISOR, PieceType.QUEEN):
        for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            candidates.append((from_row + dr, from_col + dc))
    elif piece.type in (PieceType.GENERAL, PieceType.KING):
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            candidates.append((from_row + dr, from_col + dc))
        enemy = board.get_king(2 if piece.player == 1 else 1)
        if enemy is not None and not enemy.captured:
            candidates.append(enemy.grid_position)
    elif piece.type in (PieceType.CHARIOT, PieceType.ROOK, PieceType.CANNON):
        for r in range(board.height):
            if r != from_row:
                candidates.append((r, from_col))
        for c in range(board.width):
            if c != from_col:
                candidates.append((from_row, c))
    return [(r, c) for r, c in candidates if board.is_valid_square(r, c)]

from __future__ import annotations

from app.domain.enums import BOARD_HEIGHT, BOARD_WIDTH, PieceType
from app.domain.models import MatchState, MovePath, RuleResult


class RulesEngine:
    @staticmethod
    def validate_move(state: MatchState, player: int, piece_id: str, tx: int, ty: int, now: float) -> RuleResult:
        piece = state.pieces.get(piece_id)
        if piece is None or not piece.alive:
            return RuleResult(False, "棋子不存在")
        if piece.player != player:
            return RuleResult(False, "不能操作对方棋子")
        if piece.moving:
            return RuleResult(False, "棋子正在移动")
        if piece.cooldown_until > now:
            return RuleResult(False, "棋子冷却中")
        if not (0 <= tx < BOARD_WIDTH and 0 <= ty < BOARD_HEIGHT):
            return RuleResult(False, "目标越界")
        if (piece.x, piece.y) == (tx, ty):
            return RuleResult(False, "目标点不能是原地")
        if piece.piece_type not in state.unlocks[player].unlocked:
            return RuleResult(False, "该棋种尚未解锁")

        target_piece = _piece_at(state, tx, ty)
        if target_piece and target_piece.player == player:
            return RuleResult(False, "不能吃己方棋子")

        checker = {
            PieceType.SOLDIER: _soldier,
            PieceType.ADVISOR: _advisor,
            PieceType.ELEPHANT: _elephant,
            PieceType.HORSE: _horse,
            PieceType.CANNON: _cannon,
            PieceType.CHARIOT: _chariot,
            PieceType.GENERAL: _general,
        }[piece.piece_type]

        result = checker(state, piece_id, tx, ty)
        if not result.ok:
            return result

        if _generals_face_after_move(state, piece_id, tx, ty):
            return RuleResult(False, "将帅不能隔空照面")
        return result


def _piece_at(state: MatchState, x: int, y: int):
    for p in state.pieces.values():
        if p.alive and p.x == x and p.y == y:
            return p
    return None


def _count_between_file(state: MatchState, x: int, y1: int, y2: int, ignore: set[str]) -> int:
    lo, hi = sorted((y1, y2))
    count = 0
    for p in state.pieces.values():
        if not p.alive or p.piece_id in ignore:
            continue
        if p.x == x and lo < p.y < hi:
            count += 1
    return count


def _count_between_rank(state: MatchState, y: int, x1: int, x2: int, ignore: set[str]) -> int:
    lo, hi = sorted((x1, x2))
    count = 0
    for p in state.pieces.values():
        if not p.alive or p.piece_id in ignore:
            continue
        if p.y == y and lo < p.x < hi:
            count += 1
    return count


def _soldier(state: MatchState, piece_id: str, tx: int, ty: int) -> RuleResult:
    p = state.pieces[piece_id]
    dx = tx - p.x
    dy = ty - p.y
    if abs(dx) + abs(dy) != 1:
        return RuleResult(False, "兵/卒只能一步")
    forward = -1 if p.player == 1 else 1
    crossed = p.y <= 4 if p.player == 1 else p.y >= 5
    if dy == -forward:
        return RuleResult(False, "兵/卒不能后退")
    if dy == forward and dx == 0:
        return RuleResult(True, "ok", MovePath(1.0, [(tx, ty)]))
    if crossed and dy == 0 and abs(dx) == 1:
        return RuleResult(True, "ok", MovePath(1.0, [(tx, ty)]))
    return RuleResult(False, "兵/卒走法不合法")


def _advisor(state: MatchState, piece_id: str, tx: int, ty: int) -> RuleResult:
    p = state.pieces[piece_id]
    if abs(tx - p.x) != 1 or abs(ty - p.y) != 1:
        return RuleResult(False, "士需斜走一步")
    if tx not in (3, 4, 5):
        return RuleResult(False, "士必须在九宫")
    if p.player == 1 and ty not in (7, 8, 9):
        return RuleResult(False, "士必须在九宫")
    if p.player == 2 and ty not in (0, 1, 2):
        return RuleResult(False, "士必须在九宫")
    return RuleResult(True, "ok", MovePath(1.0, [(tx, ty)]))


def _elephant(state: MatchState, piece_id: str, tx: int, ty: int) -> RuleResult:
    p = state.pieces[piece_id]
    dx = tx - p.x
    dy = ty - p.y
    if abs(dx) != 2 or abs(dy) != 2:
        return RuleResult(False, "象需走田字")
    eye = (p.x + dx // 2, p.y + dy // 2)
    if _piece_at(state, eye[0], eye[1]):
        return RuleResult(False, "象眼被塞")
    if p.player == 1 and ty < 5:
        return RuleResult(False, "象不能过河")
    if p.player == 2 and ty > 4:
        return RuleResult(False, "象不能过河")
    return RuleResult(True, "ok", MovePath(2.0, [eye, (tx, ty)]))


def _horse(state: MatchState, piece_id: str, tx: int, ty: int) -> RuleResult:
    p = state.pieces[piece_id]
    dx = tx - p.x
    dy = ty - p.y
    if (abs(dx), abs(dy)) not in {(1, 2), (2, 1)}:
        return RuleResult(False, "马走日")
    if abs(dx) == 2:
        leg = (p.x + dx // 2, p.y)
    else:
        leg = (p.x, p.y + dy // 2)
    if _piece_at(state, leg[0], leg[1]):
        return RuleResult(False, "马腿被蹩")
    return RuleResult(True, "ok", MovePath(2.0, [leg, (tx, ty)]))


def _cannon(state: MatchState, piece_id: str, tx: int, ty: int) -> RuleResult:
    p = state.pieces[piece_id]
    if p.x != tx and p.y != ty:
        return RuleResult(False, "炮需走直线")
    target = _piece_at(state, tx, ty)
    if p.x == tx:
        between = _count_between_file(state, tx, p.y, ty, {piece_id})
    else:
        between = _count_between_rank(state, ty, p.x, tx, {piece_id})
    dist = abs(tx - p.x) + abs(ty - p.y)
    if target is None and between == 0:
        return RuleResult(True, "ok", MovePath(float(dist), [(tx, ty)]))
    if target is not None and between == 1:
        return RuleResult(True, "ok", MovePath(float(dist), [(tx, ty)]))
    return RuleResult(False, "炮走法不合法（需隔一子吃）")


def _chariot(state: MatchState, piece_id: str, tx: int, ty: int) -> RuleResult:
    p = state.pieces[piece_id]
    if p.x != tx and p.y != ty:
        return RuleResult(False, "车需走直线")
    if p.x == tx:
        between = _count_between_file(state, tx, p.y, ty, {piece_id})
    else:
        between = _count_between_rank(state, ty, p.x, tx, {piece_id})
    if between != 0:
        return RuleResult(False, "车被阻挡")
    dist = abs(tx - p.x) + abs(ty - p.y)
    return RuleResult(True, "ok", MovePath(float(dist), [(tx, ty)]))


def _general(state: MatchState, piece_id: str, tx: int, ty: int) -> RuleResult:
    p = state.pieces[piece_id]
    enemy_general = next(
        ep for ep in state.pieces.values() if ep.alive and ep.piece_type == PieceType.GENERAL and ep.player != p.player
    )
    # Flying general capture.
    if tx == enemy_general.x and ty == enemy_general.y and p.x == enemy_general.x:
        between = _count_between_file(state, p.x, p.y, enemy_general.y, {piece_id, enemy_general.piece_id})
        if between == 0:
            dist = abs(enemy_general.y - p.y)
            return RuleResult(True, "ok", MovePath(float(dist), [(tx, ty)]))

    dx = abs(tx - p.x)
    dy = abs(ty - p.y)
    if dx + dy != 1:
        return RuleResult(False, "将/帅只能直走一步")
    if tx not in (3, 4, 5):
        return RuleResult(False, "将/帅必须在九宫")
    if p.player == 1 and ty not in (7, 8, 9):
        return RuleResult(False, "将/帅必须在九宫")
    if p.player == 2 and ty not in (0, 1, 2):
        return RuleResult(False, "将/帅必须在九宫")
    return RuleResult(True, "ok", MovePath(1.0, [(tx, ty)]))


def _generals_face_after_move(state: MatchState, moving_piece_id: str, tx: int, ty: int) -> bool:
    moving_piece = state.pieces[moving_piece_id]
    enemy_general = next((p for p in state.pieces.values() if p.alive and p.piece_type == PieceType.GENERAL and p.player != moving_piece.player), None)
    if enemy_general is not None and (tx, ty) == (enemy_general.x, enemy_general.y):
        return False

    generals: dict[int, tuple[int, int, str]] = {}
    for p in state.pieces.values():
        if not p.alive:
            continue
        x, y = p.x, p.y
        if p.piece_id == moving_piece_id:
            x, y = tx, ty
        if p.piece_type == PieceType.GENERAL:
            generals[p.player] = (x, y, p.piece_id)

    if 1 not in generals or 2 not in generals:
        return False
    x1, y1, gid1 = generals[1]
    x2, y2, gid2 = generals[2]
    if x1 != x2:
        return False
    between = _count_between_file(state, x1, y1, y2, {moving_piece_id, gid1, gid2})

    # moving piece may newly block between
    if moving_piece_id not in {gid1, gid2} and tx == x1 and min(y1, y2) < ty < max(y1, y2):
        between += 1

    return between == 0

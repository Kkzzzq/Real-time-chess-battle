from __future__ import annotations

import time

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_container
from app.domain.enums import MatchStatus
from app.engine.move_rules import list_legal_targets
from app.engine.phase import compute_phase, is_piece_kind_allowed_by_phase
from app.engine.snapshot import build_board_snapshot, build_match_snapshot, build_unlock_snapshot

router = APIRouter(prefix="/matches/{match_id}", tags=["query"])


def _get_state_or_404(container, match_id: str):
    s = container.repo.get_match(match_id)
    if not s:
        raise HTTPException(404, "match not found")
    return s


def _reconcile(container, match_id: str, now_ms: int):
    container.match_service.tick_once(match_id, now_ms)


@router.get("/state")
def state(match_id: str, container=Depends(get_container)):
    now_ms = int(time.time() * 1000)
    _reconcile(container, match_id, now_ms)
    s = _get_state_or_404(container, match_id)
    return build_match_snapshot(s, now_ms)


@router.get("/snapshot/full")
def full_snapshot(match_id: str, container=Depends(get_container)):
    now_ms = int(time.time() * 1000)
    _reconcile(container, match_id, now_ms)
    s = _get_state_or_404(container, match_id)
    return build_match_snapshot(s, now_ms)


@router.get("/phase")
def phase(match_id: str, container=Depends(get_container)):
    now_ms = int(time.time() * 1000)
    _reconcile(container, match_id, now_ms)
    s = _get_state_or_404(container, match_id)
    name, deadline, wave = compute_phase(now_ms, s.started_at)
    return {"name": name, "deadline_ms": deadline, "wave_index": wave, "remaining_ms": None if deadline is None else max(0, deadline - now_ms)}


@router.get("/unlock-state")
def unlock_state(match_id: str, container=Depends(get_container)):
    now_ms = int(time.time() * 1000)
    _reconcile(container, match_id, now_ms)
    s = _get_state_or_404(container, match_id)
    return build_unlock_snapshot(s, now_ms)


@router.get("/unlock-state")
def unlock_state(match_id: str, container=Depends(get_container)):
    s = _get_state_or_404(container, match_id)
    return build_unlock_snapshot(s, int(time.time() * 1000))


@router.get("/events")
def events(match_id: str, container=Depends(get_container)):
    now_ms = int(time.time() * 1000)
    _reconcile(container, match_id, now_ms)
    s = _get_state_or_404(container, match_id)
    return [{"type": e.event_type, "ts_ms": e.ts_ms, "payload": e.payload} for e in s.event_log]


@router.get("/board")
def board(match_id: str, container=Depends(get_container)):
    now_ms = int(time.time() * 1000)
    _reconcile(container, match_id, now_ms)
    s = _get_state_or_404(container, match_id)
    return build_board_snapshot(s, now_ms)


@router.get("/pieces/{piece_id}/legal-moves")
def legal_moves(match_id: str, piece_id: str, player: int | None = Query(default=None), container=Depends(get_container)):
    now_ms = int(time.time() * 1000)
    _reconcile(container, match_id, now_ms)
    s = _get_state_or_404(container, match_id)
    if piece_id not in s.pieces:
        raise HTTPException(404, "piece not found")

    piece = s.pieces[piece_id]
    if player is not None and piece.owner != player:
        raise HTTPException(403, "not your piece")

    executable = (
        s.status == MatchStatus.RUNNING
        and piece.alive
        and not piece.is_moving
        and piece.cooldown_end_at <= now_ms
        and (player is None or is_piece_kind_allowed_by_phase(player, piece.kind, s, now_ms))
        and (player is None or piece.kind in s.unlocked_by_player.get(player, set()))
    )
    return {
        "piece_id": piece_id,
        "targets": list_legal_targets(piece, s, now_ms),
        "executable": executable,
        "reason": None if executable else "piece_not_commandable_now",
    }


@router.get("/players")
def players(match_id: str, container=Depends(get_container)):
    s = _get_state_or_404(container, match_id)
    return s.players

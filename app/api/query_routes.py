from __future__ import annotations

import time

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.auth import resolve_viewer_seat_with_auth
from app.api.deps import get_container
from app.api.schemas import LegalMovesResponse, MatchSnapshotResponse
from app.domain.enums import MatchStatus
from app.engine.move_rules import list_legal_targets, validate_move
from app.engine.phase import is_piece_kind_allowed_by_phase
from app.engine.snapshot import build_board_snapshot, build_match_snapshot, build_unlock_snapshot

router = APIRouter(prefix="/matches/{match_id}", tags=["query"])


def _get_state_or_404(container, match_id: str):
    s = container.repo.get_match(match_id)
    if not s:
        raise HTTPException(404, "match not found")
    return s


@router.get("/state", response_model=MatchSnapshotResponse)
def state(
    match_id: str,
    player_id: str | None = Query(default=None),
    player_token: str | None = Query(default=None),
    container=Depends(get_container),
):
    now_ms = int(time.time() * 1000)
    s = _get_state_or_404(container, match_id)
    viewer_seat = resolve_viewer_seat_with_auth(s, player_id, player_token)
    return build_match_snapshot(s, now_ms, viewer_seat=viewer_seat)


@router.get("/phase")
def phase(match_id: str, container=Depends(get_container)):
    now_ms = int(time.time() * 1000)
    s = _get_state_or_404(container, match_id)
    return build_match_snapshot(s, now_ms)["phase"]


@router.get("/unlock-state")
def unlock_state(match_id: str, container=Depends(get_container)):
    now_ms = int(time.time() * 1000)
    s = _get_state_or_404(container, match_id)
    return build_unlock_snapshot(s, now_ms)


@router.get("/events")
def events(match_id: str, container=Depends(get_container)):
    s = _get_state_or_404(container, match_id)
    return [{"type": e.event_type, "ts_ms": e.ts_ms, "payload": e.payload} for e in s.event_log]


@router.get("/board")
def board(match_id: str, container=Depends(get_container)):
    now_ms = int(time.time() * 1000)
    s = _get_state_or_404(container, match_id)
    return {"board": build_board_snapshot(s, now_ms), "runtime_board": build_board_snapshot(s, now_ms, runtime=True)}


@router.get("/pieces/{piece_id}/legal-moves", response_model=LegalMovesResponse)
def legal_moves(
    match_id: str,
    piece_id: str,
    player_id: str | None = Query(default=None),
    player_token: str | None = Query(default=None),
    container=Depends(get_container),
):
    now_ms = int(time.time() * 1000)
    s = _get_state_or_404(container, match_id)
    if piece_id not in s.pieces:
        raise HTTPException(404, "piece not found")

    piece = s.pieces[piece_id]
    viewer_seat = resolve_viewer_seat_with_auth(s, player_id, player_token)

    static_targets = list_legal_targets(piece, s, now_ms)
    actionable_targets: list[tuple[int, int]] = []

    owner_view_executable = (
        s.status == MatchStatus.RUNNING
        and piece.alive
        and not piece.is_moving
        and piece.cooldown_end_at <= now_ms
        and is_piece_kind_allowed_by_phase(piece.owner, piece.kind, s, now_ms)
        and piece.kind in s.unlocked_by_player.get(piece.owner, set())
    )
    if player_id is not None and viewer_seat == piece.owner and owner_view_executable:
        for target in static_targets:
            ok, _ = validate_move(piece, target, s, now_ms)
            if ok:
                actionable_targets.append(target)

    executable = len(actionable_targets) > 0
    actionable = None
    if player_id is not None:
        if viewer_seat != piece.owner:
            reason = "not_piece_owner"
        elif not owner_view_executable:
            reason = "piece_not_commandable_now"
        elif not executable:
            reason = "no_actionable_targets"
        else:
            reason = None
        actionable = {
            "viewer_seat": viewer_seat,
            "actionable_targets": actionable_targets,
            "executable": executable,
            "actionable_context": "viewer_context_provided",
            "reason": reason,
        }

    return {
        "piece_id": piece_id,
        "owner": piece.owner,
        "player_id": player_id,
        "static": {"targets": static_targets},
        "actionable": actionable,
    }


@router.get("/players")
def players(match_id: str, container=Depends(get_container)):
    s = _get_state_or_404(container, match_id)
    out = {}
    for seat, info in s.players.items():
        out[str(seat)] = {
            "seat": seat,
            "player_id": info.get("player_id"),
            "name": info.get("name"),
            "ready": bool(info.get("ready", False)),
            "online": bool(info.get("online", False)),
            "is_host": bool(info.get("is_host", False)),
        }
    return out

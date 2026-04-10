from __future__ import annotations

import time

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_container
from app.engine.move_rules import list_legal_targets
from app.engine.snapshot import build_match_snapshot

router = APIRouter(prefix="/matches/{match_id}", tags=["query"])


@router.get("/state")
def state(match_id: str, container=Depends(get_container)):
    s = container.repo.get_match(match_id)
    if not s:
        raise HTTPException(404, "match not found")
    return build_match_snapshot(s, int(time.time() * 1000))


@router.get("/phase")
def phase(match_id: str, container=Depends(get_container)):
    s = container.repo.get_match(match_id)
    if not s:
        raise HTTPException(404, "match not found")
    return {"name": s.phase_name, "deadline_ms": s.phase_deadline_ms, "wave_index": s.wave_index}


@router.get("/events")
def events(match_id: str, container=Depends(get_container)):
    s = container.repo.get_match(match_id)
    if not s:
        raise HTTPException(404, "match not found")
    return [{"type": e.event_type, "ts_ms": e.ts_ms, "payload": e.payload} for e in s.event_log]


@router.get("/pieces/{piece_id}/legal-moves")
def legal_moves(match_id: str, piece_id: str, container=Depends(get_container)):
    s = container.repo.get_match(match_id)
    if not s or piece_id not in s.pieces:
        raise HTTPException(404, "not found")
    return {"piece_id": piece_id, "targets": list_legal_targets(s.pieces[piece_id], s)}


@router.get("/players")
def players(match_id: str, container=Depends(get_container)):
    s = container.repo.get_match(match_id)
    if not s:
        raise HTTPException(404, "match not found")
    return s.players

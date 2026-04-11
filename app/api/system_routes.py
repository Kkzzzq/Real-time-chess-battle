from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_container

router = APIRouter(tags=["system"])


@router.get('/health')
def health():
    return {"ok": True, "status": "healthy"}


@router.get('/ready')
def ready(container=Depends(get_container)):
    return {"ok": True, "status": "ready", "repo_backend": container.repo.__class__.__name__}


@router.get('/metrics')
def metrics(container=Depends(get_container)):
    matches = container.repo.list_matches()
    running = [m for m in matches if m.status.value == 'running']
    return {
        "matches_total": len(matches),
        "matches_running": len(running),
        "ws_active_matches": container.broadcaster.active_matches(),
        "ws_active_connections": container.broadcaster.active_connections(),
    }

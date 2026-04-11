from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["system"])


@router.get('/health')
def health():
    return {"ok": True, "status": "healthy"}


@router.get('/ready')
def ready():
    return {"ok": True, "status": "ready"}


@router.get('/metrics')
def metrics():
    # Placeholder metrics endpoint for ops integration.
    return {"matches": "n/a", "connections": "n/a"}

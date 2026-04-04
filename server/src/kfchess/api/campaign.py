"""Campaign API endpoints.

第一版已冻结/下线：当前版本只保留双人实时中国象棋主链路。
"""

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/campaign", tags=["campaign"])

_DETAIL = "Campaign mode is disabled in v1. Only 2-player real-time xiangqi is supported now."


def _disabled() -> None:
    raise HTTPException(status_code=503, detail=_DETAIL)


@router.get("/progress")
async def get_progress_disabled():
    _disabled()


@router.get("/progress/{user_id}")
async def get_user_progress_disabled(user_id: int):
    del user_id
    _disabled()


@router.get("/levels")
async def list_levels_disabled():
    _disabled()


@router.get("/levels/{level_id}")
async def get_level_info_disabled(level_id: int):
    del level_id
    _disabled()


@router.post("/levels/{level_id}/start")
async def start_level_disabled(level_id: int):
    del level_id
    _disabled()

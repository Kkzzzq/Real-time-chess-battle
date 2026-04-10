from __future__ import annotations

from dataclasses import dataclass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.api.command_routes import router as command_router
from app.api.match_routes import router as match_router
from app.api.query_routes import router as query_router
from app.api.ws_routes import router as ws_router
from app.repository.memory_repo import MemoryRepo
from app.runtime.broadcaster import Broadcaster
from app.runtime.tick_loop import TickLoop
from app.services.command_service import CommandService
from app.services.match_service import MatchService
from app.services.room_service import RoomService


@dataclass
class AppContainer:
    repo: MemoryRepo
    room_service: RoomService
    command_service: CommandService
    match_service: MatchService
    broadcaster: Broadcaster
    tick_loop: TickLoop


repo = MemoryRepo()
room_service = RoomService(repo)
command_service = CommandService(repo)
match_service = MatchService(repo)
broadcaster = Broadcaster()
tick_loop = TickLoop(match_service, broadcaster)
app_container = AppContainer(repo, room_service, command_service, match_service, broadcaster, tick_loop)

app = FastAPI(title="Realtime Xiangqi")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(match_router)
app.include_router(command_router)
app.include_router(query_router)
app.include_router(ws_router)


@app.get("/demo")
def demo() -> FileResponse:
    return FileResponse("app/web/demo.html")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    await tick_loop.shutdown()

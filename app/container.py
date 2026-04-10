from __future__ import annotations

from dataclasses import dataclass

from app.repository.memory_repo import MemoryRepo
from app.runtime.broadcaster import Broadcaster
from app.runtime.tick_loop import TickLoop
from app.services.command_service import CommandService
from app.services.match_service import MatchService
from app.services.room_service import RoomService


@dataclass
class AppContainer:
    """Application wiring container.

    This object is the single place responsible for constructing and connecting
    repositories, services, and runtime components.
    """

    repo: MemoryRepo
    room_service: RoomService
    command_service: CommandService
    match_service: MatchService
    broadcaster: Broadcaster
    tick_loop: TickLoop


def build_container() -> AppContainer:
    repo = MemoryRepo()
    room_service = RoomService(repo)
    command_service = CommandService(repo)
    match_service = MatchService(repo)
    broadcaster = Broadcaster()
    tick_loop = TickLoop(match_service, broadcaster)
    return AppContainer(
        repo=repo,
        room_service=room_service,
        command_service=command_service,
        match_service=match_service,
        broadcaster=broadcaster,
        tick_loop=tick_loop,
    )

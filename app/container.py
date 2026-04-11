from __future__ import annotations

import os
from dataclasses import dataclass

from app.repository.base import MatchRepo
from app.repository.memory_repo import MemoryRepo
from app.repository.pickle_repo import PickleRepo
from app.runtime.broadcaster import Broadcaster
from app.runtime.tick_loop import TickLoop
from app.services.command_service import CommandService
from app.services.match_service import MatchService
from app.services.room_service import RoomService


@dataclass
class AppContainer:
    repo: MatchRepo
    room_service: RoomService
    command_service: CommandService
    match_service: MatchService
    broadcaster: Broadcaster
    tick_loop: TickLoop


def _build_repo() -> MatchRepo:
    backend = os.getenv('MATCH_REPO_BACKEND', 'memory').lower()
    if backend == 'pickle':
        return PickleRepo(path=os.getenv('MATCH_REPO_PICKLE_PATH', '.data/matches.pkl'))
    return MemoryRepo()


def build_container() -> AppContainer:
    repo = _build_repo()
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

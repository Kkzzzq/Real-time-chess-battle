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
from app.services.persistence_service import PersistenceService
from app.services.player_session_service import PlayerSessionService
from app.services.room_service import RoomService


@dataclass
class AppContainer:
    repo: MatchRepo
    room_service: RoomService
    command_service: CommandService
    match_service: MatchService
    broadcaster: Broadcaster
    tick_loop: TickLoop
    persistence_service: PersistenceService


def _build_repo() -> MatchRepo:
    backend = os.getenv("MATCH_REPO_BACKEND", "memory").lower()
    if backend == "pickle":
        return PickleRepo(path=os.getenv("MATCH_REPO_PICKLE_PATH", ".data/matches.pkl"))
    return MemoryRepo()


def _build_persistence(repo: MatchRepo):
    mysql_enabled = os.getenv("MYSQL_ENABLED", "0") == "1"
    redis_enabled = os.getenv("REDIS_ENABLED", "0") == "1"

    runtime_repo = None
    presence_repo = None
    session_cache_repo = None
    mysql_match_repo = None
    mysql_player_repo = None
    mysql_event_repo = None
    mysql_session_repo = None
    archive_service = None

    if redis_enabled:
        from redis import Redis

        from app.repository.redis.presence_repo_redis import RedisPresenceRepo
        from app.repository.redis.runtime_repo_redis import RedisRuntimeRepo
        from app.repository.redis.session_cache_repo_redis import RedisSessionCacheRepo

        redis_dsn = os.getenv("REDIS_DSN", "redis://127.0.0.1:6379/0")
        client = Redis.from_url(redis_dsn, decode_responses=True)
        runtime_repo = RedisRuntimeRepo(client)
        presence_repo = RedisPresenceRepo(client)
        session_cache_repo = RedisSessionCacheRepo(client)

    if mysql_enabled:
        from app.db.session import SessionLocal
        from app.repository.mysql.event_repo_mysql import MySQLEventRepo
        from app.repository.mysql.match_repo_mysql import MySQLMatchRepo
        from app.repository.mysql.player_repo_mysql import MySQLPlayerRepo
        from app.repository.mysql.session_repo_mysql import MySQLSessionRepo
        from app.services.match_archive_service import MatchArchiveService

        mysql_match_repo = MySQLMatchRepo(SessionLocal)
        mysql_player_repo = MySQLPlayerRepo(SessionLocal)
        mysql_event_repo = MySQLEventRepo(SessionLocal)
        mysql_session_repo = MySQLSessionRepo(SessionLocal)
        archive_service = MatchArchiveService(mysql_match_repo, mysql_event_repo, mysql_player_repo)

    return (
        PersistenceService(
            match_repo=repo,
            runtime_repo=runtime_repo,
            presence_repo=presence_repo,
            session_cache_repo=session_cache_repo,
            mysql_match_repo=mysql_match_repo,
            mysql_player_repo=mysql_player_repo,
            mysql_event_repo=mysql_event_repo,
            mysql_session_repo=mysql_session_repo,
        ),
        archive_service,
    )


def build_container() -> AppContainer:
    repo = _build_repo()
    persistence_service, archive_service = _build_persistence(repo)
    session_service = PlayerSessionService(int(os.getenv("PLAYER_TOKEN_TTL_SECONDS", "86400")), persistence_service=persistence_service)
    room_service = RoomService(repo, session_service=session_service, persistence_service=persistence_service)
    command_service = CommandService(repo, persistence_service=persistence_service)
    match_service = MatchService(repo, persistence_service=persistence_service, archive_service=archive_service)
    broadcaster = Broadcaster()
    tick_loop = TickLoop(match_service, broadcaster)

    return AppContainer(
        repo=repo,
        room_service=room_service,
        command_service=command_service,
        match_service=match_service,
        broadcaster=broadcaster,
        tick_loop=tick_loop,
        persistence_service=persistence_service,
    )

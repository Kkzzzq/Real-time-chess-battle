from __future__ import annotations

import os
<<<<<<< HEAD
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

DEFAULT_MYSQL_DSN = "mysql+pymysql://root:root@127.0.0.1:3306/rtcb"


def get_mysql_dsn() -> str:
    return os.getenv("MYSQL_DSN", DEFAULT_MYSQL_DSN)


def build_engine(echo: bool = False):
    pool_size = int(os.getenv("MYSQL_POOL_SIZE", "5"))
    max_overflow = int(os.getenv("MYSQL_MAX_OVERFLOW", "10"))
    return create_engine(
        get_mysql_dsn(),
        pool_pre_ping=True,
        pool_size=pool_size,
        max_overflow=max_overflow,
        echo=echo,
        future=True,
    )


ENGINE = build_engine(echo=os.getenv("SQL_ECHO", "0") == "1")
SessionLocal = sessionmaker(bind=ENGINE, autoflush=False, autocommit=False, expire_on_commit=False, class_=Session)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
=======
from dataclasses import dataclass


@dataclass(frozen=True)
class DBSettings:
    dsn: str


def get_db_settings() -> DBSettings:
    dsn = os.getenv("MYSQL_DSN", "mysql+pymysql://root:root@localhost:3306/rtcb")
    return DBSettings(dsn=dsn)
>>>>>>> origin/main

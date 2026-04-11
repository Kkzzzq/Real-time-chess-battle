from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class DBSettings:
    dsn: str


def get_db_settings() -> DBSettings:
    dsn = os.getenv("MYSQL_DSN", "mysql+pymysql://root:root@localhost:3306/rtcb")
    return DBSettings(dsn=dsn)

from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MatchRecord(Base):
    __tablename__ = "matches"

    match_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    ruleset_name: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False)
    started_at: Mapped[int | None] = mapped_column(BigInteger)
    ended_at: Mapped[int | None] = mapped_column(BigInteger)
    winner: Mapped[int | None] = mapped_column(Integer)
    result_reason: Mapped[str | None] = mapped_column(String(128))
    allow_draw: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    tick_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    host_player_id: Mapped[str | None] = mapped_column(String(64))
    ruleset_snapshot_json: Mapped[str | None] = mapped_column(Text)


class PlayerRecord(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    player_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    match_id: Mapped[str] = mapped_column(String(64), ForeignKey("matches.match_id", ondelete="CASCADE"), nullable=False, index=True)
    seat: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    is_host: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    ready: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    online: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    joined_at: Mapped[int] = mapped_column(BigInteger, nullable=False)
    left_at: Mapped[int | None] = mapped_column(BigInteger)


class MatchEventRecord(Base):
    __tablename__ = "match_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    match_id: Mapped[str] = mapped_column(String(64), ForeignKey("matches.match_id", ondelete="CASCADE"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    ts_ms: Mapped[int] = mapped_column(BigInteger, nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)


class PlayerSessionRecord(Base):
    __tablename__ = "player_sessions"

    player_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    match_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    token_value: Mapped[str] = mapped_column(String(256), nullable=False)
    issued_at_ms: Mapped[int] = mapped_column(BigInteger, nullable=False)
    expires_at_ms: Mapped[int] = mapped_column(BigInteger, nullable=False)

"""create mysql/redis aligned storage tables

Revision ID: 0001_create_storage_tables
Revises:
Create Date: 2026-04-11
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_create_storage_tables"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "matches",
        sa.Column("match_id", sa.String(length=64), primary_key=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("ruleset_name", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
        sa.Column("started_at", sa.BigInteger(), nullable=True),
        sa.Column("ended_at", sa.BigInteger(), nullable=True),
        sa.Column("winner", sa.Integer(), nullable=True),
        sa.Column("result_reason", sa.String(length=128), nullable=True),
        sa.Column("allow_draw", sa.Boolean(), nullable=False),
        sa.Column("tick_ms", sa.Integer(), nullable=False),
        sa.Column("host_player_id", sa.String(length=64), nullable=True),
        sa.Column("ruleset_snapshot_json", sa.Text(), nullable=True),
    )
    op.create_table(
        "players",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("player_id", sa.String(length=64), nullable=False),
        sa.Column("match_id", sa.String(length=64), sa.ForeignKey("matches.match_id", ondelete="CASCADE"), nullable=False),
        sa.Column("seat", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("is_host", sa.Boolean(), nullable=False),
        sa.Column("ready", sa.Boolean(), nullable=False),
        sa.Column("online", sa.Boolean(), nullable=False),
        sa.Column("joined_at", sa.BigInteger(), nullable=False),
        sa.Column("left_at", sa.BigInteger(), nullable=True),
    )
    op.create_table(
        "match_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("match_id", sa.String(length=64), sa.ForeignKey("matches.match_id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("ts_ms", sa.BigInteger(), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
    )
    op.create_table(
        "player_sessions",
        sa.Column("player_id", sa.String(length=64), primary_key=True),
        sa.Column("match_id", sa.String(length=64), nullable=False),
        sa.Column("token_value", sa.String(length=256), nullable=False),
        sa.Column("issued_at_ms", sa.BigInteger(), nullable=False),
        sa.Column("expires_at_ms", sa.BigInteger(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("player_sessions")
    op.drop_table("match_events")
    op.drop_table("players")
    op.drop_table("matches")

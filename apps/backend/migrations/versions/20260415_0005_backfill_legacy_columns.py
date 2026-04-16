"""backfill legacy columns previously added at runtime

Revision ID: 20260415_0005
Revises: 20260415_0004
Create Date: 2026-04-15 21:50:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260415_0005"
down_revision = "20260415_0004"
branch_labels = None
depends_on = None


def _existing_columns(table_name: str) -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {col["name"] for col in inspector.get_columns(table_name)}


def _add_column_if_missing(table_name: str, column: sa.Column) -> None:
    if column.name in _existing_columns(table_name):
        return
    op.add_column(table_name, column)


def upgrade() -> None:
    _add_column_if_missing(
        "collector_tasks",
        sa.Column("collect_type", sa.String(length=32), nullable=False, server_default="search"),
    )
    _add_column_if_missing(
        "collector_tasks",
        sa.Column("source_url", sa.String(length=1000), nullable=True),
    )
    _add_column_if_missing(
        "collector_tasks",
        sa.Column("source_id", sa.String(length=255), nullable=True),
    )
    _add_column_if_missing(
        "collector_tasks",
        sa.Column("trigger_mode", sa.String(length=32), nullable=False, server_default="manual"),
    )
    _add_column_if_missing(
        "collector_tasks",
        sa.Column("execution_status", sa.String(length=64), nullable=False, server_default="PENDING"),
    )
    _add_column_if_missing(
        "collector_tasks",
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
    )
    _add_column_if_missing(
        "collector_tasks",
        sa.Column("raw_output_path", sa.String(length=1200), nullable=True),
    )
    _add_column_if_missing(
        "collector_tasks",
        sa.Column("error_message", sa.Text(), nullable=True),
    )
    _add_column_if_missing(
        "collector_tasks",
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
    )
    _add_column_if_missing(
        "collector_tasks",
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )

    _add_column_if_missing(
        "posts",
        sa.Column("author_name", sa.String(length=255), nullable=True),
    )
    _add_column_if_missing(
        "posts",
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
    )
    _add_column_if_missing(
        "posts",
        sa.Column("like_count", sa.Integer(), nullable=False, server_default="0"),
    )
    _add_column_if_missing(
        "posts",
        sa.Column("comment_count", sa.Integer(), nullable=False, server_default="0"),
    )
    _add_column_if_missing(
        "posts",
        sa.Column("favorite_count", sa.Integer(), nullable=False, server_default="0"),
    )
    _add_column_if_missing(
        "posts",
        sa.Column("share_count", sa.Integer(), nullable=False, server_default="0"),
    )
    _add_column_if_missing(
        "posts",
        sa.Column("view_count", sa.Integer(), nullable=False, server_default="0"),
    )
    _add_column_if_missing(
        "posts",
        sa.Column("is_historical_hot", sa.Boolean(), nullable=False, server_default=sa.text("0")),
    )
    _add_column_if_missing(
        "posts",
        sa.Column("note", sa.Text(), nullable=True),
    )
    _add_column_if_missing(
        "posts",
        sa.Column("source_type", sa.String(length=32), nullable=False, server_default="collector"),
    )
    _add_column_if_missing(
        "posts",
        sa.Column("topic_keywords", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
    )
    _add_column_if_missing(
        "posts",
        sa.Column("status", sa.String(length=32), nullable=False, server_default="raw"),
    )

    _add_column_if_missing(
        "analysis_results",
        sa.Column("fact_check_reviewer", sa.String(length=64), nullable=True),
    )
    _add_column_if_missing(
        "analysis_results",
        sa.Column("fact_check_notes", sa.Text(), nullable=True),
    )
    _add_column_if_missing(
        "analysis_results",
        sa.Column("fact_check_status", sa.String(length=32), nullable=False, server_default="pending"),
    )


def downgrade() -> None:
    # Intentional no-op: this migration is a compatibility backfill for legacy databases.
    pass

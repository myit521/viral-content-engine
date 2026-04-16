"""initial schema

Revision ID: 20260413_0001
Revises:
Create Date: 2026-04-13 22:30:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260413_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "collector_tasks",
        sa.Column("task_id", sa.String(length=64), nullable=False),
        sa.Column("platform_code", sa.String(length=32), nullable=False),
        sa.Column("task_type", sa.String(length=64), nullable=False),
        sa.Column("query_keyword", sa.String(length=255), nullable=False),
        sa.Column("collect_type", sa.String(length=32), nullable=False),
        sa.Column("source_url", sa.String(length=1000), nullable=True),
        sa.Column("source_id", sa.String(length=255), nullable=True),
        sa.Column("limit_count", sa.Integer(), nullable=False),
        sa.Column("trigger_mode", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("execution_status", sa.String(length=64), nullable=False),
        sa.Column("success_count", sa.Integer(), nullable=False),
        sa.Column("failed_count", sa.Integer(), nullable=False),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("raw_output_path", sa.String(length=1200), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("task_id"),
    )

    op.create_table(
        "posts",
        sa.Column("post_id", sa.String(length=64), nullable=False),
        sa.Column("platform_code", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("content_text", sa.Text(), nullable=False),
        sa.Column("source_url", sa.String(length=1000), nullable=False),
        sa.Column("author_name", sa.String(length=255), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("like_count", sa.Integer(), nullable=False),
        sa.Column("comment_count", sa.Integer(), nullable=False),
        sa.Column("favorite_count", sa.Integer(), nullable=False),
        sa.Column("share_count", sa.Integer(), nullable=False),
        sa.Column("view_count", sa.Integer(), nullable=False),
        sa.Column("is_historical_hot", sa.Boolean(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("topic_keywords", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("post_id"),
    )

    op.create_table(
        "ai_call_logs",
        sa.Column("log_id", sa.String(length=64), nullable=False),
        sa.Column("task_type", sa.String(length=32), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("prompt_version", sa.String(length=128), nullable=False),
        sa.Column("prompt_text", sa.Text(), nullable=False),
        sa.Column("response_json", sa.JSON(), nullable=True),
        sa.Column("token_usage", sa.JSON(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("log_id"),
    )

    op.create_table(
        "templates",
        sa.Column("template_id", sa.String(length=64), nullable=False),
        sa.Column("template_type", sa.String(length=32), nullable=False),
        sa.Column("template_category", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("applicable_platform", sa.String(length=64), nullable=False),
        sa.Column("applicable_topic", sa.String(length=64), nullable=False),
        sa.Column("applicable_scene", sa.String(length=64), nullable=False),
        sa.Column("structure_json", sa.JSON(), nullable=False),
        sa.Column("source_post_ids", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("template_id"),
    )

    op.create_table(
        "generated_contents",
        sa.Column("content_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("script_text", sa.Text(), nullable=False),
        sa.Column("storyboard_json", sa.JSON(), nullable=False),
        sa.Column("cover_text", sa.String(length=255), nullable=False),
        sa.Column("publish_caption", sa.Text(), nullable=False),
        sa.Column("hashtags", sa.JSON(), nullable=False),
        sa.Column("source_trace", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("fact_check_status", sa.String(length=32), nullable=False),
        sa.Column("current_version_no", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("content_id"),
    )

    op.create_table(
        "analysis_results",
        sa.Column("analysis_id", sa.String(length=64), nullable=False),
        sa.Column("post_id", sa.String(length=64), nullable=False),
        sa.Column("analysis_version", sa.String(length=32), nullable=False),
        sa.Column("prompt_version", sa.String(length=128), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("main_topic", sa.String(length=255), nullable=False),
        sa.Column("hook_text", sa.String(length=255), nullable=False),
        sa.Column("narrative_structure", sa.JSON(), nullable=False),
        sa.Column("emotional_driver", sa.String(length=255), nullable=False),
        sa.Column("fact_risk_level", sa.String(length=16), nullable=False),
        sa.Column("fact_risk_items", sa.JSON(), nullable=False),
        sa.Column("fact_check_status", sa.String(length=32), nullable=False),
        sa.Column("fact_check_reviewer", sa.String(length=64), nullable=True),
        sa.Column("fact_check_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["post_id"], ["posts.post_id"]),
        sa.PrimaryKeyConstraint("analysis_id"),
    )

    op.create_table(
        "generation_jobs",
        sa.Column("job_id", sa.String(length=64), nullable=False),
        sa.Column("job_type", sa.String(length=64), nullable=False),
        sa.Column("topic", sa.String(length=255), nullable=False),
        sa.Column("brief", sa.Text(), nullable=True),
        sa.Column("selected_template_id", sa.String(length=64), nullable=True),
        sa.Column("reference_post_ids", sa.JSON(), nullable=False),
        sa.Column("prompt_version", sa.String(length=128), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("generated_content_id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["generated_content_id"], ["generated_contents.content_id"]),
        sa.PrimaryKeyConstraint("job_id"),
    )

    op.create_table(
        "generated_content_versions",
        sa.Column("version_id", sa.String(length=64), nullable=False),
        sa.Column("generated_content_id", sa.String(length=64), nullable=False),
        sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=True),
        sa.Column("script_text", sa.Text(), nullable=False),
        sa.Column("storyboard_json", sa.JSON(), nullable=True),
        sa.Column("cover_text", sa.String(length=255), nullable=True),
        sa.Column("publish_caption", sa.Text(), nullable=True),
        sa.Column("edit_note", sa.Text(), nullable=True),
        sa.Column("editor", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["generated_content_id"], ["generated_contents.content_id"]),
        sa.PrimaryKeyConstraint("version_id"),
    )

    op.create_table(
        "review_records",
        sa.Column("review_id", sa.String(length=64), nullable=False),
        sa.Column("generated_content_id", sa.String(length=64), nullable=False),
        sa.Column("reviewer", sa.String(length=64), nullable=False),
        sa.Column("decision", sa.String(length=32), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("fact_check_status", sa.String(length=32), nullable=True),
        sa.Column("selected_version_no", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["generated_content_id"], ["generated_contents.content_id"]),
        sa.PrimaryKeyConstraint("review_id"),
    )

    op.create_table(
        "publish_records",
        sa.Column("publish_record_id", sa.String(length=64), nullable=False),
        sa.Column("generated_content_id", sa.String(length=64), nullable=False),
        sa.Column("platform_code", sa.String(length=32), nullable=False),
        sa.Column("publish_channel", sa.String(length=32), nullable=False),
        sa.Column("published_url", sa.String(length=1000), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("operator", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["generated_content_id"], ["generated_contents.content_id"]),
        sa.PrimaryKeyConstraint("publish_record_id"),
    )

    op.create_table(
        "performance_snapshots",
        sa.Column("snapshot_id", sa.String(length=64), nullable=False),
        sa.Column("publish_record_id", sa.String(length=64), nullable=False),
        sa.Column("like_count", sa.Integer(), nullable=False),
        sa.Column("comment_count", sa.Integer(), nullable=False),
        sa.Column("favorite_count", sa.Integer(), nullable=False),
        sa.Column("share_count", sa.Integer(), nullable=False),
        sa.Column("view_count", sa.Integer(), nullable=False),
        sa.Column("retention_rate", sa.Float(), nullable=True),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["publish_record_id"], ["publish_records.publish_record_id"]),
        sa.PrimaryKeyConstraint("snapshot_id"),
    )


def downgrade() -> None:
    op.drop_table("performance_snapshots")
    op.drop_table("publish_records")
    op.drop_table("review_records")
    op.drop_table("generated_content_versions")
    op.drop_table("generation_jobs")
    op.drop_table("analysis_results")
    op.drop_table("generated_contents")
    op.drop_table("templates")
    op.drop_table("ai_call_logs")
    op.drop_table("posts")
    op.drop_table("collector_tasks")

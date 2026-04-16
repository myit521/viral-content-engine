"""add query indexes for high-frequency fields

Revision ID: 20260415_0004
Revises: 20260414_0003
Create Date: 2026-04-15 09:30:00
"""
from __future__ import annotations

from alembic import op


# revision identifiers, used by Alembic.
revision = "20260415_0004"
down_revision = "20260414_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_posts_status_created_at", "posts", ["status", "created_at"], unique=False)
    op.create_index("ix_posts_source_type_created_at", "posts", ["source_type", "created_at"], unique=False)
    op.create_index("ix_analysis_results_post_created_at", "analysis_results", ["post_id", "created_at"], unique=False)
    op.create_index("ix_templates_status_created_at", "templates", ["status", "created_at"], unique=False)
    op.create_index("ix_generation_jobs_template", "generation_jobs", ["selected_template_id"], unique=False)
    op.create_index("ix_generated_content_versions_gc_ver", "generated_content_versions", ["generated_content_id", "version_no"], unique=False)
    op.create_index("ix_publish_records_gc_status", "publish_records", ["generated_content_id", "status"], unique=False)
    op.create_index("ix_performance_snapshots_publish_captured", "performance_snapshots", ["publish_record_id", "captured_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_performance_snapshots_publish_captured", table_name="performance_snapshots")
    op.drop_index("ix_publish_records_gc_status", table_name="publish_records")
    op.drop_index("ix_generated_content_versions_gc_ver", table_name="generated_content_versions")
    op.drop_index("ix_generation_jobs_template", table_name="generation_jobs")
    op.drop_index("ix_templates_status_created_at", table_name="templates")
    op.drop_index("ix_analysis_results_post_created_at", table_name="analysis_results")
    op.drop_index("ix_posts_source_type_created_at", table_name="posts")
    op.drop_index("ix_posts_status_created_at", table_name="posts")

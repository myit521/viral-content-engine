from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class CollectorTaskORM(Base):
    __tablename__ = "collector_tasks"

    task_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    platform_code: Mapped[str] = mapped_column(String(32), nullable=False)
    task_type: Mapped[str] = mapped_column(String(64), nullable=False)
    query_keyword: Mapped[str] = mapped_column(String(255), nullable=False)
    collect_type: Mapped[str] = mapped_column(String(32), nullable=False, default="search")
    source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    source_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    limit_count: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    trigger_mode: Mapped[str] = mapped_column(String(32), nullable=False, default="manual")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    execution_status: Mapped[str] = mapped_column(String(64), nullable=False, default="PENDING")
    success_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    raw_output_path: Mapped[str | None] = mapped_column(String(1200), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class PostORM(Base):
    __tablename__ = "posts"

    post_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    platform_code: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    author_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    like_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    comment_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    favorite_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    share_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    view_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_historical_hot: Mapped[bool] = mapped_column(nullable=False, default=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False, default="collector")
    topic_keywords: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="raw")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AnalysisResultORM(Base):
    __tablename__ = "analysis_results"

    analysis_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    post_id: Mapped[str] = mapped_column(ForeignKey("posts.post_id"), nullable=False)
    analysis_version: Mapped[str] = mapped_column(String(32), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(128), nullable=False)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    main_topic: Mapped[str] = mapped_column(String(255), nullable=False)
    hook_text: Mapped[str] = mapped_column(String(255), nullable=False)
    narrative_structure: Mapped[dict] = mapped_column(JSON, nullable=False)
    emotional_driver: Mapped[str] = mapped_column(String(255), nullable=False)
    fact_risk_level: Mapped[str] = mapped_column(String(16), nullable=False)
    fact_risk_items: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    fact_check_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    fact_check_reviewer: Mapped[str | None] = mapped_column(String(64), nullable=True)
    fact_check_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AICallLogORM(Base):
    __tablename__ = "ai_call_logs"

    log_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    task_type: Mapped[str] = mapped_column(String(32), nullable=False)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(128), nullable=False)
    prompt_text: Mapped[str] = mapped_column(Text, nullable=False)
    response_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    token_usage: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class TemplateORM(Base):
    __tablename__ = "templates"

    template_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    template_type: Mapped[str] = mapped_column(String(32), nullable=False)
    template_category: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    applicable_platform: Mapped[str] = mapped_column(String(64), nullable=False)
    applicable_topic: Mapped[str] = mapped_column(String(64), nullable=False)
    applicable_scene: Mapped[str] = mapped_column(String(64), nullable=False)
    structure_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    source_post_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class GeneratedContentORM(Base):
    __tablename__ = "generated_contents"

    content_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    script_text: Mapped[str] = mapped_column(Text, nullable=False)
    storyboard_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    cover_text: Mapped[str] = mapped_column(String(255), nullable=False)
    publish_caption: Mapped[str] = mapped_column(Text, nullable=False)
    hashtags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    source_trace: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    fact_check_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    current_version_no: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class GenerationJobORM(Base):
    __tablename__ = "generation_jobs"

    job_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    job_type: Mapped[str] = mapped_column(String(64), nullable=False)
    topic: Mapped[str] = mapped_column(String(255), nullable=False)
    brief: Mapped[str | None] = mapped_column(Text, nullable=True)
    selected_template_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    reference_post_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    prompt_version: Mapped[str] = mapped_column(String(128), nullable=False)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    generated_content_id: Mapped[str] = mapped_column(
        ForeignKey("generated_contents.content_id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class GeneratedContentVersionORM(Base):
    __tablename__ = "generated_content_versions"

    version_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    generated_content_id: Mapped[str] = mapped_column(
        ForeignKey("generated_contents.content_id"), nullable=False
    )
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    script_text: Mapped[str] = mapped_column(Text, nullable=False)
    storyboard_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    cover_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    publish_caption: Mapped[str | None] = mapped_column(Text, nullable=True)
    edit_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    editor: Mapped[str] = mapped_column(String(64), nullable=False, default="system")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ReviewRecordORM(Base):
    __tablename__ = "review_records"

    review_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    generated_content_id: Mapped[str] = mapped_column(
        ForeignKey("generated_contents.content_id"), nullable=False
    )
    reviewer: Mapped[str] = mapped_column(String(64), nullable=False)
    decision: Mapped[str] = mapped_column(String(32), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    fact_check_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    selected_version_no: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class PublishRecordORM(Base):
    __tablename__ = "publish_records"

    publish_record_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    generated_content_id: Mapped[str] = mapped_column(
        ForeignKey("generated_contents.content_id"), nullable=False
    )
    platform_code: Mapped[str] = mapped_column(String(32), nullable=False)
    publish_channel: Mapped[str] = mapped_column(String(32), nullable=False, default="manual")
    published_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    operator: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class PerformanceSnapshotORM(Base):
    __tablename__ = "performance_snapshots"

    snapshot_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    publish_record_id: Mapped[str] = mapped_column(
        ForeignKey("publish_records.publish_record_id"), nullable=False
    )
    like_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    comment_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    favorite_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    share_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    view_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    retention_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AsyncTaskORM(Base):
    __tablename__ = "async_tasks"

    task_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    task_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    input_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    result_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    related_resource_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    related_resource_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

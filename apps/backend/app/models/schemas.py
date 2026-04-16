from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from app.core.settings import model_profiles


class CollectorTaskCreateRequest(BaseModel):
    platform_code: Literal["zhihu"]
    task_type: str = "historical_hot"
    query_keyword: str = ""
    collect_type: Literal["search", "detail", "creator"] = "search"
    source_url: str | None = None
    source_id: str | None = None
    date_range_start: datetime | None = None
    date_range_end: datetime | None = None
    limit: int = Field(default=20, ge=1, le=200)


class CollectorTask(BaseModel):
    id: str | None = None
    task_id: str
    platform_code: str
    task_type: str
    query_keyword: str
    trigger_mode: str = "manual"
    collect_type: str = "search"
    source_url: str | None = None
    source_id: str | None = None
    status: Literal[
        "pending",
        "running",
        "succeeded",
        "partial_failed",
        "failed",
        "cancelled",
    ] = "pending"
    success_count: int = 0
    failed_count: int = 0
    retry_count: int = 0
    execution_status: Literal[
        "PENDING",
        "RUNNING",
        "SUCCESS",
        "FAILED",
        "RATE_LIMITED",
        "LOGIN_EXPIRED",
        "PROXY_FAILED",
        "VERIFICATION_REQUIRED",
    ] = "PENDING"
    raw_output_path: str | None = None
    error_message: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class Post(BaseModel):
    id: str | None = None
    post_id: str
    platform_code: str
    title: str
    content_text: str
    source_url: str
    source_type: str = "collector"
    author_name: str | None = None
    published_at: datetime | None = None
    like_count: int = 0
    comment_count: int = 0
    favorite_count: int = 0
    share_count: int = 0
    view_count: int = 0
    is_historical_hot: bool = False
    note: str | None = None
    topic_keywords: list[str] = Field(default_factory=list)
    status: Literal["raw", "normalized", "analyzed", "templated", "archived"] = "raw"
    created_at: datetime
    updated_at: datetime


class AnalysisCreateRequest(BaseModel):
    post_id: str
    analysis_version: str = "v1"
    prompt_version: str = "analysis.zhihu.history.v1"
    model_name: str = model_profiles.analysis_model


class AnalysisResult(BaseModel):
    id: str | None = None
    analysis_id: str
    post_id: str
    analysis_version: str
    prompt_version: str
    model_name: str
    summary: str
    main_topic: str
    hook_text: str
    narrative_structure: dict[str, Any]
    emotional_driver: str
    fact_risk_level: Literal["low", "medium", "high"]
    fact_risk_items: list[str]
    fact_check_status: Literal["pending", "confirmed", "needs_evidence", "rejected"] = (
        "pending"
    )
    fact_check_reviewer: str | None = None
    fact_check_notes: str | None = None
    created_at: datetime


class AnalysisNarrativeStructure(BaseModel):
    opening: str
    body: list[str]
    ending: str


class AnalysisLLMOutput(BaseModel):
    summary: str
    main_topic: str
    hook_text: str
    narrative_structure: AnalysisNarrativeStructure
    emotional_driver: str
    fact_risk_level: Literal["low", "medium", "high"]
    fact_risk_items: list[str] = Field(default_factory=list)


class TemplateCreateRequest(BaseModel):
    template_type: Literal["title", "script", "storyboard", "caption"] = "script"
    template_category: Literal[
        "title_hook", "opening_hook", "narrative_frame", "ending_cta", "full_script"
    ] = "narrative_frame"
    name: str
    applicable_platform: str = "zhihu_to_video"
    applicable_topic: str = "history"
    applicable_scene: str = "general"
    structure_json: dict[str, Any]
    source_post_ids: list[str] = Field(default_factory=list)


class TemplateAIGenerateRequest(BaseModel):
    name: str | None = None
    generation_goal: str | None = None
    template_type: Literal["title", "script", "storyboard", "caption"] = "script"
    template_category: Literal[
        "title_hook", "opening_hook", "narrative_frame", "ending_cta", "full_script"
    ] = "narrative_frame"
    applicable_platform: str = "zhihu_to_video"
    applicable_topic: str = "history"
    applicable_scene: str = "general"
    requirements: str | None = None
    description: str | None = None
    model_name: str | None = None
    reference_post_ids: list[str] | None = None

    @model_validator(mode="after")
    def validate_name_or_goal(self) -> "TemplateAIGenerateRequest":
        if (self.name or "").strip() or (self.generation_goal or "").strip():
            return self
        raise ValueError("Either 'name' or 'generation_goal' must be provided.")


class Template(BaseModel):
    id: str | None = None
    template_id: str
    template_type: str
    template_category: str
    name: str
    applicable_platform: str
    applicable_topic: str
    applicable_scene: str
    structure_json: dict[str, Any]
    source_post_ids: list[str]
    status: Literal["draft", "active", "disabled", "archived"] = "draft"
    created_at: datetime
    updated_at: datetime


class GenerationCreateRequest(BaseModel):
    job_type: Literal["script_generation"] = "script_generation"
    topic: str
    brief: str | None = None
    selected_template_id: str | None = None
    reference_post_ids: list[str] = Field(default_factory=list)
    prompt_version: str = "generation.zhihu_to_video.v1"
    model_name: str | None = None


class GeneratedContent(BaseModel):
    id: str | None = None
    content_id: str
    title: str
    script_text: str
    storyboard_json: dict[str, Any]
    cover_text: str
    publish_caption: str
    hashtags: list[str]
    source_trace: dict[str, Any]
    status: Literal["draft", "in_review", "approved", "rejected", "published"] = "draft"
    fact_check_status: Literal["pending", "confirmed", "needs_evidence", "rejected"] = (
        "pending"
    )
    current_version_no: int = 1
    created_at: datetime
    updated_at: datetime


class StoryboardShot(BaseModel):
    shot_no: int
    duration_seconds: int = Field(ge=1, le=120)
    visual_description: str
    voiceover: str


class GeneratedScriptLLMOutput(BaseModel):
    title_candidates: list[str] = Field(min_length=1, max_length=5)
    script_text: str
    storyboard: list[StoryboardShot] = Field(default_factory=list)
    cover_text: str
    publish_caption: str
    hashtags: list[str] = Field(default_factory=list)


class TemplateAIGeneratedStructure(BaseModel):
    opening: str
    body: list[str] = Field(min_length=1, max_length=8)
    ending: str


class TemplateAIGeneratedLLMOutput(BaseModel):
    name: str
    structure_json: TemplateAIGeneratedStructure


class ModelOptionItem(BaseModel):
    model_name: str
    label: str
    provider: str
    enabled: bool
    recommended: bool = False
    description: str | None = None
    scene: str
    supported_task_types: list[str] = Field(default_factory=list)


class ModelOptionsResponse(BaseModel):
    scene: str
    default_model: str
    options: list[ModelOptionItem] = Field(default_factory=list)


class GenerationJob(BaseModel):
    id: str | None = None
    job_id: str
    job_type: str
    topic: str
    brief: str | None = None
    selected_template_id: str | None = None
    reference_post_ids: list[str] = Field(default_factory=list)
    prompt_version: str
    model_name: str
    status: Literal["pending", "retrieving", "generating", "reviewing", "completed", "failed"]
    generated_content: GeneratedContent
    created_at: datetime
    updated_at: datetime


class PostManualImportRequest(BaseModel):
    platform_code: Literal["zhihu"] = "zhihu"
    source_url: str = ""
    title: str
    content_text: str
    author_name: str | None = None
    published_at: datetime | None = None
    topic_keywords: list[str] = Field(default_factory=list)
    note: str | None = None


class PostPatchRequest(BaseModel):
    topic_keywords: list[str] | None = None
    is_historical_hot: bool | None = None
    note: str | None = None


class PostBatchImportRequest(BaseModel):
    items: list[PostManualImportRequest] = Field(default_factory=list, min_length=1, max_length=500)


class AnalysisBatchCreateRequest(BaseModel):
    items: list[AnalysisCreateRequest] = Field(default_factory=list, min_length=1, max_length=500)


class PostBatchDeleteRequest(BaseModel):
    post_ids: list[str] = Field(default_factory=list, min_length=1, max_length=500)


class FactCheckRequest(BaseModel):
    fact_check_status: Literal["pending", "confirmed", "needs_evidence", "rejected"]
    reviewer: str
    notes: str | None = None
    risk_items: list[dict[str, Any]] = Field(default_factory=list)


class TemplateStatusRequest(BaseModel):
    status: Literal["draft", "active", "disabled", "archived"]


class TemplateAutoSummarizeRequest(BaseModel):
    analysis_ids: list[str] = Field(default_factory=list, min_length=2, max_length=1000)
    min_cluster_size: int = Field(default=2, ge=2, le=50)
    template_type: Literal["script", "title", "storyboard", "caption"] = "script"
    template_category: Literal[
        "title_hook", "opening_hook", "narrative_frame", "ending_cta", "full_script"
    ] = "narrative_frame"
    applicable_platform: str = "zhihu_to_video"
    applicable_topic: str = "history"
    applicable_scene: str = "general"


class ContentVersionCreateRequest(BaseModel):
    editor: str
    title: str | None = None
    script_text: str
    storyboard_json: dict[str, Any] | None = None
    cover_text: str | None = None
    publish_caption: str | None = None
    edit_note: str | None = None


class ReviewCreateRequest(BaseModel):
    generated_content_id: str
    reviewer: str
    decision: Literal["approve", "reject", "edit_required"]
    comment: str | None = None
    fact_check_status: Literal["pending", "confirmed", "needs_evidence", "rejected"] | None = None
    selected_version_no: int | None = None


class PublishRecordCreateRequest(BaseModel):
    generated_content_id: str
    platform_code: str
    publish_channel: str = "manual"
    published_url: str | None = None
    published_at: datetime | None = None
    operator: str
    notes: str | None = None


class PublishSnapshotCreateRequest(BaseModel):
    like_count: int = 0
    comment_count: int = 0
    favorite_count: int = 0
    share_count: int = 0
    view_count: int = 0
    retention_rate: float | None = None
    captured_at: datetime

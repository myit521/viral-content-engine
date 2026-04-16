from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.id_generator import new_id
from app.core.settings import model_option_settings, model_profiles
from app.generators.script_generator import generate_script
from app.models.orm import (
    AnalysisResultORM,
    GeneratedContentORM,
    GeneratedContentVersionORM,
    GenerationJobORM,
    PostORM,
    TemplateORM,
)
from app.models.schemas import (
    GeneratedContent,
    GenerationCreateRequest,
    GenerationJob,
    ModelOptionItem,
    ModelOptionsResponse,
)


class InvalidModelSelectionError(ValueError):
    pass


class GenerationService:
    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC)

    @staticmethod
    def _content_to_schema(content: GeneratedContentORM) -> GeneratedContent:
        return GeneratedContent(
            id=content.content_id,
            content_id=content.content_id,
            title=content.title,
            script_text=content.script_text,
            storyboard_json=content.storyboard_json,
            cover_text=content.cover_text,
            publish_caption=content.publish_caption,
            hashtags=content.hashtags or [],
            source_trace=content.source_trace,
            status=content.status,
            fact_check_status=content.fact_check_status,
            current_version_no=content.current_version_no,
            created_at=content.created_at,
            updated_at=content.updated_at,
        )

    @staticmethod
    def _normalize_model_option(scene: str, raw: dict) -> ModelOptionItem | None:
        model_name = str(raw.get("model_name", "")).strip()
        if not model_name:
            return None
        return ModelOptionItem(
            model_name=model_name,
            label=str(raw.get("label", model_name)).strip() or model_name,
            provider=str(raw.get("provider", model_profiles.provider)).strip() or model_profiles.provider,
            enabled=bool(raw.get("enabled", True)),
            recommended=bool(raw.get("recommended", False)),
            description=str(raw.get("description", "")).strip() or None,
            scene=str(raw.get("scene", scene)).strip() or scene,
            supported_task_types=[
                str(item).strip()
                for item in (raw.get("supported_task_types") or [])
                if str(item).strip()
            ],
        )

    def get_model_options(self, scene: str = "generation") -> ModelOptionsResponse:
        scene_name = (scene or "generation").strip() or "generation"
        items: list[ModelOptionItem] = []
        seen: set[str] = set()
        for raw in model_option_settings.options:
            option = self._normalize_model_option(scene_name, raw)
            if not option or option.scene != scene_name:
                continue
            if option.model_name in seen:
                continue
            seen.add(option.model_name)
            items.append(option)

        if not items:
            items = [
                ModelOptionItem(
                    model_name=model_profiles.generation_model,
                    label="Generation Default",
                    provider=model_profiles.provider,
                    enabled=True,
                    recommended=True,
                    description="Default model for content generation.",
                    scene=scene_name,
                    supported_task_types=["script_generation"],
                )
            ]

        if scene_name == "generation":
            configured_default = model_option_settings.generation_default_model
        elif scene_name == "template_generation":
            configured_default = model_option_settings.template_generation_default_model
        else:
            configured_default = items[0].model_name

        enabled_names = {item.model_name for item in items if item.enabled}
        default_model = (
            configured_default
            if configured_default in enabled_names
            else next((item.model_name for item in items if item.enabled), items[0].model_name)
        )
        return ModelOptionsResponse(scene=scene_name, default_model=default_model, options=items)

    def resolve_model_name(self, *, scene: str, requested_model_name: str | None) -> str:
        options = self.get_model_options(scene)
        enabled_names = {item.model_name for item in options.options if item.enabled}
        if not requested_model_name or not requested_model_name.strip():
            return options.default_model
        model_name = requested_model_name.strip()
        if model_name not in enabled_names:
            allowed = ", ".join(sorted(enabled_names))
            raise InvalidModelSelectionError(
                f"model_name '{model_name}' is not enabled for scene '{scene}'. allowed: [{allowed}]"
            )
        return model_name

    @staticmethod
    def _build_reference_posts_with_analysis(
        db: Session,
        reference_post_ids: list[str],
    ) -> list[dict]:
        if not reference_post_ids:
            return []

        posts = (
            db.query(PostORM)
            .filter(PostORM.post_id.in_(reference_post_ids))
            .all()
        )
        post_map = {post.post_id: post for post in posts}

        analyses = (
            db.query(AnalysisResultORM)
            .filter(AnalysisResultORM.post_id.in_(reference_post_ids))
            .order_by(AnalysisResultORM.post_id.asc(), AnalysisResultORM.created_at.desc())
            .all()
        )
        latest_analysis_by_post: dict[str, AnalysisResultORM] = {}
        for analysis in analyses:
            if analysis.post_id not in latest_analysis_by_post:
                latest_analysis_by_post[analysis.post_id] = analysis

        reference_posts: list[dict] = []
        for post_id in reference_post_ids:
            post = post_map.get(post_id)
            if not post:
                continue
            row = {
                "post_id": post.post_id,
                "title": post.title,
                "content_text": post.content_text,
            }
            latest_analysis = latest_analysis_by_post.get(post.post_id)
            if latest_analysis:
                row["analysis"] = {
                    "main_topic": latest_analysis.main_topic,
                    "hook_text": latest_analysis.hook_text,
                    "narrative_structure": latest_analysis.narrative_structure,
                    "emotional_driver": latest_analysis.emotional_driver,
                    "summary": latest_analysis.summary,
                }
            reference_posts.append(row)
        return reference_posts

    def create_generation_job(self, db: Session, request: GenerationCreateRequest) -> GenerationJob:
        now = self._now()
        job_id = new_id("job")
        template = db.get(TemplateORM, request.selected_template_id) if request.selected_template_id else None
        structure = template.structure_json if template else {"body": []}
        reference_posts = self._build_reference_posts_with_analysis(db, request.reference_post_ids)

        model_name = self.resolve_model_name(scene="generation", requested_model_name=request.model_name)

        result = generate_script(
            request.topic,
            request.brief,
            structure,
            reference_posts=reference_posts,
            db=db,
            prompt_version=request.prompt_version,
            model_name=model_name,
        )

        content = GeneratedContentORM(
            content_id=new_id("gc"),
            title=result["title_candidates"][0],
            script_text=result["script_text"],
            storyboard_json={"shots": result["storyboard"]},
            cover_text=result["cover_text"],
            publish_caption=result["publish_caption"],
            hashtags=result["hashtags"],
            source_trace={
                "template_id": request.selected_template_id,
                "reference_post_ids": request.reference_post_ids,
                "title_candidates": result["title_candidates"],
            },
            status="in_review",
            fact_check_status="pending",
            current_version_no=1,
            created_at=now,
            updated_at=now,
        )
        db.add(content)
        initial_version = GeneratedContentVersionORM(
            version_id=new_id("gcv"),
            generated_content_id=content.content_id,
            version_no=1,
            title=content.title,
            script_text=content.script_text,
            storyboard_json=content.storyboard_json,
            cover_text=content.cover_text,
            publish_caption=content.publish_caption,
            edit_note="initial draft",
            editor="system",
            created_at=now,
        )
        db.add(initial_version)

        job = GenerationJobORM(
            job_id=job_id,
            job_type=request.job_type,
            topic=request.topic,
            brief=request.brief,
            selected_template_id=request.selected_template_id,
            reference_post_ids=request.reference_post_ids,
            prompt_version=request.prompt_version,
            model_name=model_name,
            status="reviewing",
            generated_content_id=content.content_id,
            created_at=now,
            updated_at=now,
        )
        db.add(job)
        db.commit()
        db.refresh(content)
        db.refresh(job)
        return GenerationJob(
            id=job.job_id,
            job_id=job.job_id,
            job_type=job.job_type,
            topic=job.topic,
            brief=job.brief,
            selected_template_id=job.selected_template_id,
            reference_post_ids=job.reference_post_ids or [],
            prompt_version=job.prompt_version,
            model_name=job.model_name,
            status=job.status,
            generated_content=self._content_to_schema(content),
            created_at=job.created_at,
            updated_at=job.updated_at,
        )


generation_service = GenerationService()

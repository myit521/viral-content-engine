from __future__ import annotations

import json
from collections import defaultdict
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.id_generator import new_id
from app.core.prompt_manager import prompt_manager
from app.core.settings import ai_settings
from app.models.orm import AnalysisResultORM, PostORM, TemplateORM
from app.models.schemas import (
    Template,
    TemplateAIGenerateRequest,
    TemplateAIGeneratedLLMOutput,
    TemplateAutoSummarizeRequest,
    TemplateCreateRequest,
)
from app.services.ai_client import AIClientError, ai_client, schema_from_model
from app.services.generation_service import generation_service
from app.templates.template_engine import build_template_structure


class TemplateAIGenerationUnavailableError(RuntimeError):
    pass


class TemplateAIGenerationError(RuntimeError):
    pass


class TemplateService:
    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC)

    @staticmethod
    def _to_schema(template: TemplateORM) -> Template:
        return Template(
            id=template.template_id,
            template_id=template.template_id,
            template_type=template.template_type,
            template_category=template.template_category,
            name=template.name,
            applicable_platform=template.applicable_platform,
            applicable_topic=template.applicable_topic,
            applicable_scene=template.applicable_scene,
            structure_json=template.structure_json,
            source_post_ids=template.source_post_ids or [],
            status=template.status,
            created_at=template.created_at,
            updated_at=template.updated_at,
        )

    @staticmethod
    def _build_reference_context(db: Session, reference_post_ids: list[str] | None) -> str:
        if not reference_post_ids:
            return ""

        posts = db.query(PostORM).filter(PostORM.post_id.in_(reference_post_ids)).all()
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

        blocks: list[str] = []
        for post_id in reference_post_ids:
            post = post_map.get(post_id)
            if not post:
                continue
            lines = [
                f"样本ID: {post.post_id}",
                f"样本标题: {post.title or '无标题'}",
            ]
            latest_analysis = latest_analysis_by_post.get(post.post_id)
            if latest_analysis:
                lines.extend(
                    [
                        f"主题: {latest_analysis.main_topic or '未知'}",
                        f"钩子: {latest_analysis.hook_text or '无'}",
                        f"情绪驱动: {latest_analysis.emotional_driver or '未知'}",
                        f"叙事结构: {json.dumps(latest_analysis.narrative_structure or {}, ensure_ascii=False)}",
                        f"摘要: {latest_analysis.summary or '无'}",
                    ]
                )
            blocks.append("\n".join(lines))
        return "\n\n".join(blocks)

    def create_template(self, db: Session, request: TemplateCreateRequest) -> Template:
        now = self._now()
        template = TemplateORM(
            template_id=new_id("tpl"),
            template_type=request.template_type,
            template_category=request.template_category,
            name=request.name,
            applicable_platform=request.applicable_platform,
            applicable_topic=request.applicable_topic,
            applicable_scene=request.applicable_scene,
            structure_json=build_template_structure(request.structure_json),
            source_post_ids=request.source_post_ids,
            status="draft",
            created_at=now,
            updated_at=now,
        )
        db.add(template)
        db.commit()
        db.refresh(template)
        return self._to_schema(template)

    def create_template_with_ai(self, db: Session, request: TemplateAIGenerateRequest) -> Template:
        if not ai_settings.configured:
            raise TemplateAIGenerationUnavailableError("AI is not configured.")

        reference_post_ids = request.reference_post_ids or []
        reference_context = self._build_reference_context(db, reference_post_ids)

        model_name = generation_service.resolve_model_name(
            scene="template_generation",
            requested_model_name=request.model_name,
        )
        prompt = prompt_manager.load(
            prompt_id="template.center.generate.v1",
            variables={
                "name": request.name or "",
                "generation_goal": request.generation_goal or "",
                "template_type": request.template_type,
                "template_category": request.template_category,
                "applicable_platform": request.applicable_platform,
                "applicable_topic": request.applicable_topic,
                "applicable_scene": request.applicable_scene,
                "requirements": request.requirements or "",
                "description": request.description or "",
                "reference_context": reference_context,
            },
        )

        try:
            response = ai_client.chat_completion_sync(
                prompt=prompt,
                schema=schema_from_model(TemplateAIGeneratedLLMOutput, name="ai_generated_template"),
                model=model_name,
                task_type="template_generation",
                prompt_version="template.center.generate.v1",
                db=db,
                system_prompt=(
                    "You are a template generation engine. "
                    "Return valid JSON only and keep structure concise and reusable."
                ),
            )
            parsed = TemplateAIGeneratedLLMOutput.model_validate(response["result"])
        except Exception as exc:  # noqa: BLE001
            if isinstance(exc, AIClientError):
                raise TemplateAIGenerationError(str(exc)) from exc
            if isinstance(exc, ValueError):
                raise TemplateAIGenerationError(f"Invalid AI template output: {exc}") from exc
            raise

        now = self._now()
        template_name = (request.name or "").strip() or parsed.name.strip()
        if not template_name:
            template_name = f"ai-{request.template_category}-{int(now.timestamp())}"

        template = TemplateORM(
            template_id=new_id("tpl"),
            template_type=request.template_type,
            template_category=request.template_category,
            name=template_name,
            applicable_platform=request.applicable_platform,
            applicable_topic=request.applicable_topic,
            applicable_scene=request.applicable_scene,
            structure_json=build_template_structure(parsed.structure_json.model_dump(mode="json")),
            source_post_ids=reference_post_ids,
            status="draft",
            created_at=now,
            updated_at=now,
        )
        db.add(template)
        db.commit()
        db.refresh(template)
        return self._to_schema(template)

    def auto_summarize_templates(
        self, db: Session, request: TemplateAutoSummarizeRequest
    ) -> tuple[list[Template], list[dict]]:
        analyses = (
            db.query(AnalysisResultORM)
            .filter(AnalysisResultORM.analysis_id.in_(request.analysis_ids))
            .all()
        )
        by_id = {item.analysis_id: item for item in analyses}
        missing_ids = [item for item in request.analysis_ids if item not in by_id]

        clusters: dict[str, list[AnalysisResultORM]] = defaultdict(list)
        for item in analyses:
            key = f"{(item.main_topic or 'unknown').strip().lower()}|{(item.emotional_driver or 'neutral').strip().lower()}"
            clusters[key].append(item)

        created: list[Template] = []
        cluster_stats: list[dict] = []
        now = self._now()
        for cluster_key, rows in clusters.items():
            cluster_stats.append({"cluster_key": cluster_key, "size": len(rows)})
            if len(rows) < request.min_cluster_size:
                continue

            opening_candidates = [
                str((r.narrative_structure or {}).get("opening", "")).strip() for r in rows
            ]
            body_candidates = [
                (r.narrative_structure or {}).get("body", []) for r in rows
            ]
            ending_candidates = [
                str((r.narrative_structure or {}).get("ending", "")).strip() for r in rows
            ]

            opening = max((x for x in opening_candidates if x), key=opening_candidates.count, default="Start with a surprising hook")
            ending = max((x for x in ending_candidates if x), key=ending_candidates.count, default="Close with a clear CTA")
            body_pool: list[str] = []
            for body in body_candidates:
                if isinstance(body, list):
                    body_pool.extend([str(x).strip() for x in body if str(x).strip()])
            if not body_pool:
                body_pool = ["Background", "Conflict", "Takeaway"]
            dedup_body: list[str] = []
            for item in body_pool:
                if item not in dedup_body:
                    dedup_body.append(item)
                if len(dedup_body) >= 5:
                    break

            main_topic = rows[0].main_topic or "general"
            template = TemplateORM(
                template_id=new_id("tpl"),
                template_type=request.template_type,
                template_category=request.template_category,
                name=f"auto-{main_topic[:18]}-{len(rows)}",
                applicable_platform=request.applicable_platform,
                applicable_topic=request.applicable_topic,
                applicable_scene=request.applicable_scene,
                structure_json=build_template_structure(
                    {"opening": opening, "body": dedup_body, "ending": ending}
                ),
                source_post_ids=[r.post_id for r in rows if r.post_id],
                status="draft",
                created_at=now,
                updated_at=now,
            )
            db.add(template)
            db.flush()
            created.append(self._to_schema(template))

        db.commit()
        return created, [{"missing_analysis_ids": missing_ids}, {"clusters": cluster_stats}]

    def get_template(self, db: Session, template_id: str) -> Template | None:
        template = db.get(TemplateORM, template_id)
        if not template:
            return None
        return self._to_schema(template)


template_service = TemplateService()


from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.analyzers.content_features import analyze_content_features
from app.models.schemas import AnalysisCreateRequest, AnalysisResult
from app.core.id_generator import new_id
from app.core.settings import model_profiles
from app.models.orm import AnalysisResultORM, PostORM
from app.services.text_preprocess_service import text_preprocess_service


class AnalysisService:
    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC)

    @staticmethod
    def _to_schema(analysis: AnalysisResultORM) -> AnalysisResult:
        return AnalysisResult(
            id=analysis.analysis_id,
            analysis_id=analysis.analysis_id,
            post_id=analysis.post_id,
            analysis_version=analysis.analysis_version,
            prompt_version=analysis.prompt_version,
            model_name=analysis.model_name,
            summary=analysis.summary,
            main_topic=analysis.main_topic,
            hook_text=analysis.hook_text,
            narrative_structure=analysis.narrative_structure,
            emotional_driver=analysis.emotional_driver,
            fact_risk_level=analysis.fact_risk_level,
            fact_risk_items=analysis.fact_risk_items or [],
            fact_check_status=analysis.fact_check_status,
            fact_check_reviewer=analysis.fact_check_reviewer,
            fact_check_notes=analysis.fact_check_notes,
            created_at=analysis.created_at,
        )

    def create_analysis(self, db: Session, request: AnalysisCreateRequest) -> AnalysisResult:
        post = db.get(PostORM, request.post_id)
        if not post:
            raise KeyError("post not found")

        normalized_title = text_preprocess_service.preprocess(post.title or "").cleaned_text or post.title
        normalized_content = text_preprocess_service.preprocess(post.content_text or "").markdown_text or post.content_text

        # 使用请求中的模型，如果为空则使用配置文件的分析模型
        model_name = request.model_name or model_profiles.analysis_model

        features = analyze_content_features(
            normalized_title,
            normalized_content,
            db=db,
            prompt_version=request.prompt_version,
            model_name=model_name,
        )
        analysis = AnalysisResultORM(
            analysis_id=new_id("an"),
            post_id=post.post_id,
            analysis_version=request.analysis_version,
            prompt_version=request.prompt_version,
            model_name=model_name,
            summary=features["summary"],
            main_topic=features["main_topic"],
            hook_text=features["hook_text"],
            narrative_structure=features["narrative_structure"],
            emotional_driver=features["emotional_driver"],
            fact_risk_level=features["fact_risk_level"],
            fact_risk_items=features["fact_risk_items"],
            fact_check_status="pending",
            created_at=self._now(),
        )
        db.add(analysis)
        post.status = "analyzed"
        post.updated_at = self._now()
        db.commit()
        db.refresh(analysis)
        return self._to_schema(analysis)


analysis_service = AnalysisService()

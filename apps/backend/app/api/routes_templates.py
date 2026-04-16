from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.common import error_response, success_response
from app.core.cache import cache_service
from app.core.database import get_db
from app.core.settings import cache_settings
from app.models.orm import GeneratedContentORM, GenerationJobORM, TemplateORM
from app.models.schemas import TemplateAIGenerateRequest, TemplateAutoSummarizeRequest, TemplateCreateRequest, TemplateStatusRequest
from app.services.template_service import (
    TemplateAIGenerationError,
    TemplateAIGenerationUnavailableError,
    template_service,
)
from app.services.generation_service import InvalidModelSelectionError

router = APIRouter()


def _now() -> datetime:
    return datetime.now(UTC)


def _paginate(query, page: int, page_size: int) -> tuple[list, int]:
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def _template_dict(item: TemplateORM) -> dict:
    return {
        "id": item.template_id,
        "template_id": item.template_id,
        "template_type": item.template_type,
        "template_category": item.template_category,
        "name": item.name,
        "applicable_platform": item.applicable_platform,
        "applicable_topic": item.applicable_topic,
        "applicable_scene": item.applicable_scene,
        "structure_json": item.structure_json,
        "source_post_ids": item.source_post_ids or [],
        "status": item.status,
        "created_at": item.created_at.isoformat(),
        "updated_at": item.updated_at.isoformat(),
    }


def _template_is_referenced(db: Session, template_id: str) -> bool:
    if db.query(GenerationJobORM).filter(GenerationJobORM.selected_template_id == template_id).first():
        return True
    for content in db.query(GeneratedContentORM).all():
        if content.source_trace and content.source_trace.get("template_id") == template_id:
            return True
    return False


def _normalize_fts_query(q: str) -> str:
    return " ".join(q.strip().split())


def _phrase_fts_query(q: str) -> str:
    escaped = q.replace('"', '""')
    return f'"{escaped}"'


@router.post("/templates")
def create_template(request: TemplateCreateRequest, db: Session = Depends(get_db)) -> dict:
    template = template_service.create_template(db, request)
    cache_service.invalidate_prefix("api:templates:list:")
    return success_response(template.model_dump(mode="json"))


@router.post("/templates/ai-generate")
def ai_generate_template(request: TemplateAIGenerateRequest, db: Session = Depends(get_db)) -> JSONResponse:
    try:
        template = template_service.create_template_with_ai(db, request)
    except InvalidModelSelectionError as exc:
        return JSONResponse(status_code=400, content=error_response("INVALID_MODEL_NAME", str(exc)))
    except TemplateAIGenerationUnavailableError as exc:
        return JSONResponse(status_code=503, content=error_response("AI_UNAVAILABLE", str(exc)))
    except TemplateAIGenerationError as exc:
        return JSONResponse(status_code=502, content=error_response("AI_TEMPLATE_GENERATION_FAILED", str(exc)))

    cache_service.invalidate_prefix("api:templates:list:")
    return JSONResponse(status_code=200, content=success_response(template.model_dump(mode="json")))


@router.post("/templates/generate")
def ai_generate_template_compatible(
    request: TemplateAIGenerateRequest, db: Session = Depends(get_db)
) -> JSONResponse:
    return ai_generate_template(request, db)


@router.post("/templates/auto-summarize")
def auto_summarize_templates(
    request: TemplateAutoSummarizeRequest, db: Session = Depends(get_db)
) -> JSONResponse:
    created, meta = template_service.auto_summarize_templates(db, request)
    cache_service.invalidate_prefix("api:templates:list:")
    return JSONResponse(
        status_code=200,
        content=success_response(
            {
                "created_count": len(created),
                "items": [item.model_dump(mode="json") for item in created],
                "meta": meta,
            }
        ),
    )


@router.get("/templates")
def list_templates(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    template_category: str | None = Query(None),
    status: str | None = Query(None),
    include_archived: bool = Query(False),
    db: Session = Depends(get_db),
) -> dict:
    cache_key = (
        f"api:templates:list:{page}:{page_size}:{template_category or ''}:{status or ''}:{include_archived}"
    )
    cached = cache_service.get(cache_key)
    if isinstance(cached, dict):
        return success_response(cached)

    q = db.query(TemplateORM)
    if template_category:
        q = q.filter(TemplateORM.template_category == template_category)
    if status:
        q = q.filter(TemplateORM.status == status)
    elif not include_archived:
        q = q.filter(TemplateORM.status != "archived")
    q = q.order_by(TemplateORM.created_at.desc())
    items, total = _paginate(q, page, page_size)
    data = {"items": [_template_dict(i) for i in items], "page": page, "page_size": page_size, "total": total}
    cache_service.set(cache_key, data, ttl_seconds=cache_settings.templates_ttl_seconds)
    return success_response(data)


@router.get("/templates/search")
def search_templates(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    include_archived: bool = Query(False),
    db: Session = Depends(get_db),
) -> JSONResponse:
    query_text = _normalize_fts_query(q)
    params = {"query": query_text, "limit": page_size, "offset": (page - 1) * page_size}
    status_filter = "" if include_archived else "AND t.status != 'archived'"

    count_sql = text(
        f"""
        SELECT COUNT(1)
        FROM templates_fts f
        JOIN templates t ON t.template_id = f.template_id
        WHERE f MATCH :query
        {status_filter}
        """
    )
    ids_sql = text(
        f"""
        SELECT t.template_id, bm25(templates_fts) AS rank
        FROM templates_fts f
        JOIN templates t ON t.template_id = f.template_id
        WHERE f MATCH :query
        {status_filter}
        ORDER BY rank ASC, t.created_at DESC
        LIMIT :limit OFFSET :offset
        """
    )
    try:
        total = db.execute(count_sql, params).scalar_one()
        id_rows = db.execute(ids_sql, params).mappings().all()
    except Exception:
        params["query"] = _phrase_fts_query(query_text)
        try:
            total = db.execute(count_sql, params).scalar_one()
            id_rows = db.execute(ids_sql, params).mappings().all()
        except Exception:
            fallback_q = db.query(TemplateORM).filter(
                TemplateORM.name.contains(q)
                | TemplateORM.template_type.contains(q)
                | TemplateORM.template_category.contains(q)
            )
            if not include_archived:
                fallback_q = fallback_q.filter(TemplateORM.status != "archived")
            total = fallback_q.count()
            items = (
                fallback_q.order_by(TemplateORM.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
                .all()
            )
            return JSONResponse(
                status_code=200,
                content=success_response(
                    {
                        "items": [_template_dict(i) for i in items],
                        "page": page,
                        "page_size": page_size,
                        "total": total,
                        "mode": "fallback_like",
                    }
                ),
            )

    ids = [row["template_id"] for row in id_rows]
    if not ids:
        return JSONResponse(
            status_code=200,
            content=success_response({"items": [], "page": page, "page_size": page_size, "total": total}),
        )
    rows = db.query(TemplateORM).filter(TemplateORM.template_id.in_(ids)).all()
    row_map = {item.template_id: item for item in rows}
    items = [_template_dict(row_map[tid]) for tid in ids if tid in row_map]
    return JSONResponse(
        status_code=200,
        content=success_response({"items": items, "page": page, "page_size": page_size, "total": total}),
    )


@router.get("/templates/{template_id}")
def get_template(template_id: str, db: Session = Depends(get_db)) -> JSONResponse:
    template = db.get(TemplateORM, template_id)
    if not template:
        return JSONResponse(status_code=404, content=error_response("NOT_FOUND", "template not found"))
    return JSONResponse(status_code=200, content=success_response(_template_dict(template)))


@router.post("/templates/{template_id}/status")
def update_template_status(
    template_id: str, request: TemplateStatusRequest, db: Session = Depends(get_db)
) -> JSONResponse:
    template = db.get(TemplateORM, template_id)
    if not template:
        return JSONResponse(status_code=404, content=error_response("NOT_FOUND", "template not found"))
    template.status = request.status
    template.updated_at = _now()
    db.commit()
    db.refresh(template)
    cache_service.invalidate_prefix("api:templates:list:")
    return JSONResponse(status_code=200, content=success_response(_template_dict(template)))


@router.delete("/templates/{template_id}")
def delete_template(template_id: str, db: Session = Depends(get_db)) -> JSONResponse:
    template = db.get(TemplateORM, template_id)
    if not template:
        return JSONResponse(status_code=404, content=error_response("NOT_FOUND", "template not found"))
    if template.status == "archived":
        return JSONResponse(
            status_code=200,
            content=success_response({"template_id": template.template_id, "status": template.status}),
        )
    if _template_is_referenced(db, template_id):
        return JSONResponse(
            status_code=409,
            content=error_response("CONFLICT", "template is referenced by generation jobs"),
        )
    if template.status != "archived":
        template.status = "archived"
        template.updated_at = _now()
        db.commit()
    cache_service.invalidate_prefix("api:templates:list:")
    return JSONResponse(
        status_code=200,
        content=success_response({"template_id": template.template_id, "status": template.status}),
    )

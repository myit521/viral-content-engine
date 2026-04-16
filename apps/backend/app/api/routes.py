from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.common import error_response, success_response
from app.core.cache import cache_service
from app.core.database import SessionLocal, get_db
from app.core.id_generator import new_id
from app.core.settings import ai_settings, cache_settings, crawl_settings
from app.models.orm import (
    AnalysisResultORM,
    AsyncTaskORM,
    CollectorTaskORM,
    GeneratedContentORM,
    GeneratedContentVersionORM,
    GenerationJobORM,
    PerformanceSnapshotORM,
    PostORM,
    PublishRecordORM,
    ReviewRecordORM,
    TemplateORM,
)
from app.models.schemas import (
    AnalysisBatchCreateRequest,
    AnalysisCreateRequest,
    CollectorTaskCreateRequest,
    ContentVersionCreateRequest,
    FactCheckRequest,
    GenerationCreateRequest,
    PostBatchDeleteRequest,
    PostBatchImportRequest,
    PostManualImportRequest,
    PostPatchRequest,
    PublishRecordCreateRequest,
    PublishSnapshotCreateRequest,
    ReviewCreateRequest,
)
from app.services.analysis_service import analysis_service
from app.services.collection_service import collection_service
from app.services.generation_service import InvalidModelSelectionError, generation_service
from app.services.text_preprocess_service import text_preprocess_service

router = APIRouter()


def _now() -> datetime:
    return datetime.now(UTC)


def _paginate(query, page: int, page_size: int) -> tuple[list, int]:
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def _post_dict(post: PostORM) -> dict:
    return {
        "id": post.post_id,
        "post_id": post.post_id,
        "platform_code": post.platform_code,
        "title": post.title,
        "content_text": post.content_text,
        "source_url": post.source_url,
        "source_type": post.source_type,
        "author_name": post.author_name,
        "published_at": post.published_at.isoformat() if post.published_at else None,
        "like_count": post.like_count,
        "comment_count": post.comment_count,
        "favorite_count": post.favorite_count,
        "share_count": post.share_count,
        "view_count": post.view_count,
        "is_historical_hot": post.is_historical_hot,
        "note": post.note,
        "topic_keywords": post.topic_keywords or [],
        "status": post.status,
        "created_at": post.created_at.isoformat(),
        "updated_at": post.updated_at.isoformat(),
    }


def _analysis_dict(item: AnalysisResultORM) -> dict:
    return {
        "id": item.analysis_id,
        "analysis_id": item.analysis_id,
        "post_id": item.post_id,
        "analysis_version": item.analysis_version,
        "prompt_version": item.prompt_version,
        "model_name": item.model_name,
        "summary": item.summary,
        "main_topic": item.main_topic,
        "hook_text": item.hook_text,
        "narrative_structure": item.narrative_structure,
        "emotional_driver": item.emotional_driver,
        "fact_risk_level": item.fact_risk_level,
        "fact_risk_items": item.fact_risk_items or [],
        "fact_check_status": item.fact_check_status,
        "fact_check_reviewer": item.fact_check_reviewer,
        "fact_check_notes": item.fact_check_notes,
        "created_at": item.created_at.isoformat(),
    }


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


def _generated_content_dict(item: GeneratedContentORM) -> dict:
    return {
        "id": item.content_id,
        "content_id": item.content_id,
        "title": item.title,
        "script_text": item.script_text,
        "storyboard_json": item.storyboard_json,
        "cover_text": item.cover_text,
        "publish_caption": item.publish_caption,
        "hashtags": item.hashtags or [],
        "source_trace": item.source_trace,
        "status": item.status,
        "fact_check_status": item.fact_check_status,
        "current_version_no": item.current_version_no,
        "created_at": item.created_at.isoformat(),
        "updated_at": item.updated_at.isoformat(),
    }


def _job_dict(item: GenerationJobORM, content: GeneratedContentORM | None) -> dict:
    return {
        "id": item.job_id,
        "job_id": item.job_id,
        "job_type": item.job_type,
        "topic": item.topic,
        "brief": item.brief,
        "selected_template_id": item.selected_template_id,
        "reference_post_ids": item.reference_post_ids or [],
        "prompt_version": item.prompt_version,
        "model_name": item.model_name,
        "status": item.status,
        "generated_content": _generated_content_dict(content) if content else None,
        "created_at": item.created_at.isoformat(),
        "updated_at": item.updated_at.isoformat(),
    }


def _async_task_dict(item: AsyncTaskORM) -> dict:
    return {
        "task_id": item.task_id,
        "task_type": item.task_type,
        "status": item.status,
        "progress": item.progress,
        "input_payload": item.input_payload,
        "result_payload": item.result_payload,
        "error_message": item.error_message,
        "related_resource_type": item.related_resource_type,
        "related_resource_id": item.related_resource_id,
        "started_at": item.started_at.isoformat() if item.started_at else None,
        "finished_at": item.finished_at.isoformat() if item.finished_at else None,
        "created_at": item.created_at.isoformat(),
        "updated_at": item.updated_at.isoformat(),
    }


def _version_dict(item: GeneratedContentVersionORM) -> dict:
    return {
        "version_id": item.version_id,
        "generated_content_id": item.generated_content_id,
        "version_no": item.version_no,
        "title": item.title,
        "script_text": item.script_text,
        "storyboard_json": item.storyboard_json,
        "cover_text": item.cover_text,
        "publish_caption": item.publish_caption,
        "edit_note": item.edit_note,
        "editor": item.editor,
        "created_at": item.created_at.isoformat(),
    }


def _normalize_fts_query(q: str) -> str:
    return " ".join(q.strip().split())


def _phrase_fts_query(q: str) -> str:
    escaped = q.replace('"', '""')
    return f'"{escaped}"'


def _create_manual_post(db: Session, request: PostManualImportRequest) -> PostORM:
    now = _now()
    normalized_title = text_preprocess_service.preprocess(request.title or "").cleaned_text or "untitled"
    normalized_content = text_preprocess_service.preprocess(request.content_text or "").markdown_text
    post = PostORM(
        post_id=new_id("post"),
        platform_code=request.platform_code,
        title=normalized_title,
        content_text=normalized_content or (request.content_text or ""),
        source_url=request.source_url or f"manual://{new_id('src')}",
        source_type="manual_import",
        author_name=request.author_name,
        published_at=request.published_at,
        topic_keywords=request.topic_keywords,
        note=request.note,
        status="normalized",
        created_at=now,
        updated_at=now,
    )
    db.add(post)
    return post


def _post_is_referenced(db: Session, post_id: str) -> bool:
    if db.query(AnalysisResultORM).filter(AnalysisResultORM.post_id == post_id).first():
        return True
    for template in db.query(TemplateORM).all():
        if post_id in (template.source_post_ids or []):
            return True
    for job in db.query(GenerationJobORM).all():
        if post_id in (job.reference_post_ids or []):
            return True
    for content in db.query(GeneratedContentORM).all():
        refs = content.source_trace.get("reference_post_ids", []) if content.source_trace else []
        if post_id in refs:
            return True
    return False


def _template_is_referenced(db: Session, template_id: str) -> bool:
    if db.query(GenerationJobORM).filter(GenerationJobORM.selected_template_id == template_id).first():
        return True
    for content in db.query(GeneratedContentORM).all():
        if content.source_trace and content.source_trace.get("template_id") == template_id:
            return True
    return False


def _create_async_task(
    db: Session,
    *,
    task_type: str,
    input_payload: dict | None = None,
    related_resource_type: str | None = None,
    related_resource_id: str | None = None,
) -> AsyncTaskORM:
    now = _now()
    item = AsyncTaskORM(
        task_id=new_id("at"),
        task_type=task_type,
        status="pending",
        progress=0,
        input_payload=input_payload,
        related_resource_type=related_resource_type,
        related_resource_id=related_resource_id,
        created_at=now,
        updated_at=now,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def _mark_async_task_running(db: Session, task: AsyncTaskORM, progress: int = 10) -> None:
    task.status = "running"
    task.progress = progress
    task.started_at = _now()
    task.updated_at = _now()
    db.commit()
    db.refresh(task)


def _mark_async_task_success(
    db: Session,
    task: AsyncTaskORM,
    *,
    result_payload: dict | None = None,
    related_resource_type: str | None = None,
    related_resource_id: str | None = None,
) -> None:
    task.status = "succeeded"
    task.progress = 100
    task.result_payload = result_payload
    task.related_resource_type = related_resource_type or task.related_resource_type
    task.related_resource_id = related_resource_id or task.related_resource_id
    task.error_message = None
    task.finished_at = _now()
    task.updated_at = _now()
    db.commit()
    db.refresh(task)


def _mark_async_task_failed(db: Session, task: AsyncTaskORM, error_message: str) -> None:
    task.status = "failed"
    task.progress = 100
    task.error_message = error_message[:2000]
    task.finished_at = _now()
    task.updated_at = _now()
    db.commit()
    db.refresh(task)


def _run_collector_task_async(async_task_id: str, collector_task_id: str) -> None:
    with SessionLocal() as db:
        async_task = db.get(AsyncTaskORM, async_task_id)
        if not async_task:
            return
        _mark_async_task_running(db, async_task, progress=15)
        try:
            task = collection_service.run_task(db, collector_task_id)
            _mark_async_task_success(
                db,
                async_task,
                result_payload={
                    "task_id": task.task_id,
                    "status": task.status,
                    "execution_status": task.execution_status,
                    "success_count": task.success_count,
                    "failed_count": task.failed_count,
                },
                related_resource_type="collector_task",
                related_resource_id=collector_task_id,
            )
        except Exception as exc:
            _mark_async_task_failed(db, async_task, str(exc))


def _run_analysis_create_async(async_task_id: str, request_payload: dict) -> None:
    with SessionLocal() as db:
        async_task = db.get(AsyncTaskORM, async_task_id)
        if not async_task:
            return
        _mark_async_task_running(db, async_task, progress=20)
        try:
            request = AnalysisCreateRequest(**request_payload)
            result = analysis_service.create_analysis(db, request)
            _mark_async_task_success(
                db,
                async_task,
                result_payload=result.model_dump(mode="json"),
                related_resource_type="analysis_result",
                related_resource_id=result.analysis_id,
            )
        except Exception as exc:
            _mark_async_task_failed(db, async_task, str(exc))


def _run_generation_job_create_async(async_task_id: str, request_payload: dict) -> None:
    with SessionLocal() as db:
        async_task = db.get(AsyncTaskORM, async_task_id)
        if not async_task:
            return
        _mark_async_task_running(db, async_task, progress=20)
        try:
            request = GenerationCreateRequest(**request_payload)
            job = generation_service.create_generation_job(db, request)
            _mark_async_task_success(
                db,
                async_task,
                result_payload={
                    "job_id": job.job_id,
                    "status": job.status,
                    "generated_content": job.generated_content.model_dump(mode="json"),
                },
                related_resource_type="generation_job",
                related_resource_id=job.job_id,
            )
        except Exception as exc:
            _mark_async_task_failed(db, async_task, str(exc))


@router.get("/health")
def health() -> dict:
    data = cache_service.get_or_set(
        "api:health",
        lambda: {
            "status": "ok",
            "ai_configured": ai_settings.configured,
            "ai_model": ai_settings.default_model_name if ai_settings.configured else None,
            "ai_mock_fallback": ai_settings.allow_mock_fallback,
            "database": "sqlite",
            "mediacrawler_enabled": crawl_settings.mediacrawler_enable_real,
        },
        ttl_seconds=cache_settings.health_ttl_seconds,
    )
    return success_response(data)


@router.get("/platforms")
def get_platforms() -> dict:
    data = cache_service.get_or_set(
        "api:platforms",
        lambda: [
            {
                "id": 1,
                "code": "zhihu",
                "name": "Zhihu",
                "enabled": True,
                "mvp_enabled": True,
            }
        ],
        ttl_seconds=cache_settings.platforms_ttl_seconds,
    )
    return success_response(data)


@router.get("/model-options")
def get_model_options(scene: str = Query("generation")) -> JSONResponse:
    result = generation_service.get_model_options(scene=scene)
    return JSONResponse(status_code=200, content=success_response(result.model_dump(mode="json")))


@router.get("/tasks/{task_id}")
def get_async_task(task_id: str, db: Session = Depends(get_db)) -> JSONResponse:
    task = db.get(AsyncTaskORM, task_id)
    if not task:
        return JSONResponse(status_code=404, content=error_response("NOT_FOUND", "async task not found"))
    return JSONResponse(status_code=200, content=success_response(_async_task_dict(task)))


@router.post("/collector-tasks")
def create_collector_task(
    request: CollectorTaskCreateRequest, db: Session = Depends(get_db)
) -> dict:
    task = collection_service.create_task(db, request)
    return success_response(
        {
            "id": task.task_id,
            "task_id": task.task_id,
            "status": task.status,
            "execution_status": task.execution_status,
        }
    )


@router.get("/collector-tasks")
def list_collector_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    db: Session = Depends(get_db),
) -> dict:
    q = db.query(CollectorTaskORM)
    if status:
        q = q.filter(CollectorTaskORM.status == status)
    q = q.order_by(CollectorTaskORM.created_at.desc())
    items, total = _paginate(q, page, page_size)
    rows = [
        {
            "id": i.task_id,
            "task_id": i.task_id,
            "platform_code": i.platform_code,
            "task_type": i.task_type,
            "query_keyword": i.query_keyword,
            "collect_type": i.collect_type,
            "source_url": i.source_url,
            "source_id": i.source_id,
            "trigger_mode": i.trigger_mode,
            "status": i.status,
            "execution_status": i.execution_status,
            "success_count": i.success_count,
            "failed_count": i.failed_count,
            "retry_count": i.retry_count,
            "raw_output_path": i.raw_output_path,
            "error_message": i.error_message,
            "started_at": i.started_at.isoformat() if i.started_at else None,
            "finished_at": i.finished_at.isoformat() if i.finished_at else None,
            "created_at": i.created_at.isoformat(),
            "updated_at": i.updated_at.isoformat(),
        }
        for i in items
    ]
    return success_response({"items": rows, "page": page, "page_size": page_size, "total": total})


@router.get("/collector-tasks/{task_id}")
def get_collector_task(task_id: str, db: Session = Depends(get_db)) -> JSONResponse:
    task = db.get(CollectorTaskORM, task_id)
    if not task:
        return JSONResponse(status_code=404, content=error_response("NOT_FOUND", "collector task not found"))
    return JSONResponse(
        status_code=200,
        content=success_response(
            {
                "id": task.task_id,
                "task_id": task.task_id,
                "platform_code": task.platform_code,
                "task_type": task.task_type,
                "query_keyword": task.query_keyword,
                "collect_type": task.collect_type,
                "source_url": task.source_url,
                "source_id": task.source_id,
                "trigger_mode": task.trigger_mode,
                "status": task.status,
                "execution_status": task.execution_status,
                "success_count": task.success_count,
                "failed_count": task.failed_count,
                "retry_count": task.retry_count,
                "raw_output_path": task.raw_output_path,
                "error_message": task.error_message,
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "finished_at": task.finished_at.isoformat() if task.finished_at else None,
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat(),
            }
        ),
    )


@router.post("/collector-tasks/{task_id}/run")
def run_collector_task(
    task_id: str,
    background_tasks: BackgroundTasks,
    async_mode: bool = Query(False),
    db: Session = Depends(get_db),
) -> JSONResponse:
    if async_mode:
        collector_task = db.get(CollectorTaskORM, task_id)
        if not collector_task:
            return JSONResponse(status_code=404, content=error_response("NOT_FOUND", "collector task not found"))
        async_task = _create_async_task(
            db,
            task_type="collector_run",
            input_payload={"collector_task_id": task_id},
            related_resource_type="collector_task",
            related_resource_id=task_id,
        )
        background_tasks.add_task(_run_collector_task_async, async_task.task_id, task_id)
        return JSONResponse(status_code=202, content=success_response(_async_task_dict(async_task)))

    try:
        task = collection_service.run_task(db, task_id)
        return JSONResponse(
            status_code=200,
            content=success_response(
                {
                    "id": task.task_id,
                    "task_id": task.task_id,
                    "status": task.status,
                    "execution_status": task.execution_status,
                    "success_count": task.success_count,
                    "failed_count": task.failed_count,
                    "retry_count": task.retry_count,
                    "raw_output_path": task.raw_output_path,
                    "error_message": task.error_message,
                }
            ),
        )
    except KeyError:
        return JSONResponse(
            status_code=404,
            content=error_response("NOT_FOUND", "collector task not found"),
        )


@router.get("/posts")
def list_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    keyword: str | None = Query(None),
    source_type: str | None = Query(None),
    include_archived: bool = Query(False),
    db: Session = Depends(get_db),
) -> dict:
    q = db.query(PostORM)
    if status:
        q = q.filter(PostORM.status == status)
    elif not include_archived:
        q = q.filter(PostORM.status != "archived")
    if source_type:
        q = q.filter(PostORM.source_type == source_type)
    if keyword:
        q = q.filter(PostORM.title.contains(keyword) | PostORM.content_text.contains(keyword))
    q = q.order_by(PostORM.created_at.desc())
    items, total = _paginate(q, page, page_size)
    return success_response(
        {
            "items": [_post_dict(i) for i in items],
            "page": page,
            "page_size": page_size,
            "total": total,
        }
    )


@router.get("/posts/search")
def search_posts(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    include_archived: bool = Query(False),
    db: Session = Depends(get_db),
) -> JSONResponse:
    query_text = _normalize_fts_query(q)
    params = {"query": query_text, "limit": page_size, "offset": (page - 1) * page_size}
    status_filter = "" if include_archived else "AND p.status != 'archived'"

    count_sql = text(
        f"""
        SELECT COUNT(1)
        FROM posts_fts f
        JOIN posts p ON p.post_id = f.post_id
        WHERE f MATCH :query
        {status_filter}
        """
    )
    ids_sql = text(
        f"""
        SELECT p.post_id, bm25(posts_fts) AS rank
        FROM posts_fts f
        JOIN posts p ON p.post_id = f.post_id
        WHERE f MATCH :query
        {status_filter}
        ORDER BY rank ASC, p.created_at DESC
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
            fallback_q = db.query(PostORM).filter(
                PostORM.title.contains(q) | PostORM.content_text.contains(q) | PostORM.topic_keywords.contains(q)
            )
            if not include_archived:
                fallback_q = fallback_q.filter(PostORM.status != "archived")
            total = fallback_q.count()
            items = fallback_q.order_by(PostORM.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
            return JSONResponse(
                status_code=200,
                content=success_response(
                    {
                        "items": [_post_dict(i) for i in items],
                        "page": page,
                        "page_size": page_size,
                        "total": total,
                        "mode": "fallback_like",
                    }
                ),
            )

    ids = [row["post_id"] for row in id_rows]
    if not ids:
        return JSONResponse(
            status_code=200,
            content=success_response({"items": [], "page": page, "page_size": page_size, "total": total}),
        )
    posts = db.query(PostORM).filter(PostORM.post_id.in_(ids)).all()
    post_map = {item.post_id: item for item in posts}
    items = [_post_dict(post_map[pid]) for pid in ids if pid in post_map]
    return JSONResponse(
        status_code=200,
        content=success_response({"items": items, "page": page, "page_size": page_size, "total": total}),
    )


@router.get("/posts/{post_id}")
def get_post_detail(post_id: str, db: Session = Depends(get_db)) -> JSONResponse:
    item = db.get(PostORM, post_id)
    if not item:
        return JSONResponse(status_code=404, content=error_response("NOT_FOUND", "post not found"))
    return JSONResponse(status_code=200, content=success_response(_post_dict(item)))


@router.post("/posts/manual-import")
def manual_import_post(request: PostManualImportRequest, db: Session = Depends(get_db)) -> dict:
    post = _create_manual_post(db, request)
    db.commit()
    db.refresh(post)
    return success_response(_post_dict(post))


@router.post("/posts/batch-import")
def batch_import_posts(request: PostBatchImportRequest, db: Session = Depends(get_db)) -> JSONResponse:
    created: list[dict] = []
    errors: list[dict] = []
    for idx, item in enumerate(request.items):
        try:
            with db.begin_nested():
                post = _create_manual_post(db, item)
                db.flush()
                created.append(_post_dict(post))
        except Exception as exc:
            errors.append({"index": idx, "error": str(exc)})

    db.commit()
    return JSONResponse(
        status_code=200,
        content=success_response(
            {
                "created_count": len(created),
                "failed_count": len(errors),
                "items": created,
                "errors": errors,
            }
        ),
    )


@router.patch("/posts/{post_id}")
def patch_post(post_id: str, request: PostPatchRequest, db: Session = Depends(get_db)) -> JSONResponse:
    post = db.get(PostORM, post_id)
    if not post:
        return JSONResponse(status_code=404, content=error_response("NOT_FOUND", "post not found"))
    if request.topic_keywords is not None:
        post.topic_keywords = request.topic_keywords
    if request.is_historical_hot is not None:
        post.is_historical_hot = request.is_historical_hot
    if request.note is not None:
        post.note = request.note
    post.updated_at = _now()
    db.commit()
    db.refresh(post)
    return JSONResponse(status_code=200, content=success_response(_post_dict(post)))


@router.delete("/posts/batch")
def batch_delete_posts(request: PostBatchDeleteRequest, db: Session = Depends(get_db)) -> JSONResponse:
    archived: list[str] = []
    errors: list[dict] = []

    for post_id in request.post_ids:
        post = db.get(PostORM, post_id)
        if not post:
            errors.append({"post_id": post_id, "code": "NOT_FOUND", "message": "post not found"})
            continue
        if post.status == "archived":
            archived.append(post_id)
            continue
        if _post_is_referenced(db, post_id):
            errors.append(
                {"post_id": post_id, "code": "CONFLICT", "message": "post is referenced by other resources"}
            )
            continue

        post.status = "archived"
        post.updated_at = _now()
        archived.append(post_id)

    db.commit()
    return JSONResponse(
        status_code=200,
        content=success_response(
            {
                "archived_count": len(archived),
                "failed_count": len(errors),
                "archived_post_ids": archived,
                "errors": errors,
            }
        ),
    )


@router.delete("/posts/{post_id}")
def delete_post(post_id: str, db: Session = Depends(get_db)) -> JSONResponse:
    post = db.get(PostORM, post_id)
    if not post:
        return JSONResponse(status_code=404, content=error_response("NOT_FOUND", "post not found"))
    if post.status == "archived":
        return JSONResponse(
            status_code=200,
            content=success_response({"post_id": post.post_id, "status": post.status}),
        )
    if _post_is_referenced(db, post_id):
        return JSONResponse(
            status_code=409,
            content=error_response("CONFLICT", "post is referenced by other resources"),
        )
    if post.status != "archived":
        post.status = "archived"
        post.updated_at = _now()
        db.commit()
    return JSONResponse(
        status_code=200,
        content=success_response({"post_id": post.post_id, "status": post.status}),
    )


@router.post("/analysis-results")
def create_analysis(
    request: AnalysisCreateRequest,
    background_tasks: BackgroundTasks,
    async_mode: bool = Query(False),
    db: Session = Depends(get_db),
) -> JSONResponse:
    if async_mode:
        post = db.get(PostORM, request.post_id)
        if not post:
            return JSONResponse(
                status_code=404,
                content=error_response("NOT_FOUND", "post not found"),
            )
        async_task = _create_async_task(
            db,
            task_type="analysis_create",
            input_payload=request.model_dump(mode="json"),
            related_resource_type="post",
            related_resource_id=request.post_id,
        )
        background_tasks.add_task(
            _run_analysis_create_async,
            async_task.task_id,
            request.model_dump(mode="json"),
        )
        return JSONResponse(status_code=202, content=success_response(_async_task_dict(async_task)))

    try:
        result = analysis_service.create_analysis(db, request)
        return JSONResponse(status_code=200, content=success_response(result.model_dump(mode="json")))
    except KeyError:
        return JSONResponse(
            status_code=404,
            content=error_response("NOT_FOUND", "post not found"),
        )


@router.post("/analysis-results/batch-create")
def batch_create_analysis(
    request: AnalysisBatchCreateRequest,
    db: Session = Depends(get_db),
) -> JSONResponse:
    created: list[dict] = []
    errors: list[dict] = []
    for idx, item in enumerate(request.items):
        try:
            result = analysis_service.create_analysis(db, item)
            created.append(result.model_dump(mode="json"))
        except KeyError:
            errors.append({"index": idx, "post_id": item.post_id, "code": "NOT_FOUND", "message": "post not found"})
        except Exception as exc:
            errors.append({"index": idx, "post_id": item.post_id, "code": "FAILED", "message": str(exc)})

    return JSONResponse(
        status_code=200,
        content=success_response(
            {
                "created_count": len(created),
                "failed_count": len(errors),
                "items": created,
                "errors": errors,
            }
        ),
    )


@router.get("/analysis-results/{analysis_id}")
def get_analysis_result(analysis_id: str, db: Session = Depends(get_db)) -> JSONResponse:
    item = db.get(AnalysisResultORM, analysis_id)
    if not item:
        return JSONResponse(status_code=404, content=error_response("NOT_FOUND", "analysis result not found"))
    return JSONResponse(status_code=200, content=success_response(_analysis_dict(item)))


@router.get("/posts/{post_id}/analysis-results")
def list_post_analysis_results(post_id: str, db: Session = Depends(get_db)) -> JSONResponse:
    post = db.get(PostORM, post_id)
    if not post:
        return JSONResponse(status_code=404, content=error_response("NOT_FOUND", "post not found"))
    analyses = (
        db.query(AnalysisResultORM)
        .filter(AnalysisResultORM.post_id == post_id)
        .order_by(AnalysisResultORM.created_at.desc())
        .all()
    )
    return JSONResponse(
        status_code=200,
        content=success_response([_analysis_dict(item) for item in analyses]),
    )


@router.post("/analysis-results/{analysis_id}/fact-check")
def fact_check_analysis(analysis_id: str, request: FactCheckRequest, db: Session = Depends(get_db)) -> JSONResponse:
    item = db.get(AnalysisResultORM, analysis_id)
    if not item:
        return JSONResponse(status_code=404, content=error_response("NOT_FOUND", "analysis result not found"))
    item.fact_check_status = request.fact_check_status
    item.fact_check_reviewer = request.reviewer
    item.fact_check_notes = request.notes
    db.commit()
    db.refresh(item)
    return JSONResponse(status_code=200, content=success_response(_analysis_dict(item)))


@router.post("/generation-jobs")
def create_generation_job(
    request: GenerationCreateRequest,
    background_tasks: BackgroundTasks,
    async_mode: bool = Query(False),
    db: Session = Depends(get_db),
) -> JSONResponse:
    if async_mode:
        async_task = _create_async_task(
            db,
            task_type="generation_create",
            input_payload=request.model_dump(mode="json"),
        )
        background_tasks.add_task(
            _run_generation_job_create_async,
            async_task.task_id,
            request.model_dump(mode="json"),
        )
        return JSONResponse(status_code=202, content=success_response(_async_task_dict(async_task)))

    try:
        job = generation_service.create_generation_job(db, request)
    except InvalidModelSelectionError as exc:
        return JSONResponse(status_code=400, content=error_response("INVALID_MODEL_NAME", str(exc)))
    return JSONResponse(
        status_code=200,
        content=success_response(
            {
                "id": job.job_id,
                "job_id": job.job_id,
                "status": job.status,
                "generated_content": job.generated_content.model_dump(mode="json"),
            }
        ),
    )


@router.get("/generation-jobs/{job_id}")
def get_generation_job(job_id: str, db: Session = Depends(get_db)) -> JSONResponse:
    job = db.get(GenerationJobORM, job_id)
    if not job:
        return JSONResponse(status_code=404, content=error_response("NOT_FOUND", "generation job not found"))
    content = db.get(GeneratedContentORM, job.generated_content_id)
    return JSONResponse(status_code=200, content=success_response(_job_dict(job, content)))


@router.get("/generation-jobs")
def list_generation_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    db: Session = Depends(get_db),
) -> dict:
    q = db.query(GenerationJobORM)
    if status:
        q = q.filter(GenerationJobORM.status == status)
    q = q.order_by(GenerationJobORM.created_at.desc())
    items, total = _paginate(q, page, page_size)

    content_ids = [item.generated_content_id for item in items]
    content_map: dict[str, GeneratedContentORM] = {}
    if content_ids:
        contents = (
            db.query(GeneratedContentORM)
            .filter(GeneratedContentORM.content_id.in_(content_ids))
            .all()
        )
        content_map = {item.content_id: item for item in contents}

    return success_response(
        {
            "items": [_job_dict(item, content_map.get(item.generated_content_id)) for item in items],
            "page": page,
            "page_size": page_size,
            "total": total,
        }
    )


@router.get("/generated-contents")
def list_generated_contents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    job_id: str | None = Query(None),
    db: Session = Depends(get_db),
) -> dict:
    q = db.query(GeneratedContentORM)
    if job_id:
        job = db.get(GenerationJobORM, job_id)
        if not job:
            return success_response({"items": [], "page": page, "page_size": page_size, "total": 0})
        q = q.filter(GeneratedContentORM.content_id == job.generated_content_id)
    q = q.order_by(GeneratedContentORM.created_at.desc())
    items, total = _paginate(q, page, page_size)
    return success_response(
        {"items": [_generated_content_dict(i) for i in items], "page": page, "page_size": page_size, "total": total}
    )


@router.get("/generated-contents/{content_id}")
def get_generated_content(content_id: str, db: Session = Depends(get_db)) -> JSONResponse:
    item = db.get(GeneratedContentORM, content_id)
    if not item:
        return JSONResponse(status_code=404, content=error_response("NOT_FOUND", "generated content not found"))
    return JSONResponse(status_code=200, content=success_response(_generated_content_dict(item)))


@router.get("/generated-contents/{content_id}/review-compare")
def get_review_compare(content_id: str, db: Session = Depends(get_db)) -> JSONResponse:
    content = db.get(GeneratedContentORM, content_id)
    if not content:
        return JSONResponse(status_code=404, content=error_response("NOT_FOUND", "generated content not found"))

    versions = (
        db.query(GeneratedContentVersionORM)
        .filter(GeneratedContentVersionORM.generated_content_id == content_id)
        .order_by(GeneratedContentVersionORM.version_no.asc())
        .all()
    )
    initial = versions[0] if versions else None
    current = versions[-1] if versions else None
    return JSONResponse(
        status_code=200,
        content=success_response(
            {
                "generated_content_id": content_id,
                "source_summary": content.source_trace.get("reference_post_ids", []),
                "initial_draft": {
                    "version_no": initial.version_no,
                    "title": initial.title,
                    "script_text": initial.script_text,
                }
                if initial
                else None,
                "current_edit": {
                    "version_no": current.version_no,
                    "title": current.title,
                    "script_text": current.script_text,
                }
                if current
                else None,
                "final_draft": {
                    "version_no": current.version_no,
                    "title": current.title,
                    "script_text": current.script_text,
                }
                if content.status in ["approved", "published"] and current
                else None,
            }
        ),
    )


@router.post("/generated-contents/{content_id}/versions")
def create_content_version(
    content_id: str, request: ContentVersionCreateRequest, db: Session = Depends(get_db)
) -> JSONResponse:
    content = db.get(GeneratedContentORM, content_id)
    if not content:
        return JSONResponse(status_code=404, content=error_response("NOT_FOUND", "generated content not found"))

    last = (
        db.query(GeneratedContentVersionORM)
        .filter(GeneratedContentVersionORM.generated_content_id == content_id)
        .order_by(GeneratedContentVersionORM.version_no.desc())
        .first()
    )
    next_version = 1 if not last else last.version_no + 1
    version = GeneratedContentVersionORM(
        version_id=new_id("gcv"),
        generated_content_id=content_id,
        version_no=next_version,
        title=request.title,
        script_text=request.script_text,
        storyboard_json=request.storyboard_json,
        cover_text=request.cover_text,
        publish_caption=request.publish_caption,
        edit_note=request.edit_note,
        editor=request.editor,
        created_at=_now(),
    )
    db.add(version)

    content.title = request.title or content.title
    content.script_text = request.script_text
    content.storyboard_json = request.storyboard_json or content.storyboard_json
    content.cover_text = request.cover_text or content.cover_text
    content.publish_caption = request.publish_caption or content.publish_caption
    content.current_version_no = next_version
    content.updated_at = _now()

    db.commit()
    return JSONResponse(
        status_code=200,
        content=success_response(
            {
                "version_id": version.version_id,
                "version_no": version.version_no,
                "generated_content_id": content_id,
                "current_version_no": content.current_version_no,
            }
        ),
    )


@router.get("/generated-contents/{content_id}/versions")
def list_content_versions(
    content_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> JSONResponse:
    content = db.get(GeneratedContentORM, content_id)
    if not content:
        return JSONResponse(status_code=404, content=error_response("NOT_FOUND", "generated content not found"))

    q = (
        db.query(GeneratedContentVersionORM)
        .filter(GeneratedContentVersionORM.generated_content_id == content_id)
        .order_by(GeneratedContentVersionORM.version_no.desc())
    )
    items, total = _paginate(q, page, page_size)
    return JSONResponse(
        status_code=200,
        content=success_response(
            {
                "items": [_version_dict(i) for i in items],
                "page": page,
                "page_size": page_size,
                "total": total,
                "current_version_no": content.current_version_no,
            }
        ),
    )


@router.patch("/generated-contents/{content_id}/versions/{version_no}")
def switch_content_version(content_id: str, version_no: int, db: Session = Depends(get_db)) -> JSONResponse:
    content = db.get(GeneratedContentORM, content_id)
    if not content:
        return JSONResponse(status_code=404, content=error_response("NOT_FOUND", "generated content not found"))

    version = (
        db.query(GeneratedContentVersionORM)
        .filter(
            GeneratedContentVersionORM.generated_content_id == content_id,
            GeneratedContentVersionORM.version_no == version_no,
        )
        .first()
    )
    if not version:
        return JSONResponse(status_code=404, content=error_response("NOT_FOUND", "content version not found"))

    if version.title:
        content.title = version.title
    content.script_text = version.script_text
    if version.storyboard_json is not None:
        content.storyboard_json = version.storyboard_json
    if version.cover_text:
        content.cover_text = version.cover_text
    if version.publish_caption:
        content.publish_caption = version.publish_caption
    content.current_version_no = version.version_no
    content.updated_at = _now()
    db.commit()
    db.refresh(content)

    return JSONResponse(
        status_code=200,
        content=success_response(
            {
                "content_id": content.content_id,
                "current_version_no": content.current_version_no,
                "active_version": _version_dict(version),
                "content": _generated_content_dict(content),
            }
        ),
    )


@router.post("/generated-contents/{content_id}/fact-check")
def fact_check_generated_content(
    content_id: str, request: FactCheckRequest, db: Session = Depends(get_db)
) -> JSONResponse:
    content = db.get(GeneratedContentORM, content_id)
    if not content:
        return JSONResponse(status_code=404, content=error_response("NOT_FOUND", "generated content not found"))

    content.fact_check_status = request.fact_check_status
    content.updated_at = _now()
    db.commit()
    db.refresh(content)

    return JSONResponse(status_code=200, content=success_response(_generated_content_dict(content)))


@router.post("/reviews")
def create_review(request: ReviewCreateRequest, db: Session = Depends(get_db)) -> JSONResponse:
    content = db.get(GeneratedContentORM, request.generated_content_id)
    if not content:
        return JSONResponse(status_code=404, content=error_response("NOT_FOUND", "generated content not found"))

    review = ReviewRecordORM(
        review_id=new_id("rvw"),
        generated_content_id=request.generated_content_id,
        reviewer=request.reviewer,
        decision=request.decision,
        comment=request.comment,
        fact_check_status=request.fact_check_status,
        selected_version_no=request.selected_version_no,
        reviewed_at=_now(),
    )
    db.add(review)

    if request.decision == "approve":
        content.status = "approved"
    elif request.decision == "reject":
        content.status = "rejected"
    else:
        content.status = "draft"
    if request.fact_check_status:
        content.fact_check_status = request.fact_check_status
    content.updated_at = _now()

    db.commit()
    return JSONResponse(
        status_code=200,
        content=success_response(
            {
                "review_id": review.review_id,
                "generated_content_id": review.generated_content_id,
                "decision": review.decision,
                "status": content.status,
            }
        ),
    )


@router.post("/publish-records")
def create_publish_record(request: PublishRecordCreateRequest, db: Session = Depends(get_db)) -> JSONResponse:
    content = db.get(GeneratedContentORM, request.generated_content_id)
    if not content:
        return JSONResponse(status_code=404, content=error_response("NOT_FOUND", "generated content not found"))

    now = _now()
    record = PublishRecordORM(
        publish_record_id=new_id("pr"),
        generated_content_id=request.generated_content_id,
        platform_code=request.platform_code,
        publish_channel=request.publish_channel,
        published_url=request.published_url,
        published_at=request.published_at,
        operator=request.operator,
        status="published",
        notes=request.notes,
        created_at=now,
        updated_at=now,
    )
    db.add(record)
    content.status = "published"
    content.updated_at = now
    db.commit()
    return JSONResponse(
        status_code=200,
        content=success_response(
            {
                "id": record.publish_record_id,
                "publish_record_id": record.publish_record_id,
                "generated_content_id": record.generated_content_id,
                "platform_code": record.platform_code,
                "status": record.status,
            }
        ),
    )


@router.post("/publish-records/{publish_record_id}/snapshots")
def create_publish_snapshot(
    publish_record_id: str, request: PublishSnapshotCreateRequest, db: Session = Depends(get_db)
) -> JSONResponse:
    record = db.get(PublishRecordORM, publish_record_id)
    if not record:
        return JSONResponse(status_code=404, content=error_response("NOT_FOUND", "publish record not found"))

    snap = PerformanceSnapshotORM(
        snapshot_id=new_id("ps"),
        publish_record_id=publish_record_id,
        like_count=request.like_count,
        comment_count=request.comment_count,
        favorite_count=request.favorite_count,
        share_count=request.share_count,
        view_count=request.view_count,
        retention_rate=request.retention_rate,
        captured_at=request.captured_at,
        created_at=_now(),
    )
    db.add(snap)
    db.commit()
    return JSONResponse(
        status_code=200,
        content=success_response(
            {
                "snapshot_id": snap.snapshot_id,
                "publish_record_id": snap.publish_record_id,
                "captured_at": snap.captured_at.isoformat(),
            }
        ),
    )


@router.get("/publish-records")
def list_publish_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    include_archived: bool = Query(False),
    db: Session = Depends(get_db),
) -> dict:
    q = db.query(PublishRecordORM)
    if not include_archived:
        q = q.filter(PublishRecordORM.status != "archived")
    q = q.order_by(PublishRecordORM.created_at.desc())
    items, total = _paginate(q, page, page_size)
    rows = [
        {
            "id": i.publish_record_id,
            "publish_record_id": i.publish_record_id,
            "generated_content_id": i.generated_content_id,
            "platform_code": i.platform_code,
            "publish_channel": i.publish_channel,
            "published_url": i.published_url,
            "published_at": i.published_at.isoformat() if i.published_at else None,
            "operator": i.operator,
            "status": i.status,
            "notes": i.notes,
            "created_at": i.created_at.isoformat(),
            "updated_at": i.updated_at.isoformat(),
        }
        for i in items
    ]
    return success_response({"items": rows, "page": page, "page_size": page_size, "total": total})


@router.delete("/publish-records/{publish_record_id}")
def delete_publish_record(publish_record_id: str, db: Session = Depends(get_db)) -> JSONResponse:
    record = db.get(PublishRecordORM, publish_record_id)
    if not record:
        return JSONResponse(status_code=404, content=error_response("NOT_FOUND", "publish record not found"))
    if record.status == "archived":
        return JSONResponse(
            status_code=200,
            content=success_response({"publish_record_id": record.publish_record_id, "status": record.status}),
        )
    if record.status != "archived":
        record.status = "archived"
        record.updated_at = _now()
        db.commit()
    return JSONResponse(
        status_code=200,
        content=success_response({"publish_record_id": record.publish_record_id, "status": record.status}),
    )


# ==================== 闁硅翰鍎撮妴鍐春?====================

from app.api.routes_reports import router as reports_router
from app.api.routes_templates import router as templates_router

router.include_router(templates_router)
router.include_router(reports_router)



from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from app.api.common import error_response, success_response
from app.core.database import get_db
from app.models.orm import GenerationJobORM, GeneratedContentORM, PostORM, PublishRecordORM, TemplateORM

router = APIRouter()


def _now() -> datetime:
    return datetime.now(UTC)


@router.get("/reports/templates/performance")
def get_template_performance_report(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("usage_count"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
) -> dict:
    templates = db.query(TemplateORM).filter(TemplateORM.status != "archived").all()
    report = []

    for template in templates:
        jobs = db.query(GenerationJobORM).filter(GenerationJobORM.selected_template_id == template.template_id).all()
        usage_count = len(jobs)
        if usage_count == 0:
            continue

        reviewed_count = 0
        approved_count = 0
        published_count = 0
        total_likes = 0
        total_favorites = 0

        for job in jobs:
            content = db.get(GeneratedContentORM, job.generated_content_id)
            if not content:
                continue

            if content.fact_check_status:
                reviewed_count += 1
                if content.fact_check_status == "approved":
                    approved_count += 1

            publishes = db.query(PublishRecordORM).filter(
                PublishRecordORM.generated_content_id == content.content_id,
                PublishRecordORM.status == "published",
            ).all()
            published_count += len(publishes)

            if content.source_trace:
                total_likes += content.source_trace.get("like_count", 0)
                total_favorites += content.source_trace.get("favorite_count", 0)

        report.append(
            {
                "template_id": template.template_id,
                "template_name": template.name,
                "template_type": template.template_type,
                "usage_count": usage_count,
                "reviewed_count": reviewed_count,
                "approval_rate": round(approved_count / reviewed_count * 100, 2) if reviewed_count > 0 else 0,
                "published_count": published_count,
                "avg_likes": round(total_likes / usage_count, 2) if usage_count > 0 else 0,
                "avg_favorites": round(total_favorites / usage_count, 2) if usage_count > 0 else 0,
            }
        )

    sortable_fields = {
        "usage_count",
        "reviewed_count",
        "approval_rate",
        "published_count",
        "avg_likes",
        "avg_favorites",
        "template_name",
    }
    if sort_by not in sortable_fields:
        sort_by = "usage_count"

    reverse = sort_order == "desc"
    report.sort(key=lambda item: item.get(sort_by) or 0, reverse=reverse)

    total = len(report)
    start = (page - 1) * page_size
    end = start + page_size
    paged_items = report[start:end]

    return success_response(
        {
            "items": paged_items,
            "page": page,
            "page_size": page_size,
            "total": total,
            "sort_by": sort_by,
            "sort_order": sort_order,
        }
    )


@router.post("/reports/posts/export")
def export_posts_report(
    keyword: str | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    only_historical_hot: bool = Query(False),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    format: str = Query("csv", pattern="^(csv|markdown)$"),
    db: Session = Depends(get_db),
) -> JSONResponse:
    q = db.query(PostORM).filter(PostORM.status != "archived")

    if keyword:
        q = q.filter(PostORM.title.contains(keyword) | PostORM.content_text.contains(keyword))

    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
            q = q.filter(PostORM.created_at >= start_dt)
        except ValueError:
            return JSONResponse(
                status_code=400,
                content=error_response("INVALID_DATE", "start_date must be ISO 8601 date/time"),
            )

    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
            q = q.filter(PostORM.created_at <= end_dt)
        except ValueError:
            return JSONResponse(
                status_code=400,
                content=error_response("INVALID_DATE", "end_date must be ISO 8601 date/time"),
            )

    if only_historical_hot:
        q = q.filter(PostORM.is_historical_hot == True)

    order_fields = {
        "created_at": PostORM.created_at,
        "like_count": PostORM.like_count,
        "comment_count": PostORM.comment_count,
        "favorite_count": PostORM.favorite_count,
        "share_count": PostORM.share_count,
        "view_count": PostORM.view_count,
    }

    if sort_by == "engagement":
        engagement_expr = PostORM.like_count + PostORM.comment_count + PostORM.favorite_count + PostORM.share_count
        order_col = engagement_expr
    else:
        order_col = order_fields.get(sort_by, PostORM.created_at)

    order_expr = asc(order_col) if sort_order == "asc" else desc(order_col)
    posts = q.order_by(order_expr).all()

    if format == "csv":
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["post_id", "platform", "title", "author", "published_at", "likes", "comments", "favorites", "keywords", "source_url"])

        for post in posts:
            writer.writerow(
                [
                    post.post_id,
                    post.platform_code,
                    post.title,
                    post.author_name or "",
                    post.published_at.isoformat() if post.published_at else "",
                    post.like_count or 0,
                    post.comment_count or 0,
                    post.favorite_count or 0,
                    ", ".join(post.topic_keywords or []),
                    post.source_url,
                ]
            )

        return JSONResponse(
            status_code=200,
            content=success_response(
                {
                    "format": "csv",
                    "count": len(posts),
                    "sort_by": sort_by,
                    "sort_order": sort_order,
                    "data": output.getvalue(),
                }
            ),
        )

    md_lines = [
        "# Post Research Report",
        "",
        f"Export time: {_now().isoformat()}",
        f"Post count: {len(posts)}",
        "",
        "## Post List",
        "",
    ]

    for idx, post in enumerate(posts, 1):
        md_lines.append(f"### {idx}. {post.title}")
        md_lines.append("")
        md_lines.append(f"- **Platform**: {post.platform_code}")
        md_lines.append(f"- **Author**: {post.author_name or 'unknown'}")
        if post.published_at:
            md_lines.append(f"- **Published at**: {post.published_at.isoformat()}")
        md_lines.append(
            f"- **Engagement**: likes={post.like_count or 0} comments={post.comment_count or 0} favorites={post.favorite_count or 0}"
        )
        if post.topic_keywords:
            md_lines.append(f"- **Keywords**: {', '.join(post.topic_keywords)}")
        md_lines.append("")
        md_lines.append("**Summary**:")
        md_lines.append("")
        md_lines.append(f"{post.content_text[:200]}..." if len(post.content_text) > 200 else post.content_text)
        md_lines.append("")
        md_lines.append(f"[View source]({post.source_url})")
        md_lines.append("")

    return JSONResponse(
        status_code=200,
        content=success_response(
            {
                "format": "markdown",
                "count": len(posts),
                "sort_by": sort_by,
                "sort_order": sort_order,
                "data": "\n".join(md_lines),
            }
        ),
    )

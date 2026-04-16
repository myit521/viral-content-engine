from __future__ import annotations

import asyncio
import logging
import re
import time
from datetime import UTC, datetime
from urllib.parse import urlparse

import httpx
from sqlalchemy.orm import Session

from app.collectors.zhihu.adapter import ZhihuDataAdapter
from app.collectors.zhihu.executor import ExecuteParams, executor
from app.core.id_generator import new_id
from app.core.metrics import crawl_metrics
from app.core.settings import crawl_settings
from app.models.orm import CollectorTaskORM, PostORM
from app.models.schemas import CollectorTask, CollectorTaskCreateRequest, Post
from app.services.text_preprocess_service import text_preprocess_service

logger = logging.getLogger(__name__)


class CollectionService:
    def __init__(self) -> None:
        self.zhihu_adapter = ZhihuDataAdapter()
        self._proxy_pool_paused = False

    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC)

    @staticmethod
    def _to_schema(task: CollectorTaskORM) -> CollectorTask:
        return CollectorTask(
            id=task.task_id,
            task_id=task.task_id,
            platform_code=task.platform_code,
            task_type=task.task_type,
            query_keyword=task.query_keyword,
            trigger_mode=task.trigger_mode,
            collect_type=task.collect_type,
            source_url=task.source_url,
            source_id=task.source_id,
            status=task.status,
            success_count=task.success_count,
            failed_count=task.failed_count,
            retry_count=task.retry_count,
            execution_status=task.execution_status,
            raw_output_path=task.raw_output_path,
            error_message=task.error_message,
            started_at=task.started_at,
            finished_at=task.finished_at,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )

    @staticmethod
    def _post_to_schema(post: PostORM) -> Post:
        return Post(
            id=post.post_id,
            post_id=post.post_id,
            platform_code=post.platform_code,
            title=post.title,
            content_text=post.content_text,
            source_url=post.source_url,
            source_type=post.source_type,
            author_name=post.author_name,
            published_at=post.published_at,
            like_count=post.like_count,
            comment_count=post.comment_count,
            favorite_count=post.favorite_count,
            share_count=post.share_count,
            view_count=post.view_count,
            is_historical_hot=post.is_historical_hot,
            note=post.note,
            topic_keywords=post.topic_keywords or [],
            status=post.status,
            created_at=post.created_at,
            updated_at=post.updated_at,
        )

    def create_task(self, db: Session, request: CollectorTaskCreateRequest) -> CollectorTask:
        now = self._now()
        collect_type = request.collect_type
        source_id = request.source_id
        source_url = request.source_url
        query_keyword = self._normalize_possible_mojibake(request.query_keyword)

        if source_url and not source_id:
            parsed = self._parse_zhihu_url(source_url)
            if parsed:
                collect_type = parsed["collect_type"]
                source_id = parsed["source_id"]

        task = CollectorTaskORM(
            task_id=new_id("ct"),
            platform_code=request.platform_code,
            task_type=request.task_type,
            query_keyword=query_keyword,
            collect_type=collect_type,
            source_url=source_url,
            source_id=source_id,
            limit_count=request.limit,
            trigger_mode="manual",
            status="pending",
            execution_status="PENDING",
            created_at=now,
            updated_at=now,
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return self._to_schema(task)

    def run_task(self, db: Session, task_id: str) -> CollectorTask:
        task = db.get(CollectorTaskORM, task_id)
        if not task:
            raise KeyError("collector task not found")

        if task.source_url and not task.source_id:
            parsed = self._parse_zhihu_url(task.source_url)
            if not parsed:
                task.status = "failed"
                task.execution_status = "FAILED"
                task.error_message = "unsupported zhihu url"
                task.finished_at = self._now()
                task.updated_at = self._now()
                db.commit()
                db.refresh(task)
                return self._to_schema(task)
            task.collect_type = parsed["collect_type"]
            task.source_id = parsed["source_id"]

        task.status = "running"
        task.execution_status = "RUNNING"
        task.started_at = self._now()
        task.updated_at = self._now()
        db.commit()

        retry_count = 0
        active_proxy: str | None = None
        backup_proxy_used = False
        execute_result = None

        if crawl_settings.proxy_pool and not self._proxy_pool_paused:
            active_proxy = crawl_settings.proxy_pool[0]

        crawl_metrics.task_started()
        try:
            while True:
                execute_result = self._execute_sync(
                    ExecuteParams(
                        task_id=task.task_id,
                        platform=task.platform_code,
                        collect_type=task.collect_type,
                        query_keyword=self._normalize_possible_mojibake(task.query_keyword),
                        source_id=task.source_id,
                        source_url=task.source_url,
                        limit=task.limit_count,
                        proxy=active_proxy,
                    )
                )

                task.raw_output_path = execute_result.raw_output_file
                task.execution_status = execute_result.status
                task.error_message = execute_result.error_message
                task.retry_count = retry_count
                task.updated_at = self._now()
                db.commit()

                if execute_result.status == "RATE_LIMITED":
                    if retry_count < crawl_settings.max_retry_count:
                        wait_seconds = crawl_settings.retry_exponential_base * (5**retry_count)
                        retry_count += 1
                        task.retry_count = retry_count
                        task.execution_status = "RATE_LIMITED"
                        task.updated_at = self._now()
                        db.commit()
                        time.sleep(wait_seconds)
                        continue
                    task.execution_status = "FAILED"
                    task.error_message = "rate limited beyond max retry count"
                    db.commit()
                    break

                if execute_result.status == "PROXY_FAILED" and crawl_settings.proxy_pool:
                    if not backup_proxy_used and len(crawl_settings.proxy_pool) > 1:
                        backup_proxy_used = True
                        active_proxy = crawl_settings.proxy_pool[1]
                        retry_count += 1
                        task.retry_count = retry_count
                        task.updated_at = self._now()
                        db.commit()
                        continue

                    task.execution_status = "PROXY_FAILED"
                    task.error_message = "proxy failed; pause current proxy pool and require intervention"
                    self._proxy_pool_paused = True
                    db.commit()
                    break

                if execute_result.status == "VERIFICATION_REQUIRED":
                    self._notify_verification_required(task.task_id, task.platform_code)

                break

            assert execute_result is not None

            if execute_result.status == "SUCCESS" and execute_result.raw_output_file:
                parsed = self.zhihu_adapter.parse_raw_file(execute_result.raw_output_file)
                now = self._now()
                for reason in parsed.skipped_reasons:
                    logger.warning("adapter record skipped task_id=%s reason=%s", task.task_id, reason)

                for item in parsed.collected:
                    normalized_title = text_preprocess_service.preprocess(item.title or "").cleaned_text or "untitled"
                    normalized_content = text_preprocess_service.preprocess(item.content_text or "").markdown_text
                    post = PostORM(
                        post_id=new_id("post"),
                        platform_code=task.platform_code,
                        title=normalized_title,
                        content_text=normalized_content or (item.content_text or ""),
                        source_url=item.source_url or f"https://www.zhihu.com/question/{item.source_id or 'unknown'}",
                        source_type="collector",
                        author_name=item.author_name,
                        published_at=item.published_at,
                        like_count=item.like_count,
                        comment_count=item.comment_count,
                        favorite_count=item.favorite_count,
                        share_count=item.share_count,
                        view_count=item.view_count,
                        is_historical_hot=item.is_historical_hot,
                        topic_keywords=item.topic_keywords,
                        status="normalized",
                        created_at=now,
                        updated_at=now,
                    )
                    db.add(post)

                task.success_count = len(parsed.collected)
                task.failed_count = parsed.skipped_count
                if task.success_count == 0:
                    task.status = "failed"
                    task.execution_status = "FAILED"
                    task.error_message = "no valid records after adapter validation"
                elif task.failed_count > 0:
                    task.status = "partial_failed"
                    task.execution_status = "SUCCESS"
                    task.error_message = "; ".join(parsed.skipped_reasons[:3])
                else:
                    task.status = "succeeded"
                    task.execution_status = "SUCCESS"
                    task.error_message = None
            else:
                task.status = "failed"
                if task.execution_status not in {
                    "RATE_LIMITED",
                    "LOGIN_EXPIRED",
                    "PROXY_FAILED",
                    "VERIFICATION_REQUIRED",
                    "FAILED",
                }:
                    task.execution_status = "FAILED"

            task.finished_at = self._now()
            task.updated_at = self._now()
            db.commit()
            db.refresh(task)
            return self._to_schema(task)
        finally:
            duration_seconds = 0.0
            if execute_result is not None:
                duration_seconds = execute_result.duration_seconds
            crawl_metrics.task_finished(success=task.execution_status == "SUCCESS", duration_seconds=duration_seconds)

    def list_posts(self, db: Session) -> list[Post]:
        posts = db.query(PostORM).order_by(PostORM.created_at.desc()).all()
        return [self._post_to_schema(item) for item in posts]

    @staticmethod
    def _execute_sync(params: ExecuteParams):
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(executor.execute_task(params))
        finally:
            loop.close()

    @staticmethod
    def _parse_zhihu_url(url: str) -> dict[str, str] | None:
        try:
            parsed = urlparse(url)
            host = parsed.netloc.lower()
            path = parsed.path.strip("/")
        except Exception:
            return None

        if "zhihu.com" not in host:
            return None

        question_match = re.fullmatch(r"question/(\d+)(?:/answer/\d+)?", path)
        if question_match:
            return {"collect_type": "detail", "source_id": question_match.group(1)}

        if host == "zhuanlan.zhihu.com":
            article_match = re.fullmatch(r"p/(\d+)", path)
            if article_match:
                return {"collect_type": "detail", "source_id": article_match.group(1)}

        pin_match = re.fullmatch(r"pin/([\w-]+)", path)
        if pin_match:
            return {"collect_type": "detail", "source_id": pin_match.group(1)}

        people_match = re.fullmatch(r"people/([\w-]+)", path)
        if people_match:
            return {"collect_type": "creator", "source_id": people_match.group(1)}

        return None

    @staticmethod
    def _notify_verification_required(task_id: str, platform: str) -> None:
        if not crawl_settings.verification_webhook:
            return
        try:
            httpx.post(
                crawl_settings.verification_webhook,
                json={
                    "event": "VERIFICATION_REQUIRED",
                    "task_id": task_id,
                    "platform": platform,
                    "message": "Crawler hit captcha/slider challenge and requires manual intervention.",
                },
                timeout=10.0,
            )
        except Exception as exc:
            logger.warning("verification webhook failed task_id=%s error=%s", task_id, exc)

    @staticmethod
    def _normalize_possible_mojibake(value: str | None) -> str:
        if not value:
            return ""

        candidates = [value]
        for source_encoding in ("latin-1", "gbk"):
            try:
                repaired = value.encode(source_encoding).decode("utf-8")
            except (UnicodeEncodeError, UnicodeDecodeError):
                continue
            candidates.append(repaired)

        best = value
        best_score = CollectionService._encoding_score(value)
        for candidate in candidates[1:]:
            score = CollectionService._encoding_score(candidate)
            if score > best_score:
                best = candidate
                best_score = score
        return best

    @staticmethod
    def _count_cjk_chars(value: str) -> int:
        return sum(1 for ch in value if "\u4e00" <= ch <= "\u9fff")

    @staticmethod
    def _encoding_score(value: str) -> tuple[int, int]:
        question_penalty = -value.count("?")
        return (CollectionService._count_cjk_chars(value), question_penalty)


collection_service = CollectionService()

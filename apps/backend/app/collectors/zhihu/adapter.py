from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.collectors.base import CollectedPost


@dataclass
class AdapterParseResult:
    collected: list[CollectedPost]
    skipped_count: int
    skipped_reasons: list[str]


class ZhihuDataAdapter:
    def parse_raw_file(self, raw_file: str) -> AdapterParseResult:
        path = Path(raw_file)
        payload = json.loads(path.read_text(encoding="utf-8"))

        if isinstance(payload, dict):
            items = payload.get("items", [])
        elif isinstance(payload, list):
            items = payload
        else:
            items = []

        collected: list[CollectedPost] = []
        skipped_reasons: list[str] = []

        for index, item in enumerate(items):
            if not isinstance(item, dict):
                skipped_reasons.append(f"record_{index}: invalid item type")
                continue

            content_text = self._pick_content(item)
            publish_time = self._pick_publish_time(item) or self._fallback_publish_time(path)
            author_name = self._pick_author(item, content_text) or "未知作者"
            if not content_text:
                missing = []
                if not content_text:
                    missing.append("content")
                skipped_reasons.append(f"record_{index}: missing fields={','.join(missing)}")
                continue

            title = item.get("title") or (content_text[:30] if content_text else f"zhihu-{index}")
            topic_keywords = item.get("topic_keywords", [])
            if not topic_keywords and item.get("source_keyword"):
                topic_keywords = [str(item.get("source_keyword"))]

            metrics = item.get("metrics") or {}
            like_count = self._to_int(metrics.get("like_count", item.get("voteup_count", 0)))
            comment_count = self._to_int(metrics.get("comment_count", item.get("comment_count", 0)))
            favorite_count = self._to_int(metrics.get("favorite_count", 0))
            share_count = self._to_int(metrics.get("share_count", 0))
            view_count = self._to_int(metrics.get("view_count", 0))

            collected.append(
                CollectedPost(
                    title=title,
                    content_text=content_text,
                    source_url=str(item.get("url") or item.get("content_url") or ""),
                    topic_keywords=[str(keyword) for keyword in topic_keywords if str(keyword).strip()],
                    author_name=author_name,
                    published_at=publish_time,
                    like_count=like_count,
                    comment_count=comment_count,
                    favorite_count=favorite_count,
                    share_count=share_count,
                    view_count=view_count,
                    is_historical_hot=bool(item.get("is_historical_hot", False)),
                    source_id=str(item.get("source_id") or item.get("content_id") or ""),
                )
            )

        return AdapterParseResult(
            collected=collected,
            skipped_count=len(skipped_reasons),
            skipped_reasons=skipped_reasons,
        )

    @staticmethod
    def _pick_content(item: dict[str, Any]) -> str:
        return str(item.get("content") or item.get("content_text") or "").strip()

    @staticmethod
    def _pick_author(item: dict[str, Any], content_text: str = "") -> str:
        author_info = item.get("author_info") or {}
        if isinstance(author_info, dict) and author_info.get("name"):
            return str(author_info.get("name")).strip()
        direct_name = str(item.get("user_nickname") or item.get("author_name") or "").strip()
        if direct_name:
            return direct_name

        for separator in ("：", ":"):
            prefix, matched, _ = content_text.partition(separator)
            candidate = prefix.strip()
            if matched and 0 < len(candidate) <= 20 and "\n" not in candidate:
                return candidate

        return ""

    def _pick_publish_time(self, item: dict[str, Any]) -> datetime | None:
        return self._parse_datetime(item.get("create_time") or item.get("created_time"))

    @staticmethod
    def _fallback_publish_time(path: Path) -> datetime:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)

    @staticmethod
    def _parse_datetime(value: Any) -> datetime | None:
        if value is None or value == "":
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, (int, float)):
            if value <= 0:
                return None
            try:
                return datetime.fromtimestamp(float(value), tz=UTC)
            except (OverflowError, OSError, ValueError):
                return None

        text = str(value).strip()
        if not text:
            return None
        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None

    @staticmethod
    def _to_int(value: Any) -> int:
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class CollectedPost:
    title: str
    content_text: str
    source_url: str
    topic_keywords: list[str]
    author_name: str | None = None
    published_at: datetime | None = None
    like_count: int = 0
    comment_count: int = 0
    favorite_count: int = 0
    share_count: int = 0
    view_count: int = 0
    is_historical_hot: bool = False
    source_id: str | None = None


class BaseCollector(ABC):
    @abstractmethod
    def collect(self, query_keyword: str, limit: int) -> list[CollectedPost]:
        raise NotImplementedError

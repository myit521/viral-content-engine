from __future__ import annotations

import threading
import time
from typing import Any, Callable

from app.core.settings import cache_settings


class InMemoryTTLCache:
    def __init__(self) -> None:
        self._store: dict[str, tuple[float, Any]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Any | None:
        now = time.time()
        with self._lock:
            item = self._store.get(key)
            if item is None:
                return None
            expires_at, value = item
            if expires_at < now:
                self._store.pop(key, None)
                return None
            return value

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        ttl = ttl_seconds or cache_settings.default_ttl_seconds
        expires_at = time.time() + max(ttl, 1)
        with self._lock:
            self._store[key] = (expires_at, value)

    def invalidate(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)

    def invalidate_prefix(self, prefix: str) -> None:
        with self._lock:
            keys = [k for k in self._store if k.startswith(prefix)]
            for key in keys:
                self._store.pop(key, None)

    def get_or_set(self, key: str, loader: Callable[[], Any], ttl_seconds: int | None = None) -> Any:
        existing = self.get(key)
        if existing is not None:
            return existing
        value = loader()
        self.set(key, value, ttl_seconds=ttl_seconds)
        return value


class CacheService:
    def __init__(self) -> None:
        self._memory = InMemoryTTLCache()

    @property
    def enabled(self) -> bool:
        return cache_settings.enabled

    def get(self, key: str) -> Any | None:
        if not self.enabled:
            return None
        return self._memory.get(key)

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        if not self.enabled:
            return
        self._memory.set(key, value, ttl_seconds=ttl_seconds)

    def invalidate(self, key: str) -> None:
        self._memory.invalidate(key)

    def invalidate_prefix(self, prefix: str) -> None:
        self._memory.invalidate_prefix(prefix)

    def get_or_set(self, key: str, loader: Callable[[], Any], ttl_seconds: int | None = None) -> Any:
        if not self.enabled:
            return loader()
        return self._memory.get_or_set(key, loader, ttl_seconds=ttl_seconds)


cache_service = CacheService()

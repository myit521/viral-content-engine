from __future__ import annotations

from dataclasses import dataclass


@dataclass
class _FallbackStore:
    running: int = 0
    success_total: int = 0
    failed_total: int = 0
    duration_sum: float = 0.0
    duration_count: int = 0


class CrawlMetrics:
    def __init__(self) -> None:
        self._fallback = _FallbackStore()
        self._prom_enabled = False
        self._content_type = "text/plain; version=0.0.4"

        try:
            from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Counter, Gauge, Histogram

            registry = CollectorRegistry()
            self._running = Gauge(
                "crawler_running_tasks",
                "Current running crawler tasks",
                registry=registry,
            )
            self._success = Counter(
                "crawler_success_total",
                "Total successful crawler tasks",
                registry=registry,
            )
            self._failed = Counter(
                "crawler_failed_total",
                "Total failed crawler tasks",
                registry=registry,
            )
            self._duration = Histogram(
                "crawler_duration_seconds",
                "Crawler task execution duration in seconds",
                registry=registry,
            )
            self._avg_duration = Gauge(
                "crawler_avg_duration_seconds",
                "Average crawler task execution duration in seconds",
                registry=registry,
            )
            self._registry = registry
            self._content_type = CONTENT_TYPE_LATEST
            self._prom_enabled = True
        except Exception:
            self._registry = None

    @property
    def content_type(self) -> str:
        return self._content_type

    def task_started(self) -> None:
        if self._prom_enabled:
            self._running.inc()
            return
        self._fallback.running += 1

    def task_finished(self, success: bool, duration_seconds: float) -> None:
        duration_seconds = max(duration_seconds, 0.0)
        if self._prom_enabled:
            self._running.dec()
            if success:
                self._success.inc()
            else:
                self._failed.inc()
            self._duration.observe(duration_seconds)
            # Histogram already has _sum/_count; this gauge is for direct average consumption.
            total_count = self._success._value.get() + self._failed._value.get()
            if total_count > 0:
                total_sum = self._duration._sum.get()
                self._avg_duration.set(total_sum / total_count)
            return

        self._fallback.running = max(self._fallback.running - 1, 0)
        if success:
            self._fallback.success_total += 1
        else:
            self._fallback.failed_total += 1
        self._fallback.duration_sum += duration_seconds
        self._fallback.duration_count += 1

    def render(self) -> str:
        if self._prom_enabled:
            from prometheus_client import generate_latest

            return generate_latest(self._registry).decode("utf-8")

        avg = 0.0
        if self._fallback.duration_count > 0:
            avg = self._fallback.duration_sum / self._fallback.duration_count
        return "\n".join(
            [
                "# TYPE crawler_running_tasks gauge",
                f"crawler_running_tasks {self._fallback.running}",
                "# TYPE crawler_success_total counter",
                f"crawler_success_total {self._fallback.success_total}",
                "# TYPE crawler_failed_total counter",
                f"crawler_failed_total {self._fallback.failed_total}",
                "# TYPE crawler_avg_duration_seconds gauge",
                f"crawler_avg_duration_seconds {avg}",
                "",
            ]
        )


crawl_metrics = CrawlMetrics()

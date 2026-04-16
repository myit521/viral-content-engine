from __future__ import annotations

import os
import json
import tempfile
import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


def _load_local_env() -> None:
    env_path = Path.cwd() / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue

        # Keep existing environment variables untouched; only fill missing keys from .env.
        normalized = value.strip().strip('"').strip("'")
        if key not in os.environ:
            os.environ[key] = normalized


_load_local_env()


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _to_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _load_json_list(value: str | None) -> list[dict] | None:
    if not value:
        return None
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, list):
        return None
    cleaned: list[dict] = []
    for item in parsed:
        if isinstance(item, dict):
            cleaned.append(item)
    return cleaned


@dataclass(frozen=True)
class CrawlSettings:
    max_concurrent_tasks: int = int(os.getenv("CRAWL_MAX_CONCURRENT_TASKS", "2"))
    task_timeout_seconds: int = int(os.getenv("CRAWL_TASK_TIMEOUT_SECONDS", "300"))
    retry_exponential_base: int = int(os.getenv("CRAWL_RETRY_EXPONENTIAL_BASE", "60"))
    max_retry_count: int = int(os.getenv("CRAWL_MAX_RETRY_COUNT", "3"))
    temp_user_data_dir_prefix: str = os.getenv(
        "CRAWL_TEMP_USER_DATA_DIR_PREFIX",
        str(Path(tempfile.gettempdir()) / "mediacrawler_"),
    )
    raw_output_root: str = os.getenv(
        "CRAWL_RAW_OUTPUT_ROOT",
        str(Path("data") / "raw"),
    )
    logs_dir: str = os.getenv(
        "CRAWL_LOGS_DIR",
        str(Path("logs")),
    )
    persistent_browser_state_root: str = os.getenv(
        "CRAWL_PERSISTENT_BROWSER_STATE_ROOT",
        str(Path("data") / "browser_state"),
    )
    mediacrawler_executable: str = os.getenv("MEDIACRAWLER_EXECUTABLE", "mediacrawler")
    mediacrawler_project_dir: str = os.getenv(
        "MEDIACRAWLER_PROJECT_DIR",
        str(Path("external") / "MediaCrawler"),
    )
    mediacrawler_enable_real: bool = _to_bool(os.getenv("MEDIACRAWLER_ENABLE_REAL"), default=False)
    fallback_to_mock: bool = _to_bool(os.getenv("MEDIACRAWLER_FALLBACK_MOCK"), default=True)
    proxy_pool: list[str] = field(default_factory=lambda: _split_csv(os.getenv("CRAWL_PROXY_POOL")))
    verification_webhook: str | None = os.getenv("CRAWL_VERIFICATION_WEBHOOK")


crawl_settings = CrawlSettings()


@dataclass(frozen=True)
class AISettings:
    api_key: str | None = os.getenv("OPENAI_API_KEY")
    base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    default_model_name: str = os.getenv("DEFAULT_MODEL_NAME", "gpt-4.1-mini")
    request_timeout_seconds: float = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "60"))
    max_retries: int = int(os.getenv("OPENAI_MAX_RETRIES", "2"))
    prompt_root: str = os.getenv(
        "PROMPT_ROOT",
        str(Path("shared") / "contracts" / "prompts"),
    )
    allow_mock_fallback: bool = _to_bool(os.getenv("AI_ALLOW_MOCK_FALLBACK"), default=True)
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    @property
    def configured(self) -> bool:
        if not self.api_key or not self.base_url:
            return False
        key = self.api_key.strip()
        placeholders = {"your-api-key-here", "sk-xxxxx", "replace-me"}
        if key in placeholders:
            return False
        return True


ai_settings = AISettings()


@dataclass(frozen=True)
class ModelProfiles:
    """Model selection profiles for different AI task scenarios."""

    analysis_model: str = os.getenv("AI_ANALYSIS_MODEL", "gpt-4.1-mini")
    generation_model: str = os.getenv("AI_GENERATION_MODEL", "gpt-4.1-mini")
    template_induction_model: str = os.getenv("AI_TEMPLATE_INDUCTION_MODEL", "gpt-4.1-mini")
    preprocessing_model: str = os.getenv("AI_PREPROCESSING_MODEL", "gpt-4.1-mini")
    fallback_model: str = os.getenv("AI_FALLBACK_MODEL", "gpt-4.1-mini")

    # openai, dashscope, zhipu, custom
    provider: str = os.getenv("AI_PROVIDER", "openai")

    def __post_init__(self):
        logger.info(
            "AI models loaded: analysis=%s generation=%s provider=%s",
            self.analysis_model,
            self.generation_model,
            self.provider,
        )

    @property
    def provider_base_url(self) -> str:
        """Resolve provider-specific base URL."""
        provider_urls = {
            "openai": "https://api.openai.com/v1",
            "dashscope": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "zhipu": "https://open.bigmodel.cn/api/paas/v4",
        }
        return provider_urls.get(self.provider, os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"))


model_profiles = ModelProfiles()


def _default_model_options() -> list[dict]:
    return [
        {
            "scene": "generation",
            "model_name": model_profiles.generation_model,
            "label": "Generation Default",
            "provider": model_profiles.provider,
            "enabled": True,
            "recommended": True,
            "description": "Default model for content generation.",
            "supported_task_types": ["script_generation"],
        },
        {
            "scene": "generation",
            "model_name": "rule-based-mvp",
            "label": "Rule-based MVP",
            "provider": "rule_based",
            "enabled": True,
            "recommended": False,
            "description": "Local fallback generator used in MVP environments.",
            "supported_task_types": ["script_generation"],
        },
        {
            "scene": "template_generation",
            "model_name": model_profiles.template_induction_model,
            "label": "Template AI Default",
            "provider": model_profiles.provider,
            "enabled": True,
            "recommended": True,
            "description": "Recommended model for AI template generation.",
            "supported_task_types": ["template_generation"],
        },
    ]


@dataclass(frozen=True)
class ModelOptionSettings:
    """Model option registry exposed to the frontend model selector."""

    options_json: str | None = os.getenv("AI_MODEL_OPTIONS_JSON")
    generation_default_model: str = os.getenv("AI_GENERATION_DEFAULT_MODEL", model_profiles.generation_model)
    template_generation_default_model: str = os.getenv(
        "AI_TEMPLATE_GENERATION_DEFAULT_MODEL", model_profiles.template_induction_model
    )

    @property
    def options(self) -> list[dict]:
        parsed = _load_json_list(self.options_json)
        if parsed:
            return parsed
        return _default_model_options()


model_option_settings = ModelOptionSettings()


@dataclass(frozen=True)
class CacheSettings:
    enabled: bool = _to_bool(os.getenv("CACHE_ENABLED"), default=True)
    backend: str = os.getenv("CACHE_BACKEND", "memory")
    default_ttl_seconds: int = int(os.getenv("CACHE_DEFAULT_TTL_SECONDS", "60"))
    health_ttl_seconds: int = int(os.getenv("CACHE_HEALTH_TTL_SECONDS", "15"))
    platforms_ttl_seconds: int = int(os.getenv("CACHE_PLATFORMS_TTL_SECONDS", "300"))
    templates_ttl_seconds: int = int(os.getenv("CACHE_TEMPLATES_TTL_SECONDS", "120"))
    ai_ttl_seconds: int = int(os.getenv("CACHE_AI_TTL_SECONDS", "3600"))


cache_settings = CacheSettings()


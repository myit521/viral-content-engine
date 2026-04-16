from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
from datetime import UTC, datetime
from typing import Any

import httpx
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.id_generator import new_id
from app.core.cache import cache_service
from app.core.settings import ai_settings, cache_settings, model_profiles
from app.models.orm import AICallLogORM

logger = logging.getLogger(__name__)


class AIClientError(RuntimeError):
    pass


class AIClient:
    def __init__(self) -> None:
        self._settings = ai_settings

    def _headers(self) -> dict[str, str]:
        if not self._settings.api_key:
            raise AIClientError("OPENAI_API_KEY is not configured.")
        return {
            "Authorization": f"Bearer {self._settings.api_key}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _supports_json_schema() -> bool:
        """Check if the current AI provider supports OpenAI json_schema response format.

        Only the official OpenAI API supports structured outputs with json_schema.
        Third-party compatible APIs (DeepSeek, DashScope, Zhipu, etc.) only support
        {"type": "json_object"}.
        """
        base = ai_settings.base_url.lower()
        # Positive match: only official OpenAI endpoint
        if "openai.com" in base:
            return True
        # Everything else (deepseek, dashscope, zhipu, localhost, custom) → no json_schema
        return False

    def _response_format(self, schema: dict[str, Any]) -> dict[str, Any]:
        if self._supports_json_schema():
            return {
                "type": "json_schema",
                "json_schema": {
                    "name": schema.get("name", "structured_output"),
                    "strict": True,
                    "schema": schema["schema"] if "schema" in schema else schema,
                },
            }
        return {"type": "json_object"}

    def _schema_instruction(self, schema: dict[str, Any]) -> str:
        """Build a prompt suffix describing the expected JSON schema for non-OpenAI providers."""
        if self._supports_json_schema():
            return ""
        raw_schema = schema["schema"] if "schema" in schema else schema
        return (
            "\n\nIMPORTANT: You MUST respond with valid JSON that conforms to the following JSON Schema. "
            "Do NOT include any text outside the JSON object.\n"
            f"```json\n{json.dumps(raw_schema, ensure_ascii=False, indent=2)}\n```"
        )

    def _extract_json_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        choices = payload.get("choices") or []
        if not choices:
            raise AIClientError("AI response did not include choices.")

        message = choices[0].get("message") or {}
        if message.get("parsed"):
            return message["parsed"]

        content = message.get("content")
        if isinstance(content, list):
            for item in content:
                if item.get("type") == "output_text" and item.get("text"):
                    return json.loads(item["text"])
        if isinstance(content, str):
            return json.loads(content)

        text = message.get("text")
        if text:
            return json.loads(text)

        raise AIClientError("AI response did not include parseable JSON content.")

    @staticmethod
    def _cache_key(
        *,
        prompt: str,
        schema: dict[str, Any],
        model: str,
        task_type: str,
        prompt_version: str,
        system_prompt: str | None,
    ) -> str:
        payload = {
            "prompt": prompt,
            "schema": schema,
            "model": model,
            "task_type": task_type,
            "prompt_version": prompt_version,
            "system_prompt": system_prompt or "",
        }
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        return f"ai:chat:{digest}"

    def _log_call(
        self,
        db: Session | None,
        *,
        task_type: str,
        model: str,
        prompt_version: str,
        prompt_text: str,
        response_json: dict[str, Any] | None,
        token_usage: dict[str, Any] | None,
        duration_ms: int,
        status: str,
        error_message: str | None = None,
    ) -> None:
        if db is None:
            return

        log_row = AICallLogORM(
            log_id=new_id("ail"),
            task_type=task_type,
            model_name=model,
            prompt_version=prompt_version,
            prompt_text=prompt_text,
            response_json=response_json,
            token_usage=token_usage or {},
            duration_ms=duration_ms,
            status=status,
            error_message=error_message,
            created_at=datetime.now(UTC),
        )
        db.add(log_row)
        db.flush()

    async def chat_completion(
        self,
        *,
        prompt: str,
        schema: dict[str, Any],
        model: str,
        task_type: str,
        prompt_version: str,
        db: Session | None = None,
        system_prompt: str | None = None,
    ) -> dict[str, Any]:
        start = time.perf_counter()
        cache_key = self._cache_key(
            prompt=prompt,
            schema=schema,
            model=model,
            task_type=task_type,
            prompt_version=prompt_version,
            system_prompt=system_prompt,
        )
        cached = cache_service.get(cache_key)
        if isinstance(cached, dict) and "result" in cached:
            duration_ms = int((time.perf_counter() - start) * 1000)
            self._log_call(
                db,
                task_type=task_type,
                model=model,
                prompt_version=prompt_version,
                prompt_text=prompt,
                response_json=cached.get("result"),
                token_usage=cached.get("usage") or {},
                duration_ms=duration_ms,
                status="cached",
            )
            return {
                "result": cached.get("result"),
                "usage": cached.get("usage") or {},
                "duration_ms": duration_ms,
                "cache_hit": True,
            }

        schema_hint = self._schema_instruction(schema)
        effective_system = (system_prompt or "You are a precise JSON-only assistant.") + schema_hint
        request_payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": effective_system},
                {"role": "user", "content": prompt},
            ],
            "response_format": self._response_format(schema),
        }

        last_error: Exception | None = None
        for attempt in range(self._settings.max_retries + 1):
            try:
                async with httpx.AsyncClient(
                    base_url=self._settings.base_url.rstrip("/"),
                    timeout=self._settings.request_timeout_seconds,
                ) as client:
                    response = await client.post(
                        "/chat/completions",
                        headers=self._headers(),
                        json=request_payload,
                    )
                    response.raise_for_status()
                    payload = response.json()
                    result = self._extract_json_payload(payload)
                    usage = payload.get("usage") or {}
                    duration_ms = int((time.perf_counter() - start) * 1000)
                    self._log_call(
                        db,
                        task_type=task_type,
                        model=model,
                        prompt_version=prompt_version,
                        prompt_text=prompt,
                        response_json=result,
                        token_usage=usage,
                        duration_ms=duration_ms,
                        status="success",
                    )
                    cache_service.set(
                        cache_key,
                        {"result": result, "usage": usage},
                        ttl_seconds=cache_settings.ai_ttl_seconds,
                    )
                    return {
                        "result": result,
                        "usage": usage,
                        "duration_ms": duration_ms,
                        "cache_hit": False,
                    }
            except (httpx.HTTPError, json.JSONDecodeError, KeyError, AIClientError) as exc:
                last_error = exc
                should_retry = attempt < self._settings.max_retries
                if should_retry:
                    await asyncio.sleep(min(2 ** attempt, 4))
                    continue

        duration_ms = int((time.perf_counter() - start) * 1000)
        message = str(last_error) if last_error else "Unknown AI client error"
        self._log_call(
            db,
            task_type=task_type,
            model=model,
            prompt_version=prompt_version,
            prompt_text=prompt,
            response_json=None,
            token_usage=None,
            duration_ms=duration_ms,
            status="failed",
            error_message=message,
        )
        logger.warning("AI call failed: %s", message)
        raise AIClientError(message) from last_error

    def chat_completion_sync(
        self,
        *,
        prompt: str,
        schema: dict[str, Any],
        model: str,
        task_type: str,
        prompt_version: str,
        db: Session | None = None,
        system_prompt: str | None = None,
    ) -> dict[str, Any]:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(
                self.chat_completion(
                    prompt=prompt,
                    schema=schema,
                    model=model,
                    task_type=task_type,
                    prompt_version=prompt_version,
                    db=db,
                    system_prompt=system_prompt,
                )
            )
        finally:
            loop.close()

    def healthcheck_sync(self) -> bool:
        if not self._settings.configured:
            return False
        return True


def schema_from_model(model: type[BaseModel], *, name: str) -> dict[str, Any]:
    return {"name": name, "schema": model.model_json_schema()}


ai_client = AIClient()

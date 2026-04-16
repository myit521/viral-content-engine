from __future__ import annotations

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.cache import cache_service
from app.core.database import Base, engine
from app.main import app
from app.services.ai_client import ai_client


client = TestClient(app)


class TestP2Cache(unittest.TestCase):
    def setUp(self) -> None:
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        cache_service.invalidate_prefix("api:")
        cache_service.invalidate_prefix("ai:")

    def test_templates_list_cache_and_invalidate(self) -> None:
        first = client.get("/api/v1/templates?page=1&page_size=20")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.json()["data"]["total"], 0)

        client.post(
            "/api/v1/templates",
            json={
                "template_type": "script",
                "template_category": "narrative_frame",
                "name": "cache-template",
                "structure_json": {"opening": "a", "body": ["b"], "ending": "c"},
            },
        )

        second = client.get("/api/v1/templates?page=1&page_size=20")
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.json()["data"]["total"], 1)

    def test_ai_call_cache_hit(self) -> None:
        class _Resp:
            def raise_for_status(self) -> None:
                return None

            def json(self) -> dict:
                return {
                    "choices": [{"message": {"content": '{"summary":"ok"}'}}],
                    "usage": {"total_tokens": 10},
                }

        class _Client:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

            async def post(self, *args, **kwargs):
                return _Resp()

        with patch.object(ai_client, "_headers", return_value={}), patch(
            "app.services.ai_client.httpx.AsyncClient", return_value=_Client()
        ) as mocked_async_client:
            first = ai_client.chat_completion_sync(
                prompt="same prompt",
                schema={"name": "t", "schema": {"type": "object", "properties": {"summary": {"type": "string"}}, "required": ["summary"]}},
                model="test-model",
                task_type="analysis",
                prompt_version="analysis.v1",
                db=None,
            )
            second = ai_client.chat_completion_sync(
                prompt="same prompt",
                schema={"name": "t", "schema": {"type": "object", "properties": {"summary": {"type": "string"}}, "required": ["summary"]}},
                model="test-model",
                task_type="analysis",
                prompt_version="analysis.v1",
                db=None,
            )

        self.assertEqual(first["result"]["summary"], "ok")
        self.assertEqual(second["result"]["summary"], "ok")
        self.assertFalse(first.get("cache_hit", False))
        self.assertTrue(second.get("cache_hit", False))
        self.assertEqual(mocked_async_client.call_count, 1)


if __name__ == "__main__":
    unittest.main()

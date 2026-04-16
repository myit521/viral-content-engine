from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from app.core.database import Base, engine
from app.main import app
from app.services.text_preprocess_service import text_preprocess_service


client = TestClient(app)


class TestP0Blockers(unittest.TestCase):
    def setUp(self) -> None:
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    def test_text_preprocess_clean_markdown_segment(self) -> None:
        raw = "<h1>标题</h1><p>第一段&nbsp;内容</p><p>第二段内容</p>"
        result = text_preprocess_service.preprocess(raw)
        self.assertIn("标题", result.cleaned_text)
        self.assertIn("第一段", result.markdown_text)
        self.assertGreaterEqual(len(result.segments), 1)

    def test_manual_import_uses_preprocess(self) -> None:
        resp = client.post(
            "/api/v1/posts/manual-import",
            json={
                "platform_code": "zhihu",
                "title": "<b>测试标题</b>",
                "content_text": "<div>正文 <i>内容</i></div>",
            },
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()["data"]
        self.assertEqual(data["title"], "测试标题")
        self.assertIn("正文", data["content_text"])

    def test_auto_summarize_templates_from_analysis(self) -> None:
        p1 = client.post(
            "/api/v1/posts/manual-import",
            json={"platform_code": "zhihu", "title": "history", "content_text": "c1"},
        ).json()["data"]["post_id"]
        p2 = client.post(
            "/api/v1/posts/manual-import",
            json={"platform_code": "zhihu", "title": "history", "content_text": "c2"},
        ).json()["data"]["post_id"]

        a1 = client.post("/api/v1/analysis-results", json={"post_id": p1}).json()["data"]["analysis_id"]
        a2 = client.post("/api/v1/analysis-results", json={"post_id": p2}).json()["data"]["analysis_id"]

        resp = client.post(
            "/api/v1/templates/auto-summarize",
            json={"analysis_ids": [a1, a2], "min_cluster_size": 2},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()["data"]
        self.assertGreaterEqual(data["created_count"], 1)

    def test_health_ai_not_configured_with_placeholder(self) -> None:
        resp = client.get("/api/v1/health")
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.json()["data"]["ai_configured"])


if __name__ == "__main__":
    unittest.main()

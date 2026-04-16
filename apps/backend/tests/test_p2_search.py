from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from app.core.database import Base, engine
from app.main import app


client = TestClient(app)


class TestSearchFTS(unittest.TestCase):
    def setUp(self) -> None:
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    def test_posts_search_by_title_content_keywords(self) -> None:
        client.post(
            "/api/v1/posts/manual-import",
            json={
                "platform_code": "zhihu",
                "title": "秦始皇统一六国",
                "content_text": "历史叙事与制度改革",
                "topic_keywords": ["history_tag", "qin_dynasty"],
            },
        )
        client.post(
            "/api/v1/posts/manual-import",
            json={
                "platform_code": "zhihu",
                "title": "现代经济观察",
                "content_text": "宏观政策分析",
                "topic_keywords": ["经济"],
            },
        )

        r1 = client.get("/api/v1/posts/search?q=秦始皇")
        self.assertEqual(r1.status_code, 200)
        self.assertGreaterEqual(r1.json()["data"]["total"], 1)

        r2 = client.get("/api/v1/posts/search?q=制度改革")
        self.assertEqual(r2.status_code, 200)
        self.assertGreaterEqual(r2.json()["data"]["total"], 1)

        r3 = client.get("/api/v1/posts/search?q=qin_dynasty")
        self.assertEqual(r3.status_code, 200)
        self.assertGreaterEqual(r3.json()["data"]["total"], 1)

    def test_templates_search_by_name_and_type(self) -> None:
        client.post(
            "/api/v1/templates",
            json={
                "template_type": "script",
                "template_category": "narrative_frame",
                "name": "历史反转脚本",
                "structure_json": {"opening": "a", "body": ["b"], "ending": "c"},
            },
        )
        client.post(
            "/api/v1/templates",
            json={
                "template_type": "title",
                "template_category": "title_hook",
                "name": "科技标题模板",
                "structure_json": {"opening": "a", "body": ["b"], "ending": "c"},
            },
        )

        r1 = client.get("/api/v1/templates/search?q=历史反转")
        self.assertEqual(r1.status_code, 200)
        self.assertGreaterEqual(r1.json()["data"]["total"], 1)

        r2 = client.get("/api/v1/templates/search?q=title")
        self.assertEqual(r2.status_code, 200)
        self.assertGreaterEqual(r2.json()["data"]["total"], 1)


if __name__ == "__main__":
    unittest.main()

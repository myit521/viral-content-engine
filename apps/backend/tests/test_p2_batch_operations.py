from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from app.core.database import Base, engine
from app.main import app


client = TestClient(app)


class TestBatchOperations(unittest.TestCase):
    def setUp(self) -> None:
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    def test_posts_batch_import(self) -> None:
        resp = client.post(
            "/api/v1/posts/batch-import",
            json={
                "items": [
                    {"platform_code": "zhihu", "title": "t1", "content_text": "c1"},
                    {"platform_code": "zhihu", "title": "t2", "content_text": "c2"},
                ]
            },
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()["data"]
        self.assertEqual(data["created_count"], 2)
        self.assertEqual(data["failed_count"], 0)

        list_resp = client.get("/api/v1/posts")
        self.assertEqual(list_resp.status_code, 200)
        self.assertEqual(list_resp.json()["data"]["total"], 2)

    def test_analysis_results_batch_create(self) -> None:
        post_resp = client.post(
            "/api/v1/posts/manual-import",
            json={"platform_code": "zhihu", "title": "an-title", "content_text": "an-content"},
        )
        self.assertEqual(post_resp.status_code, 200)
        post_id = post_resp.json()["data"]["post_id"]

        resp = client.post(
            "/api/v1/analysis-results/batch-create",
            json={"items": [{"post_id": post_id}, {"post_id": "post_not_exists"}]},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()["data"]
        self.assertEqual(data["created_count"], 1)
        self.assertEqual(data["failed_count"], 1)
        self.assertEqual(data["errors"][0]["code"], "NOT_FOUND")

    def test_posts_batch_delete_archive(self) -> None:
        p1 = client.post(
            "/api/v1/posts/manual-import",
            json={"platform_code": "zhihu", "title": "d1", "content_text": "d1"},
        ).json()["data"]["post_id"]
        p2 = client.post(
            "/api/v1/posts/manual-import",
            json={"platform_code": "zhihu", "title": "d2", "content_text": "d2"},
        ).json()["data"]["post_id"]

        client.post(
            "/api/v1/templates",
            json={
                "template_type": "script",
                "template_category": "narrative_frame",
                "name": "ref-template",
                "structure_json": {"opening": "a", "body": ["b"], "ending": "c"},
                "source_post_ids": [p1],
            },
        )

        resp = client.request(
            "DELETE",
            "/api/v1/posts/batch",
            json={"post_ids": [p1, p2, "missing_post"]},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()["data"]
        self.assertEqual(data["archived_count"], 1)
        self.assertEqual(data["failed_count"], 2)
        codes = {item["code"] for item in data["errors"]}
        self.assertIn("CONFLICT", codes)
        self.assertIn("NOT_FOUND", codes)


if __name__ == "__main__":
    unittest.main()

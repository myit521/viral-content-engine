from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from app.core.database import Base, engine
from app.main import app


client = TestClient(app)


class TestAsyncTasks(unittest.TestCase):
    def setUp(self) -> None:
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    def test_create_generation_job_async_and_query_task(self) -> None:
        resp = client.post("/api/v1/generation-jobs?async_mode=true", json={"job_type": "script_generation", "topic": "async gen"})
        self.assertEqual(resp.status_code, 202)
        task_id = resp.json()["data"]["task_id"]

        task_resp = client.get(f"/api/v1/tasks/{task_id}")
        self.assertEqual(task_resp.status_code, 200)
        task = task_resp.json()["data"]
        self.assertEqual(task["task_id"], task_id)
        self.assertIn(task["status"], {"pending", "running", "succeeded", "failed"})

    def test_create_analysis_async_and_query_task(self) -> None:
        post_resp = client.post(
            "/api/v1/posts/manual-import",
            json={
                "platform_code": "zhihu",
                "title": "async analysis title",
                "content_text": "async analysis content",
            },
        )
        self.assertEqual(post_resp.status_code, 200)
        post_id = post_resp.json()["data"]["post_id"]

        resp = client.post("/api/v1/analysis-results?async_mode=true", json={"post_id": post_id})
        self.assertEqual(resp.status_code, 202)
        task_id = resp.json()["data"]["task_id"]

        task_resp = client.get(f"/api/v1/tasks/{task_id}")
        self.assertEqual(task_resp.status_code, 200)
        task = task_resp.json()["data"]
        self.assertEqual(task["task_type"], "analysis_create")
        self.assertIn(task["status"], {"pending", "running", "succeeded", "failed"})

    def test_get_async_task_not_found(self) -> None:
        resp = client.get("/api/v1/tasks/not_found")
        self.assertEqual(resp.status_code, 404)


if __name__ == "__main__":
    unittest.main()

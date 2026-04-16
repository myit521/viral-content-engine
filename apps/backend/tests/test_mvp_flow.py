import unittest

from fastapi.testclient import TestClient

from app.core.database import Base, engine
from app.main import app


client = TestClient(app)


class TestMvpFlow(unittest.TestCase):
    def setUp(self) -> None:
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    def test_mvp_flow(self) -> None:
        create_task_resp = client.post(
            "/api/v1/collector-tasks",
            json={
                "platform_code": "zhihu",
                "task_type": "historical_hot",
                "query_keyword": "qinshihuang",
                "limit": 5,
            },
        )
        self.assertEqual(create_task_resp.status_code, 200)
        task_id = create_task_resp.json()["data"]["task_id"]

        run_resp = client.post(f"/api/v1/collector-tasks/{task_id}/run")
        self.assertEqual(run_resp.status_code, 200)
        self.assertEqual(run_resp.json()["data"]["status"], "succeeded")

        posts_resp = client.get("/api/v1/posts")
        self.assertEqual(posts_resp.status_code, 200)
        posts = posts_resp.json()["data"]["items"]
        self.assertGreater(len(posts), 0)
        post_id = posts[0]["post_id"]

        analysis_resp = client.post(
            "/api/v1/analysis-results",
            json={"post_id": post_id},
        )
        self.assertEqual(analysis_resp.status_code, 200)
        self.assertEqual(analysis_resp.json()["data"]["post_id"], post_id)

        template_resp = client.post(
            "/api/v1/templates",
            json={
                "template_type": "script",
                "template_category": "narrative_frame",
                "name": "history-three-act",
                "structure_json": {
                    "opening": "start with a counterintuitive question",
                    "body": ["background", "conflict", "twist"],
                    "ending": "invite discussion",
                },
                "source_post_ids": [post_id],
            },
        )
        self.assertEqual(template_resp.status_code, 200)
        template_id = template_resp.json()["data"]["template_id"]

        generation_resp = client.post(
            "/api/v1/generation-jobs",
            json={
                "job_type": "script_generation",
                "topic": "what if qinshihuang lived 10 more years",
                "brief": "60s narration",
                "selected_template_id": template_id,
                "reference_post_ids": [post_id],
            },
        )
        self.assertEqual(generation_resp.status_code, 200)
        self.assertEqual(generation_resp.json()["data"]["status"], "reviewing")


if __name__ == "__main__":
    unittest.main()

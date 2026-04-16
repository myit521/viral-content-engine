from __future__ import annotations

import unittest
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from app.core.database import Base, SessionLocal, engine
from app.core.id_generator import new_id
from app.main import app
from app.models.orm import AnalysisResultORM, PostORM
from app.services.generation_service import generation_service
from app.services.template_service import template_service


client = TestClient(app)


class TestP1Features(unittest.TestCase):
    def setUp(self) -> None:
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    def _create_generation_content(self, topic: str = "p1-test-topic") -> str:
        resp = client.post(
            "/api/v1/generation-jobs",
            json={"job_type": "script_generation", "topic": topic},
        )
        self.assertEqual(resp.status_code, 200)
        return resp.json()["data"]["generated_content"]["content_id"]

    def test_generated_content_version_history_and_switch(self) -> None:
        content_id = self._create_generation_content("version-switch")

        create_version_resp = client.post(
            f"/api/v1/generated-contents/{content_id}/versions",
            json={"editor": "owner", "script_text": "v2 script"},
        )
        self.assertEqual(create_version_resp.status_code, 200)
        self.assertEqual(create_version_resp.json()["data"]["version_no"], 2)

        list_resp = client.get(f"/api/v1/generated-contents/{content_id}/versions")
        self.assertEqual(list_resp.status_code, 200)
        self.assertEqual(list_resp.json()["data"]["total"], 2)
        self.assertEqual(list_resp.json()["data"]["items"][0]["version_no"], 2)

        switch_resp = client.patch(f"/api/v1/generated-contents/{content_id}/versions/1")
        self.assertEqual(switch_resp.status_code, 200)
        self.assertEqual(switch_resp.json()["data"]["current_version_no"], 1)

    def test_generated_content_fact_check(self) -> None:
        content_id = self._create_generation_content("fact-check-content")
        resp = client.post(
            f"/api/v1/generated-contents/{content_id}/fact-check",
            json={"fact_check_status": "confirmed", "reviewer": "owner", "notes": "ok"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["data"]["fact_check_status"], "confirmed")

    def test_model_options_generation_scene(self) -> None:
        resp = client.get("/api/v1/model-options?scene=generation")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()["data"]
        self.assertEqual(data["scene"], "generation")
        self.assertIn("default_model", data)
        self.assertGreaterEqual(len(data["options"]), 1)
        for item in data["options"]:
            self.assertIn("model_name", item)
            self.assertIn("enabled", item)
            self.assertIn("provider", item)

    def test_generation_job_model_name_must_be_in_options(self) -> None:
        resp = client.post(
            "/api/v1/generation-jobs",
            json={
                "job_type": "script_generation",
                "topic": "invalid-model-test",
                "model_name": "not-in-options",
            },
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()["code"], "INVALID_MODEL_NAME")

    def test_template_ai_generate_requires_name_or_goal(self) -> None:
        resp = client.post(
            "/api/v1/templates/ai-generate",
            json={
                "template_type": "script",
                "template_category": "narrative_frame",
            },
        )
        self.assertEqual(resp.status_code, 422)

    def test_reports_template_performance_pagination(self) -> None:
        t1 = client.post(
            "/api/v1/templates",
            json={
                "template_type": "script",
                "template_category": "narrative_frame",
                "name": "template-A",
                "structure_json": {"opening": "a", "body": ["b"], "ending": "c"},
            },
        ).json()["data"]["template_id"]

        t2 = client.post(
            "/api/v1/templates",
            json={
                "template_type": "script",
                "template_category": "narrative_frame",
                "name": "template-B",
                "structure_json": {"opening": "a", "body": ["b"], "ending": "c"},
            },
        ).json()["data"]["template_id"]

        client.post("/api/v1/generation-jobs", json={"job_type": "script_generation", "topic": "a1", "selected_template_id": t1})
        client.post("/api/v1/generation-jobs", json={"job_type": "script_generation", "topic": "a2", "selected_template_id": t1})
        client.post("/api/v1/generation-jobs", json={"job_type": "script_generation", "topic": "b1", "selected_template_id": t2})

        resp = client.get(
            "/api/v1/reports/templates/performance?page=1&page_size=1&sort_by=usage_count&sort_order=desc"
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()["data"]
        self.assertEqual(data["page"], 1)
        self.assertEqual(data["page_size"], 1)
        self.assertGreaterEqual(data["total"], 2)
        self.assertEqual(len(data["items"]), 1)
        self.assertEqual(data["items"][0]["template_id"], t1)

    def test_reports_posts_export_sort_by_likes(self) -> None:
        now = datetime.now(UTC)
        with SessionLocal() as db:
            db.add_all(
                [
                    PostORM(
                        post_id=new_id("post"),
                        platform_code="zhihu",
                        title="low likes",
                        content_text="c1",
                        source_url="https://example.com/1",
                        like_count=10,
                        comment_count=1,
                        favorite_count=1,
                        share_count=0,
                        view_count=100,
                        is_historical_hot=False,
                        source_type="manual_import",
                        topic_keywords=[],
                        status="normalized",
                        created_at=now,
                        updated_at=now,
                    ),
                    PostORM(
                        post_id=new_id("post"),
                        platform_code="zhihu",
                        title="high likes",
                        content_text="c2",
                        source_url="https://example.com/2",
                        like_count=200,
                        comment_count=5,
                        favorite_count=3,
                        share_count=2,
                        view_count=500,
                        is_historical_hot=False,
                        source_type="manual_import",
                        topic_keywords=[],
                        status="normalized",
                        created_at=now,
                        updated_at=now,
                    ),
                ]
            )
            db.commit()

        resp = client.post("/api/v1/reports/posts/export?format=csv&sort_by=like_count&sort_order=desc")
        self.assertEqual(resp.status_code, 200)
        csv_data = resp.json()["data"]["data"]
        first_data_row = csv_data.splitlines()[1]
        self.assertIn("high likes", first_data_row)

    def test_generation_reference_posts_include_latest_analysis(self) -> None:
        now = datetime.now(UTC)
        post_id = new_id("post")
        with SessionLocal() as db:
            db.add(
                PostORM(
                    post_id=post_id,
                    platform_code="zhihu",
                    title="sample title",
                    content_text="sample content",
                    source_url="https://example.com/post",
                    source_type="manual_import",
                    topic_keywords=[],
                    status="normalized",
                    created_at=now,
                    updated_at=now,
                )
            )
            db.add(
                AnalysisResultORM(
                    analysis_id=new_id("an"),
                    post_id=post_id,
                    analysis_version="v1",
                    prompt_version="analysis.zhihu.history.v1",
                    model_name="test-model",
                    summary="old summary",
                    main_topic="old topic",
                    hook_text="old hook",
                    narrative_structure={"opening": "old", "body": ["a"], "ending": "b"},
                    emotional_driver="old emotion",
                    fact_risk_level="low",
                    fact_risk_items=[],
                    fact_check_status="pending",
                    created_at=now,
                )
            )
            db.add(
                AnalysisResultORM(
                    analysis_id=new_id("an"),
                    post_id=post_id,
                    analysis_version="v1",
                    prompt_version="analysis.zhihu.history.v1",
                    model_name="test-model",
                    summary="new summary",
                    main_topic="new topic",
                    hook_text="new hook",
                    narrative_structure={"opening": "new", "body": ["x"], "ending": "y"},
                    emotional_driver="new emotion",
                    fact_risk_level="low",
                    fact_risk_items=[],
                    fact_check_status="pending",
                    created_at=now + timedelta(milliseconds=1),
                )
            )
            db.commit()
            rows = generation_service._build_reference_posts_with_analysis(db, [post_id])

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["post_id"], post_id)
        self.assertIn("analysis", rows[0])
        self.assertEqual(rows[0]["analysis"]["main_topic"], "new topic")
        self.assertEqual(rows[0]["analysis"]["hook_text"], "new hook")

    def test_template_ai_reference_context_contains_analysis_fields(self) -> None:
        now = datetime.now(UTC)
        post_id = new_id("post")
        with SessionLocal() as db:
            db.add(
                PostORM(
                    post_id=post_id,
                    platform_code="zhihu",
                    title="context title",
                    content_text="context content",
                    source_url="https://example.com/context",
                    source_type="manual_import",
                    topic_keywords=[],
                    status="normalized",
                    created_at=now,
                    updated_at=now,
                )
            )
            db.add(
                AnalysisResultORM(
                    analysis_id=new_id("an"),
                    post_id=post_id,
                    analysis_version="v1",
                    prompt_version="analysis.zhihu.history.v1",
                    model_name="test-model",
                    summary="summary text",
                    main_topic="topic text",
                    hook_text="hook text",
                    narrative_structure={"opening": "o", "body": ["b1"], "ending": "e"},
                    emotional_driver="emotion text",
                    fact_risk_level="low",
                    fact_risk_items=[],
                    fact_check_status="pending",
                    created_at=now,
                )
            )
            db.commit()
            context = template_service._build_reference_context(db, [post_id])

        self.assertIn("样本ID", context)
        self.assertIn("样本标题", context)
        self.assertIn("主题", context)
        self.assertIn("钩子", context)
        self.assertIn("情绪驱动", context)


if __name__ == "__main__":
    unittest.main()

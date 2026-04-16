"""
接口完整性测试 - 根据 07-api-spec.md 验证所有接口实现
"""
import unittest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestApiCompleteness(unittest.TestCase):
    """测试 API 文档中定义的所有接口是否已实现"""

    def test_01_health_check(self):
        """GET /health - 健康检查"""
        resp = client.get("/api/v1/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["code"], "OK")

    def test_02_get_platforms(self):
        """GET /platforms - 获取平台列表"""
        resp = client.get("/api/v1/platforms")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()["data"]
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["code"], "zhihu")
        self.assertTrue(data[0]["mvp_enabled"])

    def test_03_create_collector_task(self):
        """POST /collector-tasks - 创建采集任务"""
        resp = client.post(
            "/api/v1/collector-tasks",
            json={
                "platform_code": "zhihu",
                "task_type": "historical_hot",
                "query_keyword": "秦始皇",
                "limit": 3,
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("task_id", resp.json()["data"])
        self.assertEqual(resp.json()["data"]["status"], "pending")

    def test_04_run_collector_task(self):
        """POST /collector-tasks/{task_id}/run - 执行采集任务"""
        # 先创建任务
        create_resp = client.post(
            "/api/v1/collector-tasks",
            json={
                "platform_code": "zhihu",
                "task_type": "historical_hot",
                "query_keyword": "历史人物",
                "limit": 2,
            },
        )
        task_id = create_resp.json()["data"]["task_id"]
        
        # 执行任务
        resp = client.post(f"/api/v1/collector-tasks/{task_id}/run")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["data"]["status"], "succeeded")
        self.assertGreater(resp.json()["data"]["success_count"], 0)

    def test_05_run_nonexistent_task(self):
        """POST /collector-tasks/{task_id}/run - 不存在的任务应返回 404"""
        resp = client.post("/api/v1/collector-tasks/nonexistent/run")
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.json()["code"], "NOT_FOUND")

    def test_06_list_posts(self):
        """GET /posts - 获取样本列表"""
        # 先采集一些数据
        create_resp = client.post(
            "/api/v1/collector-tasks",
            json={
                "platform_code": "zhihu",
                "task_type": "historical_hot",
                "query_keyword": "测试",
                "limit": 2,
            },
        )
        task_id = create_resp.json()["data"]["task_id"]
        client.post(f"/api/v1/collector-tasks/{task_id}/run")
        
        # 获取列表
        resp = client.get("/api/v1/posts")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("items", resp.json()["data"])

    def test_07_create_analysis(self):
        """POST /analysis-results - 创建分析结果"""
        # 先创建并采集任务
        create_resp = client.post(
            "/api/v1/collector-tasks",
            json={
                "platform_code": "zhihu",
                "query_keyword": "分析测试",
                "limit": 1,
            },
        )
        task_id = create_resp.json()["data"]["task_id"]
        client.post(f"/api/v1/collector-tasks/{task_id}/run")
        
        # 获取 post_id
        posts_resp = client.get("/api/v1/posts")
        posts = posts_resp.json()["data"]["items"]
        if not posts:
            self.skipTest("No posts available for analysis")
        
        post_id = posts[0]["post_id"]
        
        # 创建分析
        resp = client.post(
            "/api/v1/analysis-results",
            json={
                "post_id": post_id,
                "analysis_version": "v1",
                "prompt_version": "analysis.zhihu.history.v1",
                "model_name": "rule-based-mvp",
            },
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()["data"]
        self.assertEqual(data["post_id"], post_id)
        self.assertIn("analysis_id", data)
        self.assertIn("summary", data)
        self.assertIn("hook_text", data)

    def test_08_analysis_nonexistent_post(self):
        """POST /analysis-results - 不存在的 post 应返回 404"""
        resp = client.post(
            "/api/v1/analysis-results",
            json={"post_id": "nonexistent"},
        )
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.json()["code"], "NOT_FOUND")

    def test_09_create_template(self):
        """POST /templates - 创建模板"""
        resp = client.post(
            "/api/v1/templates",
            json={
                "template_type": "script",
                "template_category": "narrative_frame",
                "name": "历史反转模板",
                "structure_json": {
                    "opening": "反常识问题",
                    "body": ["背景", "冲突", "反转"],
                    "ending": "互动引导",
                },
                "source_post_ids": ["post_001"],
            },
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()["data"]
        self.assertIn("template_id", data)
        self.assertEqual(data["name"], "历史反转模板")
        self.assertEqual(data["status"], "draft")

    def test_10_create_generation_job(self):
        """POST /generation-jobs - 创建生成任务"""
        resp = client.post(
            "/api/v1/generation-jobs",
            json={
                "job_type": "script_generation",
                "topic": "如果秦始皇多活十年",
                "brief": "60秒口播稿",
                "prompt_version": "generation.zhihu_to_video.v1",
                "model_name": "rule-based-mvp",
            },
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()["data"]
        self.assertIn("job_id", data)
        self.assertEqual(data["status"], "reviewing")
        self.assertIn("generated_content", data)
        self.assertIn("title", data["generated_content"])
        self.assertIn("script_text", data["generated_content"])

    def test_11_response_structure(self):
        """验证所有响应符合统一结构: code, message, data, request_id"""
        resp = client.get("/api/v1/platforms")
        data = resp.json()
        self.assertIn("code", data)
        self.assertIn("message", data)
        self.assertIn("data", data)
        self.assertIn("request_id", data)
        self.assertEqual(data["code"], "OK")
        self.assertEqual(data["message"], "success")

    def test_12_generated_content_fields(self):
        """验证生成内容包含文档要求的字段"""
        resp = client.post(
            "/api/v1/generation-jobs",
            json={
                "job_type": "script_generation",
                "topic": "历史话题测试",
                "brief": "测试",
            },
        )
        content = resp.json()["data"]["generated_content"]
        
        # 验证必需字段
        required_fields = [
            "content_id", "title", "script_text", "storyboard_json",
            "cover_text", "publish_caption", "hashtags", "source_trace",
            "status", "fact_check_status", "current_version_no"
        ]
        for field in required_fields:
            self.assertIn(field, content, f"Missing field: {field}")


class TestAllEndpoints(unittest.TestCase):
    """测试所有 19 个文档定义的接口是否已实现并返回 200"""

    def test_13_get_collector_tasks_list(self):
        """GET /collector-tasks - 获取任务列表"""
        resp = client.get("/api/v1/collector-tasks")
        self.assertEqual(resp.status_code, 200)

    def test_14_get_collector_task_detail(self):
        """GET /collector-tasks/{task_id} - 获取任务详情"""
        create_resp = client.post(
            "/api/v1/collector-tasks",
            json={"platform_code": "zhihu", "query_keyword": "test", "limit": 1},
        )
        task_id = create_resp.json()["data"]["task_id"]
        resp = client.get(f"/api/v1/collector-tasks/{task_id}")
        self.assertEqual(resp.status_code, 200)

    def test_15_get_post_detail(self):
        """GET /posts/{post_id} - 获取样本详情"""
        create_resp = client.post(
            "/api/v1/collector-tasks",
            json={"platform_code": "zhihu", "query_keyword": "test", "limit": 1},
        )
        task_id = create_resp.json()["data"]["task_id"]
        client.post(f"/api/v1/collector-tasks/{task_id}/run")
        posts_resp = client.get("/api/v1/posts")
        post_id = posts_resp.json()["data"]["items"][0]["post_id"]
        resp = client.get(f"/api/v1/posts/{post_id}")
        self.assertEqual(resp.status_code, 200)

    def test_16_manual_import_post(self):
        """POST /posts/manual-import - 手动录入样本"""
        resp = client.post(
            "/api/v1/posts/manual-import",
            json={
                "platform_code": "zhihu",
                "title": "测试标题",
                "content_text": "测试内容",
            },
        )
        self.assertEqual(resp.status_code, 200)

    def test_17_update_post(self):
        """PATCH /posts/{post_id} - 更新样本标签"""
        create_resp = client.post(
            "/api/v1/collector-tasks",
            json={"platform_code": "zhihu", "query_keyword": "test", "limit": 1},
        )
        task_id = create_resp.json()["data"]["task_id"]
        client.post(f"/api/v1/collector-tasks/{task_id}/run")
        posts_resp = client.get("/api/v1/posts")
        post_id = posts_resp.json()["data"]["items"][0]["post_id"]
        resp = client.patch(
            f"/api/v1/posts/{post_id}",
            json={"topic_keywords": ["测试"]},
        )
        self.assertEqual(resp.status_code, 200)

    def test_18_get_analysis_result(self):
        """GET /analysis-results/{analysis_id} - 获取分析结果"""
        create_resp = client.post(
            "/api/v1/collector-tasks",
            json={"platform_code": "zhihu", "query_keyword": "test", "limit": 1},
        )
        task_id = create_resp.json()["data"]["task_id"]
        client.post(f"/api/v1/collector-tasks/{task_id}/run")
        posts_resp = client.get("/api/v1/posts")
        post_id = posts_resp.json()["data"]["items"][0]["post_id"]
        analysis_resp = client.post(
            "/api/v1/analysis-results",
            json={"post_id": post_id},
        )
        analysis_id = analysis_resp.json()["data"]["analysis_id"]
        resp = client.get(f"/api/v1/analysis-results/{analysis_id}")
        self.assertEqual(resp.status_code, 200)

    def test_19_fact_check_analysis(self):
        """POST /analysis-results/{analysis_id}/fact-check - 事实确认"""
        create_resp = client.post(
            "/api/v1/collector-tasks",
            json={"platform_code": "zhihu", "query_keyword": "test", "limit": 1},
        )
        task_id = create_resp.json()["data"]["task_id"]
        client.post(f"/api/v1/collector-tasks/{task_id}/run")
        posts_resp = client.get("/api/v1/posts")
        post_id = posts_resp.json()["data"]["items"][0]["post_id"]
        analysis_resp = client.post(
            "/api/v1/analysis-results",
            json={"post_id": post_id},
        )
        analysis_id = analysis_resp.json()["data"]["analysis_id"]
        resp = client.post(
            f"/api/v1/analysis-results/{analysis_id}/fact-check",
            json={
                "fact_check_status": "confirmed",
                "reviewer": "owner",
            },
        )
        self.assertEqual(resp.status_code, 200)

    def test_20_get_templates_list(self):
        """GET /templates - 获取模板列表"""
        resp = client.get("/api/v1/templates")
        self.assertEqual(resp.status_code, 200)

    def test_21_get_template_detail(self):
        """GET /templates/{template_id} - 获取模板详情"""
        create_resp = client.post(
            "/api/v1/templates",
            json={
                "template_type": "script",
                "template_category": "narrative_frame",
                "name": "测试模板",
                "structure_json": {"opening": "test", "body": ["test"], "ending": "test"},
            },
        )
        template_id = create_resp.json()["data"]["template_id"]
        resp = client.get(f"/api/v1/templates/{template_id}")
        self.assertEqual(resp.status_code, 200)

    def test_22_update_template_status(self):
        """POST /templates/{template_id}/status - 启用/停用模板"""
        create_resp = client.post(
            "/api/v1/templates",
            json={
                "template_type": "script",
                "template_category": "narrative_frame",
                "name": "测试模板",
                "structure_json": {"opening": "test", "body": ["test"], "ending": "test"},
            },
        )
        template_id = create_resp.json()["data"]["template_id"]
        resp = client.post(
            f"/api/v1/templates/{template_id}/status",
            json={"status": "active"},
        )
        self.assertEqual(resp.status_code, 200)

    def test_23_get_generation_job(self):
        """GET /generation-jobs/{job_id} - 获取生成任务详情"""
        create_resp = client.post(
            "/api/v1/generation-jobs",
            json={
                "job_type": "script_generation",
                "topic": "测试主题",
            },
        )
        job_id = create_resp.json()["data"]["job_id"]
        resp = client.get(f"/api/v1/generation-jobs/{job_id}")
        self.assertEqual(resp.status_code, 200)

    def test_24_get_generated_contents_list(self):
        """GET /generated-contents - 获取生成结果列表"""
        resp = client.get("/api/v1/generated-contents")
        self.assertEqual(resp.status_code, 200)

    def test_25_get_generated_content_detail(self):
        """GET /generated-contents/{content_id} - 获取生成结果详情"""
        create_resp = client.post(
            "/api/v1/generation-jobs",
            json={
                "job_type": "script_generation",
                "topic": "测试主题",
            },
        )
        content_id = create_resp.json()["data"]["generated_content"]["content_id"]
        resp = client.get(f"/api/v1/generated-contents/{content_id}")
        self.assertEqual(resp.status_code, 200)

    def test_26_review_compare(self):
        """GET /generated-contents/{content_id}/review-compare - 审核对比"""
        create_resp = client.post(
            "/api/v1/generation-jobs",
            json={
                "job_type": "script_generation",
                "topic": "测试主题",
            },
        )
        content_id = create_resp.json()["data"]["generated_content"]["content_id"]
        resp = client.get(f"/api/v1/generated-contents/{content_id}/review-compare")
        self.assertEqual(resp.status_code, 200)

    def test_27_create_version(self):
        """POST /generated-contents/{content_id}/versions - 保存编辑版本"""
        create_resp = client.post(
            "/api/v1/generation-jobs",
            json={
                "job_type": "script_generation",
                "topic": "测试主题",
            },
        )
        content_id = create_resp.json()["data"]["generated_content"]["content_id"]
        resp = client.post(
            f"/api/v1/generated-contents/{content_id}/versions",
            json={
                "editor": "owner",
                "script_text": "修改后的脚本",
            },
        )
        self.assertEqual(resp.status_code, 200)

    def test_28_submit_review(self):
        """POST /reviews - 提交审核"""
        create_resp = client.post(
            "/api/v1/generation-jobs",
            json={
                "job_type": "script_generation",
                "topic": "测试主题",
            },
        )
        content_id = create_resp.json()["data"]["generated_content"]["content_id"]
        resp = client.post(
            "/api/v1/reviews",
            json={
                "generated_content_id": content_id,
                "reviewer": "owner",
                "decision": "approve",
            },
        )
        self.assertEqual(resp.status_code, 200)

    def test_29_create_publish_record(self):
        """POST /publish-records - 创建发布记录"""
        create_resp = client.post(
            "/api/v1/generation-jobs",
            json={
                "job_type": "script_generation",
                "topic": "测试主题",
            },
        )
        content_id = create_resp.json()["data"]["generated_content"]["content_id"]
        resp = client.post(
            "/api/v1/publish-records",
            json={
                "generated_content_id": content_id,
                "platform_code": "bilibili",
                "publish_channel": "manual",
                "operator": "owner",
            },
        )
        self.assertEqual(resp.status_code, 200)

    def test_30_create_snapshot(self):
        """POST /publish-records/{id}/snapshots - 回填效果快照"""
        create_resp = client.post(
            "/api/v1/generation-jobs",
            json={
                "job_type": "script_generation",
                "topic": "测试主题",
            },
        )
        content_id = create_resp.json()["data"]["generated_content"]["content_id"]
        publish_resp = client.post(
            "/api/v1/publish-records",
            json={
                "generated_content_id": content_id,
                "platform_code": "bilibili",
                "publish_channel": "manual",
                "operator": "owner",
            },
        )
        publish_id = publish_resp.json()["data"]["id"]
        resp = client.post(
            f"/api/v1/publish-records/{publish_id}/snapshots",
            json={
                "like_count": 100,
                "captured_at": "2026-04-11T10:00:00+08:00",
            },
        )
        self.assertEqual(resp.status_code, 200)

    def test_31_get_publish_records(self):
        """GET /publish-records - 获取发布记录"""
        resp = client.get("/api/v1/publish-records")
        self.assertEqual(resp.status_code, 200)


if __name__ == "__main__":
    unittest.main()

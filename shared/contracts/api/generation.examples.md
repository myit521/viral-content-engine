# Generation Examples

## 创建生成任务

`POST /api/v1/generation-jobs`

请求体：

```json
{
  "job_type": "script_generation",
  "topic": "如果秦始皇多活十年",
  "brief": "生成一版 60 秒历史口播脚本",
  "selected_template_id": "tpl_xxx",
  "reference_post_ids": ["post_001", "post_002"],
  "prompt_version": "generation.zhihu_to_video.v1",
  "model_name": "rule-based-mvp"
}
```

响应体：

```json
{
  "code": "OK",
  "message": "success",
  "data": {
    "id": "job_xxx",
    "job_id": "job_xxx",
    "status": "completed",
    "generated_content": {
      "id": "gc_xxx",
      "content_id": "gc_xxx",
      "title": "如果秦始皇多活十年，历史会被改写吗？",
      "script_text": "很多人以为秦朝的转折发生在秦始皇死后，但真正的问题是……",
      "storyboard_json": {
        "scenes": [
          {
            "index": 1,
            "shot": "人物特写",
            "voiceover": "开头钩子"
          }
        ]
      },
      "cover_text": "秦始皇多活十年会怎样",
      "publish_caption": "一个假设问题，背后其实藏着秦朝命运的真正拐点。",
      "hashtags": ["#历史", "#秦始皇"],
      "source_trace": {
        "template_id": "tpl_xxx",
        "reference_post_ids": ["post_001", "post_002"]
      },
      "status": "draft",
      "fact_check_status": "pending",
      "current_version_no": 1,
      "created_at": "2026-04-13T10:20:30Z",
      "updated_at": "2026-04-13T10:20:30Z"
    }
  },
  "request_id": "req_xxx"
}
```


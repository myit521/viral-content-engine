# 接口文档

## 1. 文档目标

本文档定义第一阶段 MVP 的后端接口，服务对象为：

1. `Qoder Console`
2. `Codex Backend`
3. 后续测试脚本和调试工具

第一阶段范围严格限定为：

1. 历史类内容赛道
2. 知乎单平台采集
3. 人工审核、人工事实确认、人工发布回填

## 2. 设计原则

1. 所有接口以 REST 风格为主。
2. 异步型操作统一返回 `task_id`。
3. 所有关键对象返回 `status`、`created_at`、`updated_at`。
4. 所有分析和生成相关接口返回 `prompt_version`、`model_name`。
5. 审核相关接口必须返回对比视图所需字段。

## 3. 通用约定

### 3.1 Base URL

`/api/v1`

### 3.2 统一响应结构

成功响应：

```json
{
  "code": "OK",
  "message": "success",
  "data": {},
  "request_id": "req_20260410_001"
}
```

分页响应：

```json
{
  "code": "OK",
  "message": "success",
  "data": {
    "items": [],
    "page": 1,
    "page_size": 20,
    "total": 0
  },
  "request_id": "req_20260410_001"
}
```

失败响应：

```json
{
  "code": "VALIDATION_ERROR",
  "message": "topic is required",
  "data": null,
  "request_id": "req_20260410_001"
}
```

### 3.3 统一状态值

1. `collection_task.status`: `pending` / `running` / `succeeded` / `partial_failed` / `failed` / `cancelled`
2. `post.status`: `raw` / `normalized` / `analyzed` / `templated` / `archived`
3. `template.status`: `draft` / `active` / `disabled` / `archived`
4. `generation_job.status`: `pending` / `retrieving` / `generating` / `reviewing` / `completed` / `failed`
5. `generated_content.status`: `draft` / `in_review` / `approved` / `rejected` / `published`
6. `fact_check_status`: `pending` / `confirmed` / `needs_evidence` / `rejected`

### 3.4 错误码清单（第一阶段）

| 错误码 | HTTP 状态码 | 说明 |
| --- | --- | --- |
| `OK` | 200 | 成功 |
| `VALIDATION_ERROR` | 400 | 请求参数校验失败 |
| `NOT_FOUND` | 404 | 资源不存在 |
| `RESOURCE_IN_USE` | 409 | 资源仍被当前流程占用，暂不可删除 |
| `TASK_FAILED` | 500 | 异步任务执行失败 |
| `INTERNAL_ERROR` | 500 | 服务器内部错误 |
| `AI_SERVICE_ERROR` | 503 | AI 服务调用失败 |

### 3.5 删除与归档约定

1. 第一阶段删除类接口统一采用“逻辑删除”，不做数据库物理删除。
2. 控制台按钮和提示文案可使用“删除”，后端落库语义统一为 `status = archived`，以兼顾用户理解、审计留痕和后续恢复空间。
3. 列表接口默认不返回 `archived` 数据；控制台如需查看历史归档数据，可显式传 `include_archived=true`。
4. 详情接口允许查询已归档资源，用于查看来源、引用关系、审核记录和发布留痕。
5. 删除类接口应保持幂等：资源已归档时再次调用，仍返回成功态和当前状态。
6. 若资源仍被当前流程占用，返回 `RESOURCE_IN_USE`，并在 `message` 与 `data` 中提供依赖摘要，便于前端直接展示阻塞原因。

## 4. 平台与配置域

### 4.1 获取平台列表

`GET /platforms`

用途：

1. 控制台展示当前启用的平台。
2. 第一阶段固定只返回知乎。

响应示例：

```json
{
  "code": "OK",
  "message": "success",
  "data": [
    {
      "id": 1,
      "code": "zhihu",
      "name": "知乎",
      "enabled": true,
      "mvp_enabled": true
    }
  ],
  "request_id": "req_20260410_001"
}
```

## 5. 采集任务域

### 5.1 创建采集任务

`POST /collector-tasks`

请求体：

```json
{
  "platform_code": "zhihu",
  "task_type": "historical_hot",
  "query_keyword": "历史人物",
  "date_range_start": "2024-01-01",
  "date_range_end": "2026-04-10",
  "limit": 100
}
```

响应体：

```json
{
  "code": "OK",
  "message": "success",
  "data": {
    "task_id": "ct_001",
    "status": "pending"
  },
  "request_id": "req_20260410_001"
}
```

### 5.2 获取采集任务列表

`GET /collector-tasks?page=1&page_size=20&status=running`

### 5.3 获取采集任务详情

`GET /collector-tasks/{task_id}`

详情字段建议：

1. 任务参数
2. 当前状态
3. 成功采集数
4. 失败数
5. 错误摘要
6. 原始文件目录

### 5.4 手动执行采集任务

`POST /collector-tasks/{task_id}/run`

说明：

1. 第一阶段以手动触发为主。
2. 不要求建设复杂调度中心。

## 6. 内容样本域

### 6.1 获取样本列表

`GET /posts?page=1&page_size=20&source_type=collector&status=normalized&keyword=秦始皇`

支持筛选：

1. 平台
2. 主题关键词
3. 状态
4. 是否历史高赞
5. 是否手动录入
6. `include_archived`，默认 `false`

### 6.2 获取样本详情

`GET /posts/{post_id}`

详情返回建议：

1. 基础字段
2. 作者信息
3. 原始来源链接
4. 互动指标
5. 文本分段
6. 最近一次分析摘要

### 6.3 手动录入样本

`POST /posts/manual-import`

请求体：

```json
{
  "platform_code": "zhihu",
  "source_url": "https://www.zhihu.com/question/123456",
  "title": "如果秦始皇多活十年，会发生什么？",
  "content_text": "这里是手动录入的正文",
  "author_name": "匿名用户",
  "published_at": "2024-06-18T12:00:00+08:00",
  "topic_keywords": ["秦始皇", "历史假设"],
  "note": "来自手工整理的高赞回答"
}
```

用途：

1. 当采集器采集不到内容时补录样本。
2. 引入历史上已知爆款作为研究样本。

### 6.4 更新样本标签

`PATCH /posts/{post_id}`

允许人工更新：

1. `topic_keywords`
2. `is_historical_hot`
3. `note`

### 6.5 删除样本（逻辑删除）

`DELETE /posts/{post_id}`

说明：

1. 接口对控制台语义为“删除样本”，后端落库动作为 `status = archived`。
2. 已归档样本默认不出现在 `GET /posts` 列表中，但仍可通过 `GET /posts/{post_id}` 查看详情。
3. 已产生分析结果、模板引用或发布来源追踪的样本允许归档，但历史关联关系必须保留，不做级联物理删除。

响应体：

```json
{
  "code": "OK",
  "message": "success",
  "data": {
    "post_id": "post_001",
    "status": "archived"
  },
  "request_id": "req_20260410_001"
}
```

## 7. AI 分析与事实确认域

### 7.1 发起样本分析

`POST /analysis-results`

请求体：

```json
{
  "post_id": "post_001",
  "analysis_version": "v1",
  "prompt_version": "analysis.zhihu.history.v1",
  "model_name": "gpt-4.1-mini"
}
```

### 7.2 获取分析结果详情

`GET /analysis-results/{analysis_id}`

返回重点：

1. `summary`
2. `main_topic`
3. `content_angle`
4. `hook_text`
5. `narrative_structure`
6. `emotional_driver`
7. `fact_risk_level`
8. `fact_risk_items`
9. `prompt_version`
10. `model_name`

### 7.3 人工确认事实风险

`POST /analysis-results/{analysis_id}/fact-check`

请求体：

```json
{
  "fact_check_status": "confirmed",
  "reviewer": "owner",
  "notes": "已对照《史记》与百科资料确认",
  "risk_items": [
    {
      "claim": "秦始皇焚书坑儒影响范围",
      "decision": "confirmed",
      "evidence_note": "需补充史料出处到脚本备注"
    }
  ]
}
```

说明：

1. 这是第一阶段必须具备的人工闭环。
2. 未人工确认的高风险内容不得进入可发布状态。

## 8. 模板中心域

### 8.1 获取模板列表

`GET /templates?page=1&page_size=20&template_category=opening_hook&status=active`

模板分类：

1. `title_hook`
2. `opening_hook`
3. `narrative_frame`
4. `ending_cta`
5. `full_script`

补充筛选：

1. `status`
2. `include_archived`，默认 `false`

### 8.2 创建模板

`POST /templates`

请求体：

```json
{
  "template_type": "script",
  "template_category": "narrative_frame",
  "name": "历史反转三段式",
  "applicable_platform": "zhihu_to_video",
  "applicable_topic": "history",
  "applicable_scene": "人物争议",
  "structure_json": {
    "opening": "反常识问题",
    "body": ["史料背景", "争议转折", "结论升华"],
    "ending": "评论区互动"
  },
  "source_post_ids": ["post_001", "post_002"]
}
```

### 8.2a AI 生成模板

`POST /templates/ai-generate`

请求体：

```json
{
  "name": "历史人物反转模板",
  "generation_goal": "生成一个适合历史反转类视频的叙事框架模板",
  "template_type": "script",
  "template_category": "narrative_frame",
  "applicable_platform": "zhihu_to_video",
  "applicable_topic": "history",
  "reference_post_ids": ["post_001", "post_003"],
  "model_name": "deepseek-chat"
}
```

说明：

1. `reference_post_ids`：可选。传入参考样本 ID，后端自动查询样本内容及分析特征注入 AI Prompt，提升模板生成质量。
2. 不传时 AI 仅基于用户输入的目标和要求生成模板。

### 8.2b 自动归纳模板

`POST /templates/auto-summarize`

请求体：

```json
{
  "analysis_ids": ["an_001", "an_002", "an_003", "an_005"],
  "template_type": "script",
  "template_category": "narrative_frame",
  "applicable_platform": "zhihu_to_video",
  "applicable_topic": "history",
  "min_cluster_size": 2
}
```

说明：

1. 后端按 `main_topic + emotional_driver` 对分析结果做聚类。
2. 每个满足 `min_cluster_size` 的类簿自动生成一个模板，状态为 `draft`。
3. 返回创建的模板列表和聚类诊断信息。
```

### 8.3 获取模板详情

`GET /templates/{template_id}`

详情必须返回：

1. 模板结构
2. 示例样本
3. 模板评分
4. 适用场景
5. 状态

### 8.4 启用或停用模板

`POST /templates/{template_id}/status`

请求体：

```json
{
  "status": "active"
}
```

### 8.5 删除模板（逻辑删除）

`DELETE /templates/{template_id}`

说明：

1. 接口对控制台语义为“删除模板”，后端落库动作为 `status = archived`。
2. 已被历史生成结果引用的模板允许归档，但归档后不可再用于新的生成任务。
3. 若模板正被 `pending` / `retrieving` / `generating` 状态的 `generation_jobs` 引用，则返回 `RESOURCE_IN_USE`。

成功响应：

```json
{
  "code": "OK",
  "message": "success",
  "data": {
    "template_id": "tpl_001",
    "status": "archived"
  },
  "request_id": "req_20260410_001"
}
```

占用冲突响应示例：

```json
{
  "code": "RESOURCE_IN_USE",
  "message": "template is referenced by running generation jobs",
  "data": {
    "template_id": "tpl_001",
    "blocking_generation_job_ids": ["job_101", "job_108"]
  },
  "request_id": "req_20260410_001"
}
```

## 9. 内容生成域

### 9.1 创建生成任务

`POST /generation-jobs`

请求体：

```json
{
  "job_type": "script_generation",
  "topic": "如果秦始皇多活十年",
  "brief": "做成 60 秒短视频口播稿",
  "selected_template_id": "tpl_001",
  "reference_post_ids": ["post_001", "post_008"],
  "prompt_version": "generation.zhihu_to_video.v1",
  "model_name": "gpt-4.1"
}
```

说明：

1. `reference_post_ids`：可选。传入已分析样本的 post_id 列表，后端自动查询对应样本内容及其最新分析特征（main_topic、hook_text、narrative_structure、emotional_driver）注入生成 Prompt。
2. `selected_template_id`：可选。前端通过模板选择器传入，后端读取模板的 structure_json 注入生成。
3. 不传以上参数时生成仍可独立工作。
```

### 9.2 获取生成任务详情

`GET /generation-jobs/{job_id}`

### 9.3 获取生成结果列表

`GET /generated-contents?job_id=job_001`

### 9.4 获取生成结果详情

`GET /generated-contents/{content_id}`

详情必须返回：

1. `title`
2. `script_text`
3. `storyboard_json`
4. `cover_text`
5. `publish_caption`
6. `hashtags`
7. `source_trace`
8. `fact_check_status`
9. `current_version_no`

### 9.5 第一阶段不提供删除接口

1. `generation_jobs` 不提供删除接口，避免破坏任务追踪链路。
2. `generated_contents` 不提供删除接口，避免破坏版本、审核和发布回填留痕。
3. 控制台第一阶段不应为上述资源提供“删除”入口，如需弱化展示，可通过状态筛选或列表分组处理。

## 10. 审核与版本域

### 10.1 获取审核对比视图

`GET /generated-contents/{content_id}/review-compare`

返回示例：

```json
{
  "code": "OK",
  "message": "success",
  "data": {
    "generated_content_id": "gc_001",
    "source_summary": [
      {
        "post_id": "post_001",
        "title": "原始高赞回答标题",
        "hook_text": "你以为秦始皇暴政，其实不止如此"
      }
    ],
    "initial_draft": {
      "version_no": 1,
      "title": "AI 初稿标题",
      "script_text": "AI 初稿正文"
    },
    "current_edit": {
      "version_no": 2,
      "title": "人工编辑标题",
      "script_text": "人工修改后的正文"
    },
    "final_draft": null
  },
  "request_id": "req_20260410_001"
}
```

用途：

1. 支撑控制台对比视图。
2. 让审核人看到来源、初稿和编辑稿差异。

### 10.2 保存编辑版本

`POST /generated-contents/{content_id}/versions`

请求体：

```json
{
  "editor": "owner",
  "title": "人工改写后的标题",
  "script_text": "人工改写后的脚本",
  "edit_note": "压缩开头，补充史料限定语"
}
```

### 10.3 提交审核

`POST /reviews`

请求体：

```json
{
  "generated_content_id": "gc_001",
  "reviewer": "owner",
  "decision": "approve",
  "comment": "内容可发布，但封面文案需再短一些",
  "fact_check_status": "confirmed"
}
```

## 11. 发布回填域

### 11.1 创建发布记录

`POST /publish-records`

请求体：

```json
{
  "generated_content_id": "gc_001",
  "platform_code": "bilibili",
  "publish_channel": "manual",
  "published_url": "https://www.bilibili.com/video/BVxxxx",
  "published_at": "2026-04-10T20:30:00+08:00",
  "operator": "owner",
  "notes": "先手动试投放"
}
```

说明：

1. 第一阶段允许手动发布到知乎外的平台。
2. 但发布动作本身不由系统自动执行。

### 11.2 回填效果快照

`POST /publish-records/{publish_record_id}/snapshots`

请求体：

```json
{
  "like_count": 1200,
  "comment_count": 85,
  "favorite_count": 340,
  "share_count": 60,
  "view_count": 18000,
  "retention_rate": 0.42,
  "captured_at": "2026-04-11T10:00:00+08:00"
}
```

### 11.3 获取发布效果详情

`GET /publish-records/{publish_record_id}`

### 11.4 删除发布记录（逻辑删除）

`DELETE /publish-records/{publish_record_id}`

说明：

1. 接口对控制台语义为“删除发布记录”，后端落库动作为 `status = archived`。
2. 已存在的 `performance_snapshots` 不做物理删除，仍保留在归档记录下用于复盘。
3. 若后续补充发布记录列表接口，应默认隐藏 `archived` 数据，并沿用 `include_archived` 过滤约定。

响应体：

```json
{
  "code": "OK",
  "message": "success",
  "data": {
    "publish_record_id": "pr_001",
    "status": "archived"
  },
  "request_id": "req_20260410_001"
}
```

## 12. 报表域

### 12.1 模板效果报表

`GET /reports/templates/performance`

返回维度：

1. 模板使用次数
2. 审核通过率
3. 已发布次数
4. 平均点赞
5. 平均收藏
6. 平均完播

### 12.2 样本研究导出

`POST /reports/posts/export`

请求参数：

1. 关键词
2. 时间范围
3. 是否仅历史高赞
4. 导出格式 `csv` / `markdown`

## 13. 第一阶段不提供的接口

1. 自动发布接口
2. 多平台统一调度接口
3. 实时消息推送接口
4. 模型供应商管理接口
5. 采集任务删除接口（第一阶段以历史留存和状态追踪为主）
6. 生成任务删除接口
7. 生成结果删除接口
8. 任意核心对象的物理删除接口

# API Contracts

本目录存放第一阶段 MVP 的接口契约，作用是让后端、前端和测试脚本对齐请求与响应结构。

## 当前覆盖范围

1. 平台列表
2. 采集任务
3. 内容样本
4. AI 分析
5. 模板中心
6. 内容生成
7. 审核与版本
8. 发布回填

## 统一规则

Base URL:

`/api/v1`

成功响应：

```json
{
  "code": "OK",
  "message": "success",
  "data": {},
  "request_id": "req_xxxxxxxxxxxx"
}
```

错误响应：

```json
{
  "code": "NOT_FOUND",
  "message": "resource not found",
  "data": null,
  "request_id": "req_xxxxxxxxxxxx"
}
```

## 当前接口清单

### 平台配置

1. `GET /platforms`

### 采集任务

1. `POST /collector-tasks`
2. `GET /collector-tasks`
3. `GET /collector-tasks/{task_id}`
4. `POST /collector-tasks/{task_id}/run`

### 内容样本

1. `GET /posts`
2. `GET /posts/{post_id}`
3. `POST /posts/manual-import`
4. `PATCH /posts/{post_id}`
5. `DELETE /posts/{post_id}`

### AI 分析

1. `POST /analysis-results`
2. `GET /analysis-results/{analysis_id}`
3. `POST /analysis-results/{analysis_id}/fact-check`

### 模板中心

1. `POST /templates`
2. `GET /templates`
3. `GET /templates/{template_id}`
4. `POST /templates/{template_id}/status`
5. `DELETE /templates/{template_id}`
6. 当前未提供“模板中心生成模板”的独立 AI 生成接口；现有 `POST /templates` 为模板落库接口，`POST /templates/auto-summarize` 为基于分析结果聚类归纳模板，不是模板中心页面内的实时 AI 生成能力。

### 内容生成

1. `POST /generation-jobs`
2. `GET /generation-jobs/{job_id}`
3. `GET /generated-contents`
4. `GET /generated-contents/{content_id}`
5. 当前未提供“动态模型选择”查询接口，例如模型列表、默认模型、按场景推荐模型等；前端若需要动态渲染模型选项，需新增专门配置接口。

### 审核与版本

1. `GET /generated-contents/{content_id}/review-compare`
2. `POST /generated-contents/{content_id}/versions`
3. `POST /reviews`

### 发布回填

1. `POST /publish-records`
2. `POST /publish-records/{publish_record_id}/snapshots`
3. `GET /publish-records`
4. `DELETE /publish-records/{publish_record_id}`

## 示例文件

1. [采集任务示例](/F:/viral-content-engine/shared/contracts/api/collector-task.examples.md)
2. [生成任务示例](/F:/viral-content-engine/shared/contracts/api/generation.examples.md)

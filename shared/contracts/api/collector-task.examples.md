# Collector Task Examples

## 创建采集任务

`POST /api/v1/collector-tasks`

请求体：

```json
{
  "platform_code": "zhihu",
  "task_type": "historical_hot",
  "query_keyword": "秦始皇",
  "collect_type": "search",
  "source_url": null,
  "source_id": null,
  "date_range_start": "2025-01-01T00:00:00+08:00",
  "date_range_end": "2026-04-13T00:00:00+08:00",
  "limit": 20
}
```

响应体：

```json
{
  "code": "OK",
  "message": "success",
  "data": {
    "id": "ct_xxx",
    "task_id": "ct_xxx",
    "status": "pending",
    "execution_status": "PENDING"
  },
  "request_id": "req_xxx"
}
```

## 执行采集任务

`POST /api/v1/collector-tasks/{task_id}/run`

响应体：

```json
{
  "code": "OK",
  "message": "success",
  "data": {
    "id": "ct_xxx",
    "task_id": "ct_xxx",
    "status": "succeeded",
    "execution_status": "SUCCESS",
    "success_count": 8,
    "failed_count": 0,
    "retry_count": 0,
    "raw_output_path": "data/raw/zhihu/ct_xxx/20260413_102000/raw.json",
    "error_message": null
  },
  "request_id": "req_xxx"
}
```


# codex-backend

这个目录由 Codex 主导开发，承载 Python 后端与核心业务流程。

## 第一阶段职责

1. 平台采集适配器
2. 内容清洗与规范化
3. AI 内容理解
4. 模板归纳
5. 新内容生成
6. 提供给控制台的 API

## 当前实现状态

已落地模块：

1. `app/collectors/zhihu/adapter.py`（知乎采集器 MVP）
2. `app/analyzers/content_features.py`（内容特征分析，规则版）
3. `app/templates/template_engine.py`（模板结构归纳）
4. `app/generators/script_generator.py`（脚本生成）
5. `app/api/routes.py`（第一阶段核心 API）

持久化方案：

- 使用 `SQLAlchemy + SQLite`
- 默认数据库文件：`%TEMP%/viral-content-engine/app.db`（可通过 `DATABASE_URL` 覆盖）
- 应用启动时自动建表
- 已初始化 `Alembic`，后续表结构变更统一通过迁移脚本管理

采集执行方案：

- 使用 `collectors/zhihu/executor.py` 子进程调用 MediaCrawler。
- 使用 `collectors/zhihu/adapter.py` 做原始 JSON 到标准字段映射。
- 默认开启 `MEDIACRAWLER_FALLBACK_MOCK=true`，当本机未安装 MediaCrawler 时会自动回退到 `scripts/mock_mediacrawler_runner.py`。
- 执行状态枚举：`PENDING / RUNNING / SUCCESS / FAILED / RATE_LIMITED / LOGIN_EXPIRED / PROXY_FAILED / VERIFICATION_REQUIRED`。
- 每个任务独立日志落盘到 `logs/task_{task_id}.log`，raw JSON 落盘到 `data/raw/{platform}/{task_id}/{timestamp}/raw.json`。
- 暴露 Prometheus 指标：`GET /metrics`（运行任务数、累计成功/失败、平均耗时）。

## 已打通接口

1. `GET /api/v1/platforms`
2. `POST /api/v1/collector-tasks`
3. `POST /api/v1/collector-tasks/{task_id}/run`
4. `GET /api/v1/posts`
5. `POST /api/v1/analysis-results`
6. `POST /api/v1/templates`
7. `POST /api/v1/templates/ai-generate`
8. `GET /api/v1/model-options?scene=generation`
9. `POST /api/v1/generation-jobs`

## 本地运行

```powershell
python -m pip install -r requirements/requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

## PyCharm 启动（推荐）

如果历史 Run Configuration 混乱，建议新建一个 Python 配置，直接运行：

1. Script path：`F:/viral-content-engine/apps/codex-backend/run_dev.py`
2. Working directory：`F:/viral-content-engine/apps/codex-backend`
3. Python interpreter：项目对应的 `.venv`

或者使用 Module 模式：

1. Module name：`app`
2. Working directory：`F:/viral-content-engine/apps/codex-backend`

## P0 注意事项

- 请在 `.env` 中配置真实 `OPENAI_API_KEY`，占位值（如 `your-api-key-here`）会被判定为“未配置”，系统将走 Fallback。
- 新增文本预处理链路：HTML 清理、Markdown 规整、长文本分段，已接入采集入库、手动导入、分析前处理。
- 新增模板自动归纳接口：`POST /api/v1/templates/auto-summarize`（基于多条分析结果聚类生成模板）。
- 新增模板中心 AI 生成接口：`POST /api/v1/templates/ai-generate`（实时调用 AI 生成 `structure_json` 并直接落库）。
- 新增模型选项接口：`GET /api/v1/model-options?scene=generation`（前端动态发现模型与默认值，返回白名单字段，不透出 `.env` 原值）。
- `POST /api/v1/generation-jobs` 的 `model_name` 已与 `GET /api/v1/model-options?scene=generation` 对齐校验：仅允许启用模型；不传则走该场景默认模型。

接口边界说明：

- 手工创建模板：`POST /api/v1/templates`，由调用方提供 `structure_json`。
- 自动归纳模板：`POST /api/v1/templates/auto-summarize`，基于已有分析结果聚类归纳。
- AI 生成模板：`POST /api/v1/templates/ai-generate`，实时触发大模型生成模板结构并保存。
- 模型配置接口：`GET /api/v1/model-options` 仅用于前端发现可选模型，不执行内容生成任务。

## 数据库迁移（Alembic）

```powershell
# 初始化数据库到最新版本
alembic upgrade head

# 基于模型变更生成迁移脚本
alembic revision --autogenerate -m "your_migration_name"

# 执行新增迁移
alembic upgrade head
```

## 异步任务（P2 第一阶段）

- 重任务接口支持 `async_mode=true`：
1. `POST /api/v1/collector-tasks/{task_id}/run?async_mode=true`
2. `POST /api/v1/analysis-results?async_mode=true`
3. `POST /api/v1/generation-jobs?async_mode=true`
- 任务进度查询：`GET /api/v1/tasks/{task_id}`

## 缓存层（P2 第一阶段）

- 当前默认使用内存 TTL 缓存（可通过配置关闭）
- 高频接口已缓存：`GET /api/v1/health`、`GET /api/v1/platforms`、`GET /api/v1/templates`
- AI 调用结果已缓存：相同 `prompt + schema + model + task_type + prompt_version` 命中

## 批量操作（P2 第一阶段）

1. `POST /api/v1/posts/batch-import`
2. `POST /api/v1/analysis-results/batch-create`
3. `DELETE /api/v1/posts/batch`

## 搜索（P2 第一阶段）

- 基于 SQLite FTS5：
1. `GET /api/v1/posts/search?q=...`（标题、正文、关键词）
2. `GET /api/v1/templates/search?q=...`（模板名称、类型、分类）

## 索引优化（P1）

- 已提供高频查询索引迁移：`20260415_0004_add_query_indexes`

可选环境变量（采集）：

```powershell
$env:CRAWL_MAX_CONCURRENT_TASKS="2"
$env:CRAWL_TASK_TIMEOUT_SECONDS="300"
$env:CRAWL_MAX_RETRY_COUNT="3"
$env:CRAWL_RETRY_EXPONENTIAL_BASE="60"
$env:CRAWL_TEMP_USER_DATA_DIR_PREFIX="/tmp/mediacrawler_"
$env:MEDIACRAWLER_ENABLE_REAL="false"
$env:MEDIACRAWLER_PROJECT_DIR="external/MediaCrawler"
$env:MEDIACRAWLER_EXECUTABLE="mediacrawler"
$env:MEDIACRAWLER_FALLBACK_MOCK="true"
$env:CRAWL_PROXY_POOL="http://proxy1:7890,http://proxy2:7890"
$env:CRAWL_VERIFICATION_WEBHOOK="https://example.com/webhook"
```

## 运行测试

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

## 环境变量示例

请复制 [`.env.example`](/F:/viral-content-engine/apps/codex-backend/.env.example) 为 `.env` 后再启动服务。

常用配置项包括：

1. `DATABASE_URL`
2. `CRAWL_RAW_OUTPUT_ROOT`
3. `CRAWL_LOGS_DIR`
4. `MEDIACRAWLER_PROJECT_DIR`
5. `MEDIACRAWLER_ENABLE_REAL`
6. `MEDIACRAWLER_FALLBACK_MOCK`
7. `CRAWL_PROXY_POOL`
8. `CRAWL_VERIFICATION_WEBHOOK`

## 契约文档

1. [本地启动说明](/F:/viral-content-engine/docs/11-local-setup.md)
2. [API 契约](/F:/viral-content-engine/shared/contracts/api/README.md)
3. [Schema 契约](/F:/viral-content-engine/shared/contracts/schemas/README.md)
4. [Prompt 契约](/F:/viral-content-engine/shared/contracts/prompts/README.md)


# 协作与启动约定

## 1. 文档目标

本文档用于降低 `Codex + Qoder + PyCharm` 协作成本，统一最小开发约定。

## 2. 工作区建议

1. `Codex` 工作区指向 `F:\viral-content-engine\apps\codex-backend`
2. `Qoder` 工作区指向 `F:\viral-content-engine\apps\qoder-console`
3. `PyCharm` 主项目建议打开 `F:\viral-content-engine\apps\codex-backend`
4. 共享文档和协议通过绝对路径访问 `F:\viral-content-engine\docs` 与 `F:\viral-content-engine\shared\contracts`

## 3. Prompt 协作规则

1. Prompt 文件统一放在 `shared/contracts/prompts`
2. 文件命名与版本号遵循 `08-data-dictionary.md` 中的规则
3. Prompt 改动涉及输出结构变化时，必须同步更新接口文档或 JSON Schema
4. Prompt 不直接散落在业务代码中

## 4. 数据库协作规则

1. 状态流转字段只允许后端服务统一修改
2. 人工审核、事实确认、发布回填只通过 API 完成，不直接改数据库
3. 数据字典中的“写入方”定义是联调边界，不要绕过
4. 删除动作只通过删除/归档类 API 完成，不直接物理删库

## 5. 极简启动指引

第一阶段只要求启动后端最小链路：

1. 安装 Python 3.11+
2. 在 `apps/codex-backend` 创建虚拟环境
3. 安装基础依赖：`fastapi`、`uvicorn`、`sqlalchemy`、`alembic`、`pydantic`
4. 使用 SQLite 作为本地数据库
5. 将原始数据目录指向 `F:\viral-content-engine\data`

建议启动顺序：

1. 先启动数据库迁移
2. 再启动 FastAPI
3. 最后再联调控制台

## 6. 第一阶段联调顺序

1. 先打通 `POST /collector-tasks` 和 `POST /collector-tasks/{task_id}/run`
2. 再打通 `POST /analysis-results`
3. 然后实现 `POST /templates`
4. 接着打通 `POST /generation-jobs`
5. 最后联调审核、版本和发布回填接口

## 6.1 接口依赖简述

1. 采集任务 (`/collector-tasks`) 不依赖其他域，可独立开发。
2. 样本分析 (`/analysis-results`) 依赖 `posts` 表中已有样本。
3. 模板创建 (`/templates`) 依赖已分析的样本作为示例来源，但非强制。
4. 内容生成 (`/generation-jobs`) 依赖已启用的模板和可选参考样本。
5. 审核 (`/reviews`) 依赖已生成的 `generated_contents`。
6. 发布回填 (`/publish-records`) 依赖已审核通过的内容。

## 6.2 删除类接口联调约定

1. 控制台可统一展示为“删除”，但接口语义按“归档”联调，删除成功后默认从列表移除。
2. 前端列表默认不请求 `archived` 数据；只有在“查看归档”或类似场景下才传 `include_archived=true`。
3. 详情页允许继续打开已归档资源，用于查看来源、版本、审核意见和发布留痕。
4. 若后端返回 `RESOURCE_IN_USE`，前端应直接展示返回的依赖说明，不自行猜测阻塞原因。
5. 第一阶段控制台不应给 `generation_jobs`、`generated_contents`、`collection_tasks` 提供删除入口。

## 7. 常见问题 (FAQ)

> 本章节在实际开发过程中逐步补充，遇到典型问题后再填写。

### 环境启动

（待补充）

### 数据库迁移

（待补充）

### 采集器调试

（待补充）

### 接口联调

（待补充）

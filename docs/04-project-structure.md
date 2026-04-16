# 目录结构设计

## 1. 目标

目录结构要同时满足：

1. 你能边学边看懂
2. Codex 与 Qoder 不在同一目录开发
3. PyCharm 易于管理 Python 项目
4. 后续可以逐步扩展

## 2. 推荐目录

```text
viral-content-engine/
├─ README.md
├─ docs/
│  ├─ 01-prd.md
│  ├─ 02-architecture.md
│  ├─ 03-database.md
│  └─ 04-project-structure.md
├─ shared/
│  └─ contracts/
│     ├─ api/
│     ├─ schemas/
│     └─ prompts/
├─ apps/
│  ├─ codex-backend/
│  │  ├─ README.md
│  │  ├─ app/
│  │  │  ├─ api/
│  │  │  ├─ collectors/
│  │  │  ├─ analyzers/
│  │  │  ├─ templates/
│  │  │  ├─ generators/
│  │  │  ├─ repositories/
│  │  │  ├─ services/
│  │  │  ├─ models/
│  │  │  └─ core/
│  │  ├─ scripts/
│  │  ├─ tests/
│  │  └─ requirements/
│  └─ qoder-console/
│     ├─ README.md
│     ├─ src/
│     ├─ public/
│     └─ tests/
└─ data/
   ├─ raw/
   ├─ processed/
   └─ exports/
```

## 3. 每个目录的职责

### `docs/`

放产品定义、流程设计、数据库文档、开发约定。

### `shared/contracts/`

放双方共享的固定协议：

1. API 输入输出示例
2. JSON Schema
3. Prompt 模板草案
4. 标签字典

注意：
这里尽量放“约定”，少放复杂实现。

### `apps/codex-backend/`

这是 Python 主项目，建议你用 PyCharm 重点打开这个目录。

Codex 适合负责：

1. 采集器封装
2. 数据清洗
3. AI 分析链路
4. 模板提取逻辑
5. 脚本生成逻辑
6. API 接口

### `apps/qoder-console/`

这是单独的前端或轻控制台目录。

Qoder 适合负责：

1. 审核页面
2. 任务列表页
3. 模板查看页
4. 生成结果编辑页

### `data/`

本地开发的数据输出目录：

1. `raw/`：原始采集数据
2. `processed/`：清洗和分析后的文件
3. `exports/`：导出的研究报告或 CSV

## 4. 你的实际开发建议

### 你自己

主看这几个地方：

1. `apps/codex-backend/app/collectors`
2. `apps/codex-backend/app/analyzers`
3. `apps/codex-backend/app/generators`

### 让 Codex 做

1. Python 工程初始化
2. 数据模型
3. API
4. 分析和生成流程

### 让 Qoder 做

1. 前端页面骨架
2. 审核控制台
3. 简单交互页面

## 5. 第一阶段最小落地目录

如果想更轻一点，第一阶段最少只要这些：

```text
apps/codex-backend/app/collectors
apps/codex-backend/app/analyzers
apps/codex-backend/app/generators
shared/contracts/prompts
shared/contracts/schemas
docs
```

## 6. 协作约定

1. `shared/contracts` 改动要先同步文档。
2. Codex 不直接改 `apps/qoder-console`。
3. Qoder 不直接改 `apps/codex-backend`。
4. 需要联调时，以 `shared/contracts/api` 为准。

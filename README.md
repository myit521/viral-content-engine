# Viral Content Engine

> 面向短视频内容生产的研究与生成系统，聚焦 **爆款理解 → 模板沉淀 → 可控生成** 闭环。

---

## 概述

Viral Content Engine 是一个全栈内容研究与脚本生产工具。项目目标不是"全自动发爆款"，而是以 **AI 辅助分析与生成、人工把控质量与发布** 的方式，构建一套稳定的内容生产工作流。

### 核心流程

```
历史爆款采集 → 内容理解 → 结构抽象 → 模板沉淀 → 新内容生成 → 人审发布 → 数据复盘
```

### 功能亮点

- **多平台采集** — 插件化平台适配器（第一阶段支持知乎，小红书 / B站 规划中）
- **AI 内容分析** — 自动提取爆款特征、叙事结构、情绪驱动、事实风险识别
- **模板引擎** — 从成功内容中归纳可复用的结构化模板，支持版本管理
- **可控生成** — 基于模板生成视频脚本、分镜、标题、封面文案
- **人工审核** — 原始样本、AI 初稿、编辑稿三栏对比审核
- **发布复盘** — 追踪发布内容的传播效果，反哺模板优化

---

## 技术栈

| 层级 | 技术 |
|------|------|
| **后端** | Python 3.11+ / FastAPI / SQLAlchemy 2.0 / Alembic |
| **前端** | React 19 / TypeScript / Vite / React Router 7 |
| **数据库** | SQLite（开发阶段）/ PostgreSQL（生产就绪） |
| **AI 集成** | OpenAI 兼容 API（支持 OpenAI、DeepSeek、通义千问、智谱等） |
| **监控** | Prometheus Client |
| **HTTP 客户端** | httpx |

---

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- 一个 OpenAI 兼容的 API Key（OpenAI、DeepSeek 等）

### 后端启动

```bash
cd apps/backend

# 1. 创建虚拟环境
python -m venv venv
source venv/bin/activate        # Linux / macOS
# .\venv\Scripts\activate       # Windows

# 2. 安装依赖
pip install -r requirements/requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env，填入你的 API Key（OPENAI_API_KEY 为必填项）

# 4. 启动开发服务器
python run_dev.py
```

后端运行在 `http://localhost:8000`，交互式 API 文档可访问 `http://localhost:8000/docs`。

### 前端启动

```bash
cd apps/console

# 1. 安装依赖
npm install

# 2. 启动开发服务器
npm run dev
```

前端控制台运行在 `http://localhost:3000`，API 请求会自动代理到后端。

---

## 项目结构

```
viral-content-engine/
├── apps/
│   ├── backend/                  # 后端服务 (FastAPI)
│   │   ├── app/
│   │   │   ├── api/              # 路由处理
│   │   │   ├── models/           # ORM 模型 & Pydantic Schema
│   │   │   ├── services/         # 业务逻辑层
│   │   │   ├── collectors/       # 平台采集适配器
│   │   │   │   └── zhihu/        # 知乎适配器实现
│   │   │   ├── analyzers/        # 内容特征分析
│   │   │   ├── templates/        # 模板引擎
│   │   │   ├── generators/       # 脚本生成
│   │   │   ├── repositories/     # 数据访问层
│   │   │   └── core/             # 配置、数据库、缓存、指标
│   │   ├── migrations/           # Alembic 数据库迁移
│   │   ├── requirements/         # Python 依赖
│   │   └── run_dev.py            # 开发服务器入口
│   └── console/                  # 前端控制台 (React + Vite)
│       └── src/
│           ├── api/              # API 客户端 & 标签字典
│           ├── components/       # 共享 UI 组件
│           └── pages/            # 页面组件（11 个页面）
├── shared/
│   └── contracts/                # 共享协议
│       ├── api/                  # API 契约 & 示例
│       ├── schemas/              # JSON Schema 定义
│       └── prompts/              # 版本化 Prompt 模板
├── docs/                         # 项目文档（11 篇）
├── data/                         # 数据目录
│   ├── raw/                      # 原始采集数据
│   ├── processed/                # 处理后的数据
│   └── exports/                  # 导出文件
└── README.md
```

---

## API 概览

后端在 `/api/v1` 下提供 RESTful API，主要端点分组：

| 分组 | 端点 | 说明 |
|------|------|------|
| **平台** | `GET /platforms` | 获取支持的平台列表 |
| **采集任务** | `POST/GET /collector-tasks` | 创建和管理采集任务 |
| **内容样本** | `GET/POST/PATCH/DELETE /posts` | 浏览、录入、编辑、搜索内容样本 |
| **AI 分析** | `POST /analysis-results` | 对采集内容执行 AI 分析 |
| **模板中心** | `POST/GET /templates` | 创建、自动聚类、AI 生成、管理模板 |
| **内容生成** | `POST /generation-jobs` | 创建脚本生成任务 |
| **生成结果** | `GET /generated-contents` | 查看和审核生成内容 |
| **审核** | `GET /review-compare`, `POST /reviews` | 三栏对比审核与编辑反馈 |
| **发布** | `POST/GET /publish-records` | 记录发布并回填效果数据 |
| **监控** | `GET /metrics`, `GET /health` | Prometheus 指标与健康检查 |

完整 API 文档可在后端启动后访问 `http://localhost:8000/docs`（Swagger UI），或查看 [`docs/07-api-spec.md`](docs/07-api-spec.md)。

---

## 配置说明

后端通过环境变量配置，将 `.env.example` 复制为 `.env` 后按需修改：

| 变量 | 必填 | 说明 |
|------|------|------|
| `OPENAI_API_KEY` | 是 | AI 服务 API Key |
| `OPENAI_BASE_URL` | 否 | 自定义 API 地址（默认：OpenAI 官方） |
| `AI_PROVIDER` | 否 | 提供商：`openai` / `deepseek` / `dashscope` / `zhipu` / `custom` |
| `DEFAULT_MODEL_NAME` | 否 | 默认模型（默认：`gpt-4.1-mini`） |
| `DATABASE_URL` | 否 | 数据库连接字符串（默认：SQLite） |
| `AI_ANALYSIS_MODEL` | 否 | 分析任务使用的模型 |
| `AI_GENERATION_MODEL` | 否 | 脚本生成使用的模型 |
| `AI_TEMPLATE_INDUCTION_MODEL` | 否 | 模板归纳使用的模型 |
| `CACHE_ENABLED` | 否 | 是否启用响应缓存（默认：`true`） |
| `CRAWL_MAX_CONCURRENT_TASKS` | 否 | 最大并发采集任务数（默认：`2`） |

完整配置项请参考 [`apps/backend/.env.example`](apps/backend/.env.example)。

---

## 项目文档

完整的项目文档位于 [`docs/`](docs/) 目录：

| 文档 | 说明 |
|------|------|
| [`01-prd.md`](docs/01-prd.md) | 产品需求文档 |
| [`02-architecture.md`](docs/02-architecture.md) | 高层架构设计 |
| [`03-database.md`](docs/03-database.md) | 数据库设计（18 张表） |
| [`04-project-structure.md`](docs/04-project-structure.md) | 项目结构规范 |
| [`05-technical-solution.md`](docs/05-technical-solution.md) | 技术方案分析 |
| [`06-architecture-design.md`](docs/06-architecture-design.md) | 详细架构设计 |
| [`07-api-spec.md`](docs/07-api-spec.md) | API 接口规范 |
| [`08-data-dictionary.md`](docs/08-data-dictionary.md) | 数据字典 |
| [`09-collaboration-guide.md`](docs/09-collaboration-guide.md) | 协作指南 |
| [`10-glossary.md`](docs/10-glossary.md) | 术语表 |
| [`11-local-setup.md`](docs/11-local-setup.md) | 本地环境搭建指南 |

---

## 系统架构

系统采用分层架构，各层职责清晰：

```
┌─────────────────────────────────────────────────┐
│            控制台 (React + Vite)                 │  表现层
├─────────────────────────────────────────────────┤
│            API 路由 (FastAPI)                    │  应用层
├─────────────────────────────────────────────────┤
│  采集器  │  分析器  │  模板引擎  │  生成器       │  领域层
├─────────────────────────────────────────────────┤
│  业务服务  │  数据仓库  │  AI 客户端             │  基础设施层
├─────────────────────────────────────────────────┤
│  SQLAlchemy │  httpx  │  Prompt 管理  │  缓存    │  基座层
└─────────────────────────────────────────────────┘
```

### 设计亮点

- **插件化采集** — 平台适配器基于插件模式，实现基础采集接口即可接入新平台
- **版本化 Prompt** — 所有 AI 提示词以版本化 Markdown 文件存储于 `shared/contracts/prompts/`，确保分析和生成的可复现性
- **事实风险追踪** — AI 识别内容中的潜在事实风险，人工确认或驳回后方可发布
- **来源可追溯** — 所有生成内容保留到源模板和原始样本的映射关系
- **逻辑删除** — 删除操作映射为状态归档，保留完整审计轨迹

---

## 路线图

### 第一阶段（当前）
- [x] 知乎内容采集
- [x] AI 内容分析
- [x] 模板归纳引擎
- [x] 脚本生成流水线
- [x] 人工审核工作流
- [x] 发布与效果追踪

### 第二阶段（规划中）
- [ ] 小红书平台支持
- [ ] B站平台支持
- [ ] 模板聚类算法优化
- [ ] 批量生成工作流

### 第三阶段（远期）
- [ ] 抖音平台支持
- [ ] PostgreSQL 生产部署
- [ ] 多用户协作
- [ ] 数据分析仪表盘

---

## 参与贡献

欢迎贡献代码！参与方式：

1. Fork 本仓库
2. 创建特性分支（`git checkout -b feature/amazing-feature`）
3. 提交更改（`git commit -m 'Add amazing feature'`）
4. 推送分支（`git push origin feature/amazing-feature`）
5. 提交 Pull Request

开发规范和工作区约定请参阅 [协作指南](docs/09-collaboration-guide.md)。

---

## 许可证

本项目基于 MIT 许可证开源，详见 [LICENSE](LICENSE) 文件。

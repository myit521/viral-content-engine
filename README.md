# Viral Content Engine

> A research and generation system for short-video content production, focusing on the closed-loop of **viral content understanding -> template distillation -> controlled generation**.

[English](#overview) | [中文](#概述)

---

## Overview

Viral Content Engine is a full-stack tool designed for short-video content research and script production. Rather than aiming for fully automated publishing, it emphasizes a **human-in-the-loop** workflow where AI assists with analysis and generation while humans retain editorial control.

### Core Pipeline

```
Historical Viral Collection -> Content Understanding -> Structure Abstraction
    -> Template Distillation -> New Content Generation -> Human Review & Publish -> Data Review
```

### Key Features

- **Multi-Platform Collection** - Pluggable collector adapters (Zhihu supported in Phase 1, Xiaohongshu / Bilibili planned)
- **AI-Powered Analysis** - Automatic extraction of viral content features, narrative structures, and emotional drivers
- **Template Engine** - Distill successful content patterns into reusable, versioned templates
- **Controlled Generation** - Generate video scripts, shot lists, titles, and cover copy from templates
- **Human Review** - Side-by-side comparison of source material, AI drafts, and edited versions
- **Publish & Review** - Track published content performance and feed insights back into template optimization

---

## 概述

Viral Content Engine 是一个面向短视频内容生产的研究与生成系统。项目目标不是"全自动发爆款"，而是构建一个稳定的**内容研究与脚本生产工具**，以 AI 辅助分析与生成，人工把控质量与发布。

### 核心流程

```
历史爆款采集 → 内容理解 → 结构抽象 → 模板沉淀 → 新内容生成 → 人审发布 → 数据复盘
```

### 功能亮点

- **多平台采集** - 插件化平台适配器（第一阶段支持知乎，小红书 / B站 规划中）
- **AI 内容分析** - 自动提取爆款特征、叙事结构、情绪驱动、事实风险识别
- **模板引擎** - 从成功内容中归纳可复用的结构化模板，支持版本管理
- **可控生成** - 基于模板生成视频脚本、分镜、标题、封面文案
- **人工审核** - 原始样本、AI 初稿、编辑稿三栏对比审核
- **发布复盘** - 追踪发布内容的传播效果，反哺模板优化

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.11+ / FastAPI / SQLAlchemy 2.0 / Alembic |
| **Frontend** | React 19 / TypeScript / Vite / React Router 7 |
| **Database** | SQLite (development) / PostgreSQL (production-ready) |
| **AI Integration** | OpenAI-compatible API (supports OpenAI, DeepSeek, DashScope, Zhipu, custom providers) |
| **Monitoring** | Prometheus Client |
| **HTTP Client** | httpx |

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- An OpenAI-compatible API key (OpenAI, DeepSeek, etc.)

### Backend Setup

```bash
cd apps/backend

# 1. Create virtual environment
python -m venv venv
source venv/bin/activate        # Linux / macOS
# .\venv\Scripts\activate       # Windows

# 2. Install dependencies
pip install -r requirements/requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env and fill in your API key (OPENAI_API_KEY is required)

# 4. Start development server
python run_dev.py
```

The backend runs at `http://localhost:8000`. Interactive API docs are available at `http://localhost:8000/docs`.

### Frontend Setup

```bash
cd apps/console

# 1. Install dependencies
npm install

# 2. Start development server
npm run dev
```

The console is accessible at `http://localhost:3000`. API requests are automatically proxied to the backend.

---

## Project Structure

```
viral-content-engine/
├── apps/
│   ├── backend/                  # Backend service (FastAPI)
│   │   ├── app/
│   │   │   ├── api/              # Route handlers
│   │   │   ├── models/           # ORM & Pydantic schemas
│   │   │   ├── services/         # Business logic layer
│   │   │   ├── collectors/       # Platform collector adapters
│   │   │   │   └── zhihu/        # Zhihu adapter implementation
│   │   │   ├── analyzers/        # Content feature analysis
│   │   │   ├── templates/        # Template engine
│   │   │   ├── generators/       # Script generation
│   │   │   ├── repositories/     # Data access layer
│   │   │   └── core/             # Config, DB, cache, metrics
│   │   ├── migrations/           # Alembic DB migrations
│   │   ├── requirements/         # Python dependencies
│   │   └── run_dev.py            # Dev server entry point
│   └── console/                  # Frontend console (React + Vite)
│       └── src/
│           ├── api/              # API client & label dictionaries
│           ├── components/       # Shared UI components
│           └── pages/            # Page components (11 pages)
├── shared/
│   └── contracts/                # Shared protocols
│       ├── api/                  # API contract & examples
│       ├── schemas/              # JSON Schema definitions
│       └── prompts/              # Versioned prompt templates
├── docs/                         # Project documentation (11 docs)
├── data/                         # Data directory
│   ├── raw/                      # Raw collected data
│   ├── processed/                # Processed data
│   └── exports/                  # Exported files
└── README.md
```

---

## API Overview

<<<<<<< HEAD
=======
The backend exposes a RESTful API under `/api/v1`. Key endpoint groups:

| Group | Endpoints | Description |
|-------|-----------|-------------|
| **Platforms** | `GET /platforms` | List supported platforms |
| **Collector Tasks** | `POST/GET /collector-tasks` | Create and manage collection tasks |
| **Posts** | `GET/POST/PATCH/DELETE /posts` | Browse, import, edit, and search content samples |
| **Analysis** | `POST /analysis-results` | Run AI analysis on collected posts |
| **Templates** | `POST/GET /templates` | Create, auto-summarize, AI-generate, and manage templates |
| **Generation** | `POST /generation-jobs` | Create script generation jobs |
| **Generated Contents** | `GET /generated-contents` | View and review generated content |
| **Review** | `GET /review-compare`, `POST /reviews` | Side-by-side review and editorial feedback |
| **Publish** | `POST/GET /publish-records` | Record publications and backfill performance data |
| **Monitoring** | `GET /metrics`, `GET /health` | Prometheus metrics and health check |

Full API documentation is available at `http://localhost:8000/docs` (Swagger UI) when the backend is running, or see [`docs/07-api-spec.md`](docs/07-api-spec.md).

---

## Configuration

The backend is configured via environment variables. Copy `.env.example` to `.env` and customize:

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | API key for AI services |
| `OPENAI_BASE_URL` | No | Custom API base URL (default: OpenAI) |
| `AI_PROVIDER` | No | Provider: `openai` / `deepseek` / `dashscope` / `zhipu` / `custom` |
| `DEFAULT_MODEL_NAME` | No | Default model (default: `gpt-4.1-mini`) |
| `DATABASE_URL` | No | Database connection string (default: SQLite) |
| `AI_ANALYSIS_MODEL` | No | Model for analysis tasks |
| `AI_GENERATION_MODEL` | No | Model for script generation |
| `AI_TEMPLATE_INDUCTION_MODEL` | No | Model for template induction |
| `CACHE_ENABLED` | No | Enable response caching (default: `true`) |
| `CRAWL_MAX_CONCURRENT_TASKS` | No | Max concurrent collection tasks (default: `2`) |

See [`apps/backend/.env.example`](apps/backend/.env.example) for the full list of configuration options.

---

## Documentation

Comprehensive project documentation is available in the [`docs/`](docs/) directory:

| Document | Description |
|----------|-------------|
| [`01-prd.md`](docs/01-prd.md) | Product Requirements Document |
| [`02-architecture.md`](docs/02-architecture.md) | High-level Architecture |
| [`03-database.md`](docs/03-database.md) | Database Design (18 tables) |
| [`04-project-structure.md`](docs/04-project-structure.md) | Project Structure Conventions |
| [`05-technical-solution.md`](docs/05-technical-solution.md) | Technical Solution Analysis |
| [`06-architecture-design.md`](docs/06-architecture-design.md) | Detailed Architecture Design |
| [`07-api-spec.md`](docs/07-api-spec.md) | API Specification |
| [`08-data-dictionary.md`](docs/08-data-dictionary.md) | Data Dictionary |
| [`09-collaboration-guide.md`](docs/09-collaboration-guide.md) | Collaboration Guide |
| [`10-glossary.md`](docs/10-glossary.md) | Glossary of Terms |
| [`11-local-setup.md`](docs/11-local-setup.md) | Local Setup Guide |

---

## Architecture

The system follows a layered architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────┐
│              Console (React + Vite)              │  Presentation Layer
├─────────────────────────────────────────────────┤
│              API Routes (FastAPI)                │  Application Layer
├─────────────────────────────────────────────────┤
│  Collectors │ Analyzers │ Templates │ Generators │  Domain Layer
├─────────────────────────────────────────────────┤
│   Services  │  Repositories  │  AI Client       │  Infrastructure Layer
├─────────────────────────────────────────────────┤
│  SQLAlchemy │  httpx  │  Prompt Manager │ Cache  │  Foundation Layer
└─────────────────────────────────────────────────┘
```

### Design Highlights

- **Pluggable Collectors** - Platform adapters are plugin-based; add new platforms by implementing the base collector interface
- **Versioned Prompts** - All AI prompts are stored as versioned Markdown files in `shared/contracts/prompts/`, enabling reproducible analysis and generation
- **Fact Risk Tracking** - AI identifies potential factual risks in content; humans confirm or dismiss them before publishing
- **Source Traceability** - All generated content preserves mappings back to source templates and original samples
- **Logical Deletion** - Delete operations map to status archival, preserving audit trails

---

## Roadmap

### Phase 1 (Current)
- [x] Zhihu content collection
- [x] AI-powered content analysis
- [x] Template distillation engine
- [x] Script generation pipeline
- [x] Human review workflow
- [x] Publish & performance tracking

### Phase 2 (Planned)
- [ ] Xiaohongshu platform support
- [ ] Bilibili platform support
- [ ] Enhanced template clustering algorithms
- [ ] Batch generation workflows

### Phase 3 (Future)
- [ ] Douyin platform support
- [ ] PostgreSQL production deployment
- [ ] Multi-user collaboration
- [ ] Performance analytics dashboard

---

## Contributing

Contributions are welcome! Here's how to get started:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please read the [Collaboration Guide](docs/09-collaboration-guide.md) for workspace conventions and development practices.

---
>>>>>>> 065b593 (docs: rewrite README to open-source standards and add MIT LICENSE)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

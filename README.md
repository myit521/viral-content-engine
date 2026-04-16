# Viral Content Engine

一个面向短视频内容生产的研究与生成系统，核心流程为：

`历史爆款采集 -> 内容理解 -> 结构抽象 -> 模板沉淀 -> 新内容生成 -> 人审发布 -> 数据复盘`

当前阶段目标不是“全自动发爆款”，而是先做成一个稳定的内容研究与脚本生产工具，帮助你边学 Python 边把项目跑起来。

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- SQLite（开发阶段）

### 后端启动

```bash
cd apps/backend

# 1. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 .\venv\Scripts\activate  # Windows

# 2. 安装依赖
pip install -r requirements/base.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 填入你的 API 密钥

# 4. 启动开发服务器
python run_dev.py
```

### 前端启动

```bash
cd apps/console

# 1. 安装依赖
npm install

# 2. 启动开发服务器
npm run dev
```

访问 http://localhost:3000 即可使用控制台。

## 项目结构

```
viral-content-engine/
├── apps/
│   ├── backend/           # 后端服务 (FastAPI)
│   └── console/           # 前端控制台 (React + Vite)
├── docs/                  # 项目文档
├── shared/contracts/      # 共享协议 (API Schema, Prompts)
└── data/                  # 数据目录
```

## 当前规划文档

- `docs/01-prd.md` - 产品需求文档
- `docs/02-architecture.md` - 系统架构
- `docs/03-database.md` - 数据库设计
- `docs/04-project-structure.md` - 项目结构
- `docs/05-technical-solution.md` - 技术方案
- `docs/06-architecture-design.md` - 架构设计
- `docs/07-api-spec.md` - API 规范
- `docs/08-data-dictionary.md` - 数据字典
- `docs/09-collaboration-guide.md` - 协作指南
- `docs/10-glossary.md` - 术语表
- `docs/README.md` - 文档索引


## License

MIT

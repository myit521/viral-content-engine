# 本地启动说明

## 1. 目标

这份文档只解决一件事：让你在本机把当前 MVP 跑起来，并且知道最短联调路径。

## 2. 前置环境

后端需要：

1. Python 3.11+
2. PowerShell
3. 可写本地目录权限

前端需要：

1. Node.js 18+
2. npm

MediaCrawler 可选：

1. 第一阶段不强制
2. 若未接入真实 MediaCrawler，可使用后端的 mock fallback

## 3. 后端启动

工作目录：

`F:\viral-content-engine\apps\codex-backend`

命令：

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements\requirements.txt
Copy-Item .env.example .env
python -m uvicorn app.main:app --reload --port 8000
```

启动成功后检查：

```powershell
Invoke-WebRequest http://127.0.0.1:8000/api/v1/health
Invoke-WebRequest http://127.0.0.1:8000/api/v1/platforms
Invoke-WebRequest http://127.0.0.1:8000/metrics
```

## 4. 前端启动

工作目录：

`F:\viral-content-engine\apps\qoder-console`

命令：

```powershell
npm install
npm run dev
```

## 5. 环境变量说明

请参考 [`.env.example`](/F:/viral-content-engine/apps/codex-backend/.env.example)。

当前最小必配通常只有：

1. `DATABASE_URL`
2. `MEDIACRAWLER_PROJECT_DIR`
3. `MEDIACRAWLER_ENABLE_REAL`

如果只是联调接口，保留默认值即可。

## 6. 最短联调路径

建议按这个顺序验证：

1. `POST /api/v1/posts/manual-import`
2. `POST /api/v1/analysis-results`
3. `POST /api/v1/templates`
4. `POST /api/v1/generation-jobs`
5. `POST /api/v1/reviews`
6. `POST /api/v1/publish-records`

这样即使真实采集器还没完全联通，也能先验证主流程。

## 7. 采集器验证路径

如果你要验证知乎采集链路，再额外跑：

1. `POST /api/v1/collector-tasks`
2. `POST /api/v1/collector-tasks/{task_id}/run`
3. `GET /api/v1/collector-tasks/{task_id}`
4. `GET /api/v1/posts`

## 8. 常见问题

### 终端中文乱码

PowerShell 某些编码设置下读取 Markdown 可能乱码，但文件本身通常没有问题。优先用 PyCharm 查看文档内容。

### MediaCrawler 未就绪

当前后端支持 `MEDIACRAWLER_FALLBACK_MOCK=true` 的降级路径，方便先联调业务链路。

### 数据库存放在哪里

默认通过 `DATABASE_URL=sqlite:///./data/app.db` 存在后端工作目录下。


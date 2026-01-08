# WP-GW-08 验收证据记录

**工作包**：WP-GW-08_DEPLOY_VERCEL（部署：Vercel 适配）

**负责人**：Joint（Codex + Gemini，Claude 复核）

**冻结日期**：2026-01-07

**冻结版本**：v1.0

---

## 验收清单完成状态

### 1) Vercel 构建通过（配置完备）

**证据**

- Vercel 构建入口与路由：`vercel.json`
- Serverless 入口：`api/index.py`
- Python 依赖入口：`api/requirements.txt`
- 前端构建脚本：`frontend/package.json`

**配置要点**

- 前端使用 `@vercel/static-build` 构建 `frontend/dist`
- 后端使用 `@vercel/python` 并设置 `maxDuration=30`
- `/api/v1/*`、`/media/*`、`/health` 统一转发到 FastAPI
- SPA fallback 统一回落 `index.html`
- 关键环境变量仅通过配置注入：`backend/.env.example`、`frontend/.env.example`

```json
// vercel.json (摘要)
{
  "builds": [
    { "src": "api/index.py", "use": "@vercel/python" },
    { "src": "frontend/package.json", "use": "@vercel/static-build", "config": { "distDir": "dist" } }
  ],
  "functions": { "api/index.py": { "maxDuration": 30 } },
  "rewrites": [
    { "source": "/api/v1/(.*)", "destination": "/api/index.py" },
    { "source": "/media/(.*)", "destination": "/api/index.py" },
    { "source": "/health", "destination": "/api/index.py" },
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

---

### 2) 前端可访问并调用后端 API

**证据**

- API Base 默认指向 `/api/v1`：`frontend/src/services/apiClient.ts`
- 环境变量示例：`frontend/.env.example`、`frontend/env.example`
- 后端路由前缀：`backend/app/api/routes/workflow.py`、`backend/app/api/routes/video.py`

**说明**

Vercel 通过 `/api/v1/*` rewrite 将请求转发到 FastAPI，前端直接调用 `/api/v1` 下的资源即可联通。

---

### 3) 生成任务返回 task_id，轮询可继续（异步不超时）

**证据**

- 异步生成返回 `task_id`：`backend/app/api/routes/video.py`
- 任务状态轮询：`backend/app/api/routes/video.py`
- 上游超时可配置：`backend/app/core/config.py`（`VIDEO_TIMEOUT_SEC`）
- Serverless 超时上限与异步策略一致：`vercel.json`（`maxDuration`）

```python
# backend/app/api/routes/video.py (摘要)
result = await provider.generate(upstream_payload, x_user_gemini_key)
task_id = result.get("task_id")
return JSONResponse(status_code=200, content=success_response({"task_id": task_id}))
```

---

### 4) 媒体外置存储（COS）

**证据**

- 上传接口与签名策略：`backend/app/api/routes/media.py`
- COS 客户端实现：`backend/app/storage/cos_client.py`
- COS 环境变量示例：`backend/.env.example`

---

## 回滚策略

- 若 Vercel Serverless 约束无法满足稳定性：后端迁移到更适合长任务的平台，前端保持不变。

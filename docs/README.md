# GridWorkflow 项目指南

> **AI 驱动的视频创作工作流平台** — 从创意构思到视频生成的一站式解决方案

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/XucroYuri/GridWorkflow)

---

## 📖 目录

- [快速开始](#-快速开始)
- [架构概览](#-架构概览)
- [本地开发](#-本地开发)
- [生产部署](#-生产部署)
- [API 文档](#-api-文档)
- [后续迭代计划](#-后续迭代计划)
- [常见问题](#-常见问题)

---

## 🚀 快速开始

### 前置要求

- **Node.js** 18+ (推荐 20 LTS)
- **Python** 3.11+
- **Git**

### 一键本地启动

```bash
# 1. 克隆仓库
git clone https://github.com/XucroYuri/GridWorkflow.git
cd GridWorkflow

# 2. 启动后端 (终端 1)
cd backend
python -m venv .venv
# Windows: .\.venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 3. 启动前端 (终端 2)
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173 即可使用。

---

## 🏗 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                      Vercel Edge                            │
├─────────────────────────────────────────────────────────────┤
│  ┌───────────────┐     ┌────────────────────────────────┐  │
│  │   Frontend    │     │         Backend API            │  │
│  │  (Vite/React) │────▶│  (FastAPI Serverless)          │  │
│  │               │     │                                │  │
│  │  /index.html  │     │  /api/v1/*  → api/index.py    │  │
│  │  /assets/*    │     │  /media/*   → api/index.py    │  │
│  └───────────────┘     │  /health    → api/index.py    │  │
│                        └────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│   AI Gateway  │      │  Tencent COS  │      │   Supabase    │
│ (ai.t8star.cn)│      │ (媒体存储)    │      │ (认证/数据库) │
└───────────────┘      └───────────────┘      └───────────────┘
```

### 核心工作流

1. **Step 1 - 概念图生成**: 输入风格 + 剧情 → AI 生成概念图
2. **Step 2 - 分镜规划**: 基于概念图 → AI 生成分镜提示词
3. **Step 3 - 分镜图生成**: 提示词 → AI 生成 2x2 分镜格子图
4. **Step 4 - 视频提示词**: 分镜 → AI 生成 Sora2 视频提示词
5. **Step 5 - 视频生成**: 调用 Sora2 API，异步轮询获取结果

---

## 💻 本地开发

### 后端 (FastAPI)

```bash
cd backend

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Windows CMD:
.\.venv\Scripts\activate.bat
# macOS/Linux:
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量 (可选，有默认值)
cp .env.example .env
# 编辑 .env 填写 AI_GATEWAY_API_KEY 等

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 前端 (Vite + React + TypeScript)

```bash
cd frontend

# 安装依赖
npm install

# 配置环境变量
cp env.example .env
# 编辑 .env:
# VITE_API_BASE_URL=http://localhost:8000/api/v1
# VITE_SUPABASE_URL=your-supabase-url
# VITE_SUPABASE_ANON_KEY=your-anon-key

# 启动开发服务器
npm run dev
```

### 环境变量参考

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `AI_GATEWAY_API_KEY` | ✅ | - | AI 网关密钥 |
| `AI_GATEWAY_BASE_URL` | ❌ | `https://ai.t8star.cn/v1` | AI 网关地址 |
| `COS_SECRET_ID` | ⚠️ | - | 腾讯云 COS 密钥 ID |
| `COS_SECRET_KEY` | ⚠️ | - | 腾讯云 COS 密钥 |
| `COS_BUCKET` | ⚠️ | - | COS 存储桶名称 |
| `COS_REGION` | ⚠️ | - | COS 地域 (如 ap-shanghai) |
| `SUPABASE_URL` | ⚠️ | - | Supabase 项目 URL |
| `SUPABASE_ANON_KEY` | ⚠️ | - | Supabase 匿名密钥 |
| `ALLOWED_ORIGINS` | ❌ | `*` | CORS 允许的来源 |
| `VIDEO_TIMEOUT_SEC` | ❌ | `180` | 视频生成超时时间 |

> ⚠️ 标记的变量在生产环境中必填

---

## 🌐 生产部署

> **详细的部署步骤请参阅 [部署指南 (DEPLOY_GUIDE.md)](./DEPLOY_GUIDE.md)**

### 快速部署到 Vercel

1. Fork 本仓库到你的 GitHub
2. 在 [Vercel](https://vercel.com) 导入项目
3. 配置环境变量
4. 点击 Deploy

### 部署清单

- [ ] Vercel 项目创建并关联 GitHub
- [ ] 环境变量配置完成
- [ ] Supabase 项目创建并配置
- [ ] 腾讯云 COS 存储桶创建
- [ ] 自定义域名配置 (可选)
- [ ] CORS 来源限制 (生产环境必须)

---

## 📚 API 文档

### 健康检查

```http
GET /health
```

响应示例：
```json
{
  "ok": true,
  "data": {
    "status": "ok",
    "env": "production",
    "timestamp": "2026-01-07T12:00:00+00:00"
  },
  "error": null
}
```

### 工作流接口

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/concept` | POST | 生成概念图 |
| `/api/v1/storyboard/plan` | POST | 规划分镜 |
| `/api/v1/storyboard/generate` | POST | 生成分镜图 |
| `/api/v1/video/prompt` | POST | 生成视频提示词 |
| `/api/v1/video/generate` | POST | 创建视频任务 |
| `/api/v1/video/status/{task_id}` | GET | 查询视频状态 |
| `/media/upload` | POST | 上传媒体文件 |

### 统一响应格式

```typescript
interface Response<T> {
  ok: boolean;
  data: T | null;
  error: {
    code: string;
    message: string;
  } | null;
}
```

---

## 📋 后续迭代计划

### 近期 (v1.1)

- [ ] **性能优化**: 前端图片懒加载、骨架屏
- [ ] **用户体验**: 工作流进度持久化、断点续传
- [ ] **监控告警**: 接入 Sentry 错误追踪

### 中期 (v1.2)

- [ ] **多租户支持**: 用户隔离、资源配额
- [ ] **BYOK (Bring Your Own Key)**: 支持用户自带 AI API Key
- [ ] **任务队列**: 使用 Redis/Upstash 管理长任务

### 长期 (v2.0)

- [ ] **模型扩展**: 支持更多视频生成模型 (Runway, Pika)
- [ ] **协作功能**: 团队工作空间、项目共享
- [ ] **移动端适配**: 响应式 UI 优化

### 技术债务清理

- [ ] 添加单元测试 (pytest + vitest)
- [ ] E2E 测试 (Playwright)
- [ ] API 文档自动生成 (OpenAPI)
- [ ] 显式声明 Pydantic 版本依赖

---

## ❓ 常见问题

### Q: 视频生成超时怎么办？

视频生成采用异步模式，`/generate` 接口立即返回 `task_id`，通过 `/status/{task_id}` 轮询获取结果。Vercel Serverless 函数超时不会影响任务执行。

### Q: 如何切换 AI 模型？

通过环境变量配置：
- `DEFAULT_TEXT_MODEL`: 文本生成模型 (默认 `gemini-3-pro-preview`)
- `DEFAULT_IMAGE_MODEL`: 图像生成模型 (默认 `nano-banana-2`)

### Q: COS 未配置时会怎样？

媒体上传接口会返回 503 错误。如果请求中包含 `source_url`，会回退到使用该 URL。

### Q: 如何添加 IP 白名单？

设置环境变量：
```
IP_ALLOWLIST_ENABLED=true
IP_ALLOWLIST=1.2.3.4,5.6.7.8
```

---

## 📄 相关文档

- [部署指南](./DEPLOY_GUIDE.md) - 详细的生产环境部署步骤
- [工作包索引](./WORKPACKS/INDEX.md) - 多 Agent 开发工作包
- [架构决策记录](./specs/) - 技术规范文档

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📜 许可

MIT License

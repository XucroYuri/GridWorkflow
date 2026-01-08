# GridWorkflow

> 🎬 AI 驱动的视频创作工作流平台 — 从创意构思到视频生成的一站式解决方案

> ⚠️ **内部项目**: 本项目为企业内部开发项目，仅供授权人员使用。

## ✨ 特性

- **四步工作流**: 概念图 → 分镜规划 → 分镜图 → 视频生成
- **AI 驱动**: 集成 Gemini、Nano-Banana、Sora2 等模型
- **Serverless 架构**: 基于 Vercel 部署，低运维成本
- **安全可靠**: Supabase 认证 + 腾讯云 COS 存储

## 🚀 快速开始

```bash
# 克隆仓库 (推荐使用 Gitee 国内源)
git clone https://gitee.com/chengdu-flower-food/grid-workflow.git
cd grid-workflow

# 或使用 GitHub
# git clone https://github.com/XucroYuri/GridWorkflow.git

# 启动后端
cd backend && python -m venv .venv && .\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 启动前端 (新终端)
cd frontend && npm install && npm run dev
```

访问 http://localhost:5173

## 📚 文档

| 文档 | 说明 |
|------|------|
| [📖 文档中心](docs/README.md) | 文档导航与项目概览 |
| [🚀 部署指南](docs/guides/DEPLOY_GUIDE.md) | 手把手教你部署到生产环境 |
| [📋 多Agent执行方案](docs/active/multi-agent/MULTI_AGENT_EXECUTION_PLAN.md) | 多 Agent 协作开发方案 |

## 🏗 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React 19 + TypeScript + Vite + Tailwind CSS |
| 后端 | FastAPI + Python 3.11+ |
| 认证 | Supabase Auth |
| 存储 | 腾讯云 COS |
| 部署 | Vercel Serverless |

## 📦 项目结构

```
GridWorkflow/
├── api/                    # Vercel Serverless 入口
│   └── index.py
├── backend/                # FastAPI 后端
│   └── app/
│       ├── api/routes/     # API 路由
│       ├── core/           # 核心配置
│       ├── schemas/        # 数据模型
│       ├── services/       # 业务逻辑
│       └── storage/        # 存储客户端
├── frontend/               # React 前端
│   └── src/
│       ├── components/     # UI 组件
│       ├── contexts/       # React Context
│       ├── pages/          # 页面组件
│       └── services/       # API 客户端
├── docs/                   # 文档
│   ├── README.md           # 项目指南
│   ├── DEPLOY_GUIDE.md     # 部署指南
│   └── WORKPACKS/          # 工作包
└── vercel.json             # Vercel 配置
```

## 🔧 环境变量

```bash
# 必填
AI_GATEWAY_API_KEY=your-api-key
VITE_SUPABASE_URL=https://xxx.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key

# 推荐 (媒体存储)
COS_SECRET_ID=your-cos-id
COS_SECRET_KEY=your-cos-key
COS_BUCKET=your-bucket
COS_REGION=ap-shanghai

# 安全 (生产环境)
ALLOWED_ORIGINS=https://yourdomain.com
```

完整变量列表见 [部署指南](docs/guides/DEPLOY_GUIDE.md#51-环境变量完整清单)

---

> ⚠️ **声明**: 本项目为企业内部开发项目，仅供内部使用，未经授权禁止对外分发。


# GridWorkflow

> 🎬 AI 驱动的视频创作工作流平台 — 从创意构思到视频生成的一站式解决方案

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/XucroYuri/GridWorkflow)

## ✨ 特性

- **四步工作流**: 概念图 → 分镜规划 → 分镜图 → 视频生成
- **AI 驱动**: 集成 Gemini、Nano-Banana、Sora2 等模型
- **一键部署**: Vercel Serverless 架构，零运维成本
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
| [📖 项目指南](docs/README.md) | 完整的功能介绍与本地开发指南 |
| [🚀 部署指南](docs/DEPLOY_GUIDE.md) | 手把手教你部署到生产环境 |
| [📋 工作包索引](docs/WORKPACKS/INDEX.md) | 多 Agent 开发文档 |

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

完整变量列表见 [部署指南](docs/DEPLOY_GUIDE.md#51-环境变量完整清单)

## 📄 许可

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！


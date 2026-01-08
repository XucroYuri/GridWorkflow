# GridWorkflow 运行测试条件与环境配置

> **版本**: 2026-01-08  
> **状态**: ✅ 可用于本地开发和生产部署

---

## 📋 目录

1. [环境要求](#1-环境要求)
2. [必需的外部服务](#2-必需的外部服务)
3. [环境变量配置](#3-环境变量配置)
4. [本地启动步骤](#4-本地启动步骤)
5. [验证测试清单](#5-验证测试清单)
6. [常见问题排查](#6-常见问题排查)

---

## 1. 环境要求

### 1.1 运行时版本

| 环境 | 最低版本 | 推荐版本 | 检查命令 |
|------|----------|----------|----------|
| **Node.js** | 18.x | 20 LTS | `node --version` |
| **npm** | 9.x | 10.x | `npm --version` |
| **Python** | 3.11.x | 3.11.x | `python --version` |
| **pip** | 23.x | 最新 | `pip --version` |
| **Git** | 2.x | 最新 | `git --version` |

### 1.2 磁盘空间

| 项目 | 大小 |
|------|------|
| 代码仓库 | ~50MB |
| Node modules | ~300MB |
| Python venv | ~100MB |
| **总计** | ~500MB |

### 1.3 网络要求

| 服务 | 域名 | 端口 |
|------|------|------|
| AI Gateway | ai.t8star.cn | 443 |
| Supabase | *.supabase.co | 443 |
| 腾讯云 COS | *.cos.*.myqcloud.com | 443 |

---

## 2. 必需的外部服务

### 2.1 AI Gateway (✅ 必需)

**用途**: 文本分析、图像生成、视频生成

**获取方式**: 
1. 联系管理员获取 API Key
2. API Key 格式: `sk-xxxxxxxx`

**验证方式**:
```bash
curl -H "Authorization: Bearer sk-your-key" https://ai.t8star.cn/v1/models
```

### 2.2 Supabase (✅ 必需)

**用途**: 用户认证、数据库存储

**创建步骤**:
1. 访问 https://supabase.com/dashboard
2. 点击 "New Project"
3. 填写项目名称和数据库密码
4. 等待项目创建完成 (~2分钟)

**获取凭据**:
- **Settings** → **API** → 复制:
  - `Project URL` → `SUPABASE_URL`
  - `anon public` → `SUPABASE_ANON_KEY`
  - `service_role` → `SUPABASE_SERVICE_ROLE_KEY` (仅后端)

**配置认证**:
- **Authentication** → **Providers** → 启用 Email

### 2.3 腾讯云 COS (⚠️ 推荐)

**用途**: 媒体文件存储 (图片、视频)

**创建步骤**:
1. 登录 https://console.cloud.tencent.com
2. 搜索 "对象存储 COS"
3. 创建存储桶:
   - 名称: `gridworkflow-media`
   - 地域: `ap-shanghai`
   - 权限: **公有读私有写**

**获取凭据**:
- **API 密钥管理** → 新建密钥 → 复制:
  - `SecretId` → `COS_SECRET_ID`
  - `SecretKey` → `COS_SECRET_KEY`

**配置 CORS** (存储桶 → 安全管理 → 跨域访问):
```json
{
  "Origin": "*",
  "Methods": ["GET", "POST", "PUT", "HEAD"],
  "AllowHeaders": ["*"],
  "ExposeHeaders": ["ETag", "Content-Length"],
  "MaxAgeSeconds": 3600
}
```

> ⚠️ 如果不配置 COS，媒体上传接口将返回 503 错误，但不影响核心工作流测试（使用外部图片 URL）。

---

## 3. 环境变量配置

### 3.1 后端环境变量

创建文件: `backend/.env`

```bash
# ==================== 必填 ====================

# AI 网关配置
AI_GATEWAY_API_KEY=sk-your-api-key-here
AI_GATEWAY_BASE_URL=https://ai.t8star.cn/v1

# Supabase 配置
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_JWT_SECRET=your-jwt-secret-from-supabase

# ==================== 推荐 ====================

# 腾讯云 COS 配置 (不配置则媒体上传不可用)
COS_SECRET_ID=AKIDxxxxxxxxxxxxx
COS_SECRET_KEY=xxxxxxxxxxxxxxxxx
COS_BUCKET=gridworkflow-media-1234567890
COS_REGION=ap-shanghai

# ==================== 可选 ====================

# 应用配置
APP_ENV=development
LOG_LEVEL=DEBUG

# CORS 配置 (开发环境可使用 *)
ALLOWED_ORIGINS=*

# IP 白名单 (开发环境一般不启用)
IP_ALLOWLIST_ENABLED=false

# 超时配置 (秒)
TEXT_TIMEOUT_SEC=10
IMAGE_TIMEOUT_SEC=30
VIDEO_TIMEOUT_SEC=180

# 轮询间隔 (毫秒)
VIDEO_POLL_INTERVAL_MS=3000

# 默认模型
DEFAULT_TEXT_MODEL=gemini-3-pro-preview
DEFAULT_IMAGE_MODEL=nano-banana-2

# COS 高级配置
COS_SIGNED_URL=false
COS_SIGNED_URL_TTL_SECONDS=300
```

### 3.2 前端环境变量

创建文件: `frontend/.env`

```bash
# API 地址 (本地开发)
VITE_API_BASE_URL=http://localhost:8000/api/v1

# Supabase 配置 (与后端相同)
VITE_SUPABASE_URL=https://your-project-id.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 3.3 环境变量清单

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `AI_GATEWAY_API_KEY` | ✅ | - | AI 网关密钥 |
| `AI_GATEWAY_BASE_URL` | ❌ | `https://ai.t8star.cn/v1` | AI 网关地址 |
| `SUPABASE_URL` | ✅ | - | Supabase URL |
| `SUPABASE_ANON_KEY` | ✅ | - | Supabase 公开密钥 |
| `SUPABASE_JWT_SECRET` | ⚠️ | - | JWT 验证密钥 (推荐) |
| `COS_SECRET_ID` | ⚠️ | - | COS 密钥 ID |
| `COS_SECRET_KEY` | ⚠️ | - | COS 密钥 |
| `COS_BUCKET` | ⚠️ | - | COS 存储桶名称 |
| `COS_REGION` | ⚠️ | - | COS 地域 |
| `ALLOWED_ORIGINS` | ❌ | `*` | CORS 允许来源 |
| `VITE_API_BASE_URL` | ✅ | - | 前端 API 地址 |
| `VITE_SUPABASE_URL` | ✅ | - | 前端 Supabase URL |
| `VITE_SUPABASE_ANON_KEY` | ✅ | - | 前端 Supabase 密钥 |

---

## 4. 本地启动步骤

### 4.1 克隆仓库

```bash
# 推荐使用 Gitee 国内源
git clone https://gitee.com/chengdu-flower-food/grid-workflow.git
cd grid-workflow

# 或使用 GitHub
# git clone https://github.com/XucroYuri/GridWorkflow.git
```

### 4.2 启动后端

```powershell
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境 (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# 安装依赖
pip install -r requirements.txt

# 创建环境配置
# 复制上面的配置到 .env 文件

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

预期输出:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx]
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 4.3 启动前端

```powershell
# 新开终端，进入前端目录
cd frontend

# 安装依赖
npm install

# 创建环境配置
# 复制上面的配置到 .env 文件

# 启动开发服务器
npm run dev
```

预期输出:
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

---

## 5. 验证测试清单

### 5.1 后端健康检查

```bash
curl http://localhost:8000/health
```

✅ 预期响应:
```json
{
  "ok": true,
  "data": {
    "status": "ok",
    "env": "development",
    "timestamp": "2026-01-08T12:00:00+00:00"
  },
  "error": null
}
```

### 5.2 前端访问

1. 打开浏览器访问 http://localhost:5173
2. 应看到登录页面

✅ 检查点:
- [ ] 页面正常加载
- [ ] 无控制台错误
- [ ] 登录表单显示

### 5.3 用户注册/登录

1. 输入邮箱和密码
2. 点击注册或登录
3. 检查 Supabase Dashboard 是否有用户记录

✅ 检查点:
- [ ] 注册成功跳转到主页
- [ ] 登录成功显示用户状态
- [ ] Supabase Auth Users 有记录

### 5.4 视频工作流测试

1. 点击导航栏 "Video Studio"
2. 填写剧情和风格
3. 点击 "生成概念图" (Step 1)

✅ 检查点:
- [ ] 概念图正常生成
- [ ] 图片正常显示
- [ ] 无 CORS 错误

### 5.5 完整流程测试

| Step | 操作 | 预期结果 |
|------|------|----------|
| 1 | 生成概念图 | 显示概念图和 Prompt |
| 2 | 规划分镜 | 显示可编辑的分镜 Prompt |
| 3 | 生成九宫格 | 显示 2x2 九宫格图 |
| 4 | 生成视频 Prompt | 显示可编辑的视频 Prompt |
| 5 | 生成视频 | 返回 task_id，开始轮询 |

### 5.6 API 测试命令

```bash
# 概念图生成
curl -X POST http://localhost:8000/api/v1/concept \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-jwt-token>" \
  -d '{"style":"Anime","plot":"Cherry blossom scene","aspect_ratio":"16:9"}'

# 视频状态查询
curl http://localhost:8000/api/v1/video/status/<task-id> \
  -H "Authorization: Bearer <your-jwt-token>"
```

---

## 6. 常见问题排查

### 6.1 后端启动失败

**症状**: `ModuleNotFoundError`

**解决**:
```bash
# 确保虚拟环境已激活
.\.venv\Scripts\Activate.ps1
# 重新安装依赖
pip install -r requirements.txt
```

### 6.2 CORS 错误

**症状**: 浏览器控制台显示 `Access-Control-Allow-Origin` 错误

**解决**:
1. 检查 `ALLOWED_ORIGINS` 环境变量
2. 确保前端访问的是 `http://localhost:5173` 而不是 `127.0.0.1`
3. 重启后端服务

### 6.3 认证失败

**症状**: 401 Unauthorized

**解决**:
1. 检查 `SUPABASE_URL` 和 `SUPABASE_ANON_KEY` 是否正确
2. 在 Supabase Dashboard 检查 Auth 配置
3. 清除浏览器 localStorage 后重新登录

### 6.4 AI 请求失败

**症状**: 502 或 500 错误

**解决**:
1. 检查 `AI_GATEWAY_API_KEY` 是否有效
2. 检查网络是否能访问 `ai.t8star.cn`
3. 查看后端日志定位具体错误

### 6.5 图片不显示

**症状**: 图片 URL 404

**解决**:
1. 如果未配置 COS，检查是否使用了外部图片 URL
2. 如果配置了 COS，检查存储桶权限是否为"公有读"
3. 检查 COS CORS 配置

### 6.6 视频生成卡住

**症状**: 任务状态一直 "running"

**解决**:
1. AI 视频生成需要时间 (1-5分钟)
2. 检查 task_id 是否有效
3. 通过 `/video/status/{task_id}` 查看详细状态

---

## 7. 开发者快速启动脚本

### Windows PowerShell

创建文件: `start-dev.ps1`

```powershell
# GridWorkflow 快速启动脚本

Write-Host "Starting GridWorkflow Development Environment..." -ForegroundColor Cyan

# 检查 Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Python not found!" -ForegroundColor Red
    exit 1
}

# 检查 Node
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Node.js not found!" -ForegroundColor Red
    exit 1
}

# 启动后端
Write-Host "Starting Backend..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; .\.venv\Scripts\Activate.ps1; uvicorn app.main:app --reload --port 8000"

# 等待后端启动
Start-Sleep -Seconds 3

# 启动前端
Write-Host "Starting Frontend..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"

Write-Host "Development servers started!" -ForegroundColor Green
Write-Host "Backend: http://localhost:8000" -ForegroundColor Cyan
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Cyan
```

运行: `.\start-dev.ps1`

---

**文档维护者**: AI Architect  
**最后更新**: 2026-01-08


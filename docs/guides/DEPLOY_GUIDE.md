# GridWorkflow 部署指南

> 本指南面向零基础用户，详细介绍如何将 GridWorkflow 部署到生产环境。

---

## 📋 目录

1. [准备工作](#1-准备工作)
2. [创建 Supabase 项目](#2-创建-supabase-项目)
3. [创建腾讯云 COS 存储桶](#3-创建腾讯云-cos-存储桶)
4. [部署到 Vercel](#4-部署到-vercel)
5. [配置环境变量](#5-配置环境变量)
6. [验证部署](#6-验证部署)
7. [自定义域名配置](#7-自定义域名配置可选)
8. [生产环境安全加固](#8-生产环境安全加固)
9. [故障排查](#9-故障排查)

---

## 1. 准备工作

### 1.1 所需账号

在开始之前，请确保你拥有以下账号：

| 服务 | 用途 | 注册地址 |
|------|------|----------|
| **GitHub** | 代码托管 | https://github.com |
| **Vercel** | 前后端部署 | https://vercel.com |
| **Supabase** | 用户认证 & 数据库 | https://supabase.com |
| **腾讯云** | 媒体文件存储 (COS) | https://cloud.tencent.com |

### 1.2 获取 AI Gateway API Key

你需要一个 AI 网关的 API Key 来使用文本/图像/视频生成功能。

默认使用 `ai.t8star.cn` 网关，请联系管理员获取 API Key。

---

## 2. 创建 Supabase 项目

Supabase 提供用户认证和数据库服务。

### 2.1 创建项目

1. 访问 [Supabase Dashboard](https://supabase.com/dashboard)
2. 点击 **New Project**
3. 填写项目信息：
   - **Name**: `gridworkflow` (或你喜欢的名称)
   - **Database Password**: 设置一个强密码并妥善保存
   - **Region**: 选择离你最近的地域 (如 `Northeast Asia (Tokyo)`)
4. 点击 **Create new project**
5. 等待项目创建完成 (约 2 分钟)

### 2.2 获取项目凭据

项目创建完成后：

1. 进入 **Settings** → **API**
2. 记录以下信息 (后面配置环境变量需要)：

```
Project URL:        https://xxxxxxxxx.supabase.co
anon public key:    eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
service_role key:   eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9... (保密!)
```

### 2.3 配置认证提供商

1. 进入 **Authentication** → **Providers**
2. 启用 **Email** 登录 (默认已启用)
3. 可选：启用 **Google**、**GitHub** 等社交登录

### 2.4 获取 JWT 密钥 (可选但推荐)

1. 进入 **Settings** → **API**
2. 滚动到 **JWT Settings**
3. 记录 **JWT Secret** (用于后端验证 Token)

---

## 3. 创建腾讯云 COS 存储桶

腾讯云 COS 用于存储用户上传的图片和生成的视频。

### 3.1 创建存储桶

1. 登录 [腾讯云控制台](https://console.cloud.tencent.com)
2. 搜索并进入 **对象存储 COS**
3. 点击 **创建存储桶**
4. 填写配置：

| 配置项 | 推荐值 | 说明 |
|--------|--------|------|
| 名称 | `gridworkflow-media` | 自定义，全局唯一 |
| 地域 | `ap-shanghai` | 选择离用户最近的地域 |
| 访问权限 | **公有读私有写** | 允许公开访问媒体文件 |
| 版本控制 | 关闭 | 可选开启 |

5. 点击 **创建**

### 3.2 配置 CORS 跨域

1. 进入存储桶 → **安全管理** → **跨域访问 CORS**
2. 点击 **添加规则**
3. 填写：

```
来源 Origin:       *
操作 Methods:      GET, POST, PUT, HEAD
Allow-Headers:     *
Expose-Headers:    ETag, Content-Length
超时 Max-Age:      3600
```

> ⚠️ 生产环境应将 `Origin` 限制为你的域名

### 3.3 获取 API 密钥

1. 访问 [API 密钥管理](https://console.cloud.tencent.com/cam/capi)
2. 点击 **新建密钥**
3. 记录：

```
SecretId:   <你的SecretId>
SecretKey:  <你的SecretKey> (保密!)
```

### 3.4 记录存储桶信息

在存储桶概览页面记录：

```
存储桶名称: gridworkflow-media-1234567890
地域:      ap-shanghai
```

---

## 4. 部署到 Vercel

### 4.1 仓库说明

> ⚠️ 本项目为企业内部项目，请确保有仓库访问权限。

**仓库性质**:
- **Gitee**: 内部开发主仓库，所有日常开发在此进行
- **GitHub**: 快速部署临时仓库，仅用于 Vercel 等平台部署

**仓库地址**:
- Gitee (主): https://gitee.com/chengdu-flower-food/grid-workflow
- GitHub (部署): https://github.com/huachi-design/GridWorkflow

### 4.2 导入到 Vercel

> ⚠️ **重要**: Vercel 部署需要使用 GitHub 仓库（快速部署临时仓库）

1. 访问 [Vercel Dashboard](https://vercel.com/dashboard)
2. 点击 **Add New** → **Project**
3. 选择 **Import Git Repository**
4. 关联 GitHub 账号，选择 `GridWorkflow` 仓库，点击 **Import**
5. **部署前确保代码已从 Gitee 同步到 GitHub**（使用 `git push github main` 或 `git push all main`）

### 4.3 配置构建设置

Vercel 会自动检测项目配置，确认以下设置：

| 配置项 | 值 |
|--------|-----|
| Framework Preset | Other |
| Build Command | `cd frontend && npm install && npm run build` |
| Output Directory | `frontend/dist` |
| Install Command | (留空) |

### 4.4 添加环境变量

在 **Environment Variables** 部分添加以下变量：

#### 必填变量

| 变量名 | 示例值 | 说明 |
|--------|--------|------|
| `AI_GATEWAY_API_KEY` | `sk-xxxxxxxx` | AI 网关密钥 |
| `VITE_SUPABASE_URL` | `https://xxx.supabase.co` | Supabase URL |
| `VITE_SUPABASE_ANON_KEY` | `eyJhbGci...` | Supabase 公开密钥 |
| `SUPABASE_URL` | `https://xxx.supabase.co` | 后端用 Supabase URL |
| `SUPABASE_ANON_KEY` | `eyJhbGci...` | 后端用 Supabase 密钥 |

#### COS 存储变量 (推荐)

| 变量名 | 示例值 | 说明 |
|--------|--------|------|
| `COS_SECRET_ID` | `<你的SecretId>` | 腾讯云密钥 ID |
| `COS_SECRET_KEY` | `xxxxx` | 腾讯云密钥 |
| `COS_BUCKET` | `gridworkflow-media-1234567890` | 存储桶名称 |
| `COS_REGION` | `ap-shanghai` | 存储桶地域 |

#### 安全变量 (生产环境必填)

| 变量名 | 示例值 | 说明 |
|--------|--------|------|
| `ALLOWED_ORIGINS` | `https://yourdomain.com` | CORS 允许的来源 |
| `SUPABASE_JWT_SECRET` | `your-jwt-secret` | JWT 验证密钥 |

### 4.5 部署

1. 确认所有环境变量已添加
2. 点击 **Deploy**
3. 等待部署完成 (约 2-3 分钟)

部署成功后，Vercel 会提供一个类似 `https://gridworkflow-xxx.vercel.app` 的访问地址。

---

## 5. 配置环境变量

### 5.1 环境变量完整清单

以下是所有支持的环境变量：

```bash
# ==================== 必填 ====================

# AI 网关配置
AI_GATEWAY_API_KEY=sk-your-api-key
AI_GATEWAY_BASE_URL=https://ai.t8star.cn/v1  # 可选，有默认值

# Supabase 配置 (前端)
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Supabase 配置 (后端)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# ==================== 推荐 ====================

# 腾讯云 COS 配置
COS_SECRET_ID=<你的SecretId>
COS_SECRET_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
COS_BUCKET=your-bucket-name-appid
COS_REGION=ap-shanghai

# ==================== 安全加固 ====================

# CORS 来源限制 (生产环境必须设置!)
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# JWT 验证 (推荐)
SUPABASE_JWT_SECRET=your-jwt-secret

# IP 白名单 (可选)
IP_ALLOWLIST_ENABLED=false
IP_ALLOWLIST=1.2.3.4,5.6.7.8

# ==================== 可选调优 ====================

# 应用配置
APP_ENV=production
LOG_LEVEL=INFO

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
COS_SIGNED_URL=false          # 是否使用签名 URL
COS_SIGNED_URL_TTL_SECONDS=300
COS_MEDIA_PREFIX=media
COS_IMAGE_MAX_BYTES=10485760  # 10MB
COS_VIDEO_MAX_BYTES=104857600 # 100MB
```

### 5.2 在 Vercel 中修改环境变量

1. 进入 Vercel 项目 → **Settings** → **Environment Variables**
2. 添加或修改变量
3. 点击 **Save**
4. **重要**: 需要重新部署才能生效
   - 进入 **Deployments** → 点击最新部署的 **...** → **Redeploy**

---

## 6. 验证部署

### 6.1 健康检查

访问以下 URL 验证后端是否正常：

```
https://your-vercel-domain.vercel.app/health
```

预期响应：
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

### 6.2 前端访问

访问 Vercel 分配的域名，应该能看到登录页面。

### 6.3 完整流程测试

1. 注册/登录账号
2. 进入视频工作台
3. 填写风格和剧情
4. 依次执行 Step 1-5
5. 等待视频生成完成

### 6.4 常见检查点

| 检查项 | 如何验证 |
|--------|----------|
| 后端 API | `/health` 返回 200 |
| Supabase 认证 | 可以注册/登录 |
| AI 网关 | Step 1 能生成概念图 |
| COS 存储 | 图片/视频能正常显示 |

---

## 7. 自定义域名配置 (可选)

### 7.1 在 Vercel 添加域名

1. 进入项目 → **Settings** → **Domains**
2. 输入你的域名，如 `app.yourdomain.com`
3. 点击 **Add**

### 7.2 配置 DNS

Vercel 会提供 DNS 配置指引，通常需要添加：

| 类型 | 名称 | 值 |
|------|------|-----|
| CNAME | `app` | `cname.vercel-dns.com` |

或者使用 A 记录：

| 类型 | 名称 | 值 |
|------|------|-----|
| A | `@` | `76.76.21.21` |

### 7.3 等待 DNS 生效

- DNS 变更通常需要 5-30 分钟生效
- 可以使用 [whatsmydns.net](https://www.whatsmydns.net) 检查传播状态

### 7.4 更新 CORS 配置

添加自定义域名后，**必须** 更新 `ALLOWED_ORIGINS`：

```
ALLOWED_ORIGINS=https://app.yourdomain.com,https://yourdomain.com
```

---

## 8. 生产环境安全加固

### 8.1 CORS 限制

**绝对不要** 在生产环境使用 `ALLOWED_ORIGINS=*`！

正确配置：
```
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

### 8.2 API Key 安全

- 所有密钥必须通过环境变量注入
- 定期轮换 API Key
- 使用最小权限原则

### 8.3 Supabase 安全配置

1. 进入 **Authentication** → **URL Configuration**
2. 设置 **Site URL**: `https://yourdomain.com`
3. 添加 **Redirect URLs**: `https://yourdomain.com/*`

### 8.4 COS 安全配置

1. 更新 CORS 规则，限制 `Origin` 为你的域名
2. 考虑启用签名 URL (`COS_SIGNED_URL=true`)
3. 设置存储桶生命周期规则，自动清理临时文件

### 8.5 监控与告警

推荐接入：
- **Vercel Analytics**: 自带，免费
- **Sentry**: 错误追踪
- **Uptime Robot**: 可用性监控

---

## 9. 故障排查

### 9.1 部署失败

**症状**: Vercel 构建报错

**排查步骤**:
1. 查看 Vercel 构建日志
2. 常见错误：
   - `Module not found`: 检查依赖是否正确安装
   - `TypeScript error`: 检查类型定义
   - `Python syntax error`: 检查 Python 版本

### 9.2 后端 500 错误

**症状**: API 调用返回 500

**排查步骤**:
1. 查看 Vercel **Functions** 日志
2. 检查环境变量是否正确设置
3. 确认 AI Gateway API Key 有效

### 9.3 CORS 错误

**症状**: 浏览器控制台显示 CORS 错误

**解决方案**:
1. 检查 `ALLOWED_ORIGINS` 是否包含当前域名
2. 确保不包含尾部斜杠
3. 重新部署使环境变量生效

### 9.4 认证失败

**症状**: 登录后仍显示未认证

**排查步骤**:
1. 检查 `VITE_SUPABASE_URL` 和 `VITE_SUPABASE_ANON_KEY`
2. 检查 Supabase **URL Configuration** 设置
3. 清除浏览器缓存和 Cookie

### 9.5 媒体文件无法访问

**症状**: 图片/视频显示不出来

**排查步骤**:
1. 检查 COS 存储桶是否为公有读
2. 检查 COS CORS 配置
3. 检查 COS API 密钥权限

### 9.6 视频生成卡住

**症状**: 视频状态一直是 "处理中"

**可能原因**:
1. 上游 AI 服务繁忙
2. 任务已失败但状态未更新

**解决方案**:
1. 查看 `/api/v1/video/status/{task_id}` 返回的详细状态
2. 等待一段时间后重试
3. 检查 AI Gateway 配额

---

## 📞 获取帮助

如果以上步骤仍无法解决问题：

1. 查看 Issues：
   - [Gitee Issues](https://gitee.com/chengdu-flower-food/grid-workflow/issues) (国内优先)
   - [GitHub Issues](https://github.com/huachi-design/GridWorkflow/issues)
2. 提交新 Issue，附上：
   - 错误截图
   - Vercel 构建/函数日志
   - 浏览器控制台错误
3. 联系项目维护者

---

## 🎉 恭喜！

如果你已经完成了以上所有步骤，你的 GridWorkflow 应该已经在生产环境运行了。

**下一步**:
- 邀请团队成员测试
- 配置监控告警
- 根据使用情况调整资源配置

祝你使用愉快！ 🚀


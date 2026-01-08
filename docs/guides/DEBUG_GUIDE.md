# GridWorkflow 调试指导手册

**版本**: v1.0  
**更新日期**: 2026-01-07  
**适用范围**: 开发环境 & 生产环境  

---

## 📋 目录

1. [调试环境准备](#1-调试环境准备)
2. [日志系统](#2-日志系统)
3. [后端调试](#3-后端调试)
4. [前端调试](#4-前端调试)
5. [API 调试](#5-api-调试)
6. [常见问题排查](#6-常见问题排查)
7. [性能调试](#7-性能调试)
8. [生产环境调试](#8-生产环境调试)

---

## 1. 调试环境准备

### 1.1 开发环境配置

```bash
# 后端环境
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 前端环境
cd frontend
npm install
```

### 1.2 环境变量配置

创建 `.env` 文件用于本地调试：

```bash
# backend/.env
APP_ENV=development
LOG_LEVEL=DEBUG                    # 调试时设为 DEBUG
AI_GATEWAY_BASE_URL=https://ai.t8star.cn/v1
AI_GATEWAY_API_KEY=your-api-key
SUPABASE_URL=your-supabase-url
SUPABASE_JWT_SECRET=your-jwt-secret
CORS_ALLOW_ORIGINS=http://localhost:5173

# frontend/.env.local
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_SUPABASE_URL=your-supabase-url
VITE_SUPABASE_ANON_KEY=your-anon-key
```

### 1.3 启动调试服务

```bash
# 终端 1: 启动后端 (开启热重载)
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 终端 2: 启动前端
cd frontend
npm run dev
```

---

## 2. 日志系统

### 2.1 日志格式

项目使用统一的日志格式：

```
2026-01-07 10:30:45,123 | INFO | gridworkflow | request completed request_id=abc-123 step=concept model=gpt-4o latency_ms=1523.45
```

| 字段 | 说明 |
|------|------|
| `timestamp` | 时间戳 |
| `level` | 日志级别 (DEBUG/INFO/WARNING/ERROR) |
| `name` | Logger 名称 (gridworkflow) |
| `message` | 日志内容 |

### 2.2 日志级别使用

```python
# backend/app/core/logger.py
from app.core.logger import get_logger
from app.core.config import get_settings

settings = get_settings()
logger = get_logger(settings.log_level)

# 使用示例
logger.debug("详细调试信息: payload=%s", payload)   # 开发环境
logger.info("请求完成: request_id=%s", request_id)  # 常规记录
logger.warning("配额接近上限: usage=%d", usage)      # 警告
logger.error("外部服务调用失败: %s", str(exc))       # 错误
logger.exception("未处理的异常")                     # 异常（含堆栈）
```

### 2.3 调试日志开关

```bash
# 开启详细日志
export LOG_LEVEL=DEBUG

# 生产环境
export LOG_LEVEL=INFO
```

### 2.4 关键日志追踪

每个请求都会生成唯一的 `request_id`，用于追踪完整请求链路：

```python
# 在 main.py 中自动注入
request_id = str(uuid4())
request.state.request_id = request_id

# 响应头中返回
response.headers["X-Request-ID"] = request_id
```

**追踪示例：**
```bash
# 根据 request_id 搜索日志
grep "request_id=abc-123" logs/app.log
```

---

## 3. 后端调试

### 3.1 FastAPI 交互式文档

启动后端后访问：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 3.2 断点调试 (VS Code)

创建 `.vscode/launch.json`：

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI Debug",
      "type": "debugpy",
      "request": "launch",
      "module": "uvicorn",
      "args": ["app.main:app", "--reload", "--port", "8000"],
      "jinja": true,
      "cwd": "${workspaceFolder}/backend",
      "env": {
        "LOG_LEVEL": "DEBUG"
      }
    }
  ]
}
```

### 3.3 Services 调试

#### AI Service 调试

```python
# backend/app/services/ai_service.py

async def analyze_text(payload: AnalyzeRequest, user_key: Optional[str], settings: Settings):
    # 添加调试日志
    logger.debug("analyze_text 开始: prompt=%s, model=%s", 
                 payload.prompt[:50], payload.model)
    
    try:
        response = await client.post(url, json=request_body, headers=headers)
        logger.debug("AI Gateway 响应: status=%d, body=%s", 
                     response.status_code, response.text[:200])
    except httpx.TimeoutException as exc:
        logger.error("AI Gateway 超时: %s", str(exc))
        raise APIError(code="TIMEOUT", message="请求超时", status_code=504)
```

#### Video Service 调试

```python
# backend/app/services/video_service.py

class T8StarVideoProvider:
    async def generate(self, payload: dict, user_key: str | None = None):
        logger.debug("T8Star generate: model=%s, prompt=%s...", 
                     payload.get("model"), payload.get("prompt", "")[:50])
        
        # 记录上游响应
        logger.debug("T8Star 响应: %s", response.text)
```

### 3.4 异常调试

项目定义了多种自定义异常：

```python
# APIError - 业务逻辑错误
from app.services.ai_service import APIError
raise APIError(code="BAD_REQUEST", message="参数无效", status_code=400)

# AuthError - 认证错误
from app.core.auth import AuthError
raise AuthError("Token 已过期")

# UpstreamServiceError - 上游服务错误
from app.services.video_service import UpstreamServiceError
raise UpstreamServiceError(code="UPSTREAM_ERROR", message="上游服务异常", status_code=502)
```

### 3.5 数据库/Supabase 调试

```python
# 添加 Supabase 客户端调试
from supabase import create_client

client = create_client(url, key)

# 查询调试
result = client.table('workflow_sessions').select('*').eq('user_id', user_id).execute()
logger.debug("Supabase 查询结果: %s", result.data)
```

---

## 4. 前端调试

### 4.1 浏览器开发者工具

#### Console 面板

```typescript
// 添加调试日志
console.log('[GridWorkflow] 当前状态:', state);
console.log('[API] 请求参数:', payload);
console.error('[Error] 接口调用失败:', error);

// 使用 console.table 查看数组/对象
console.table(tasks);

// 使用 console.group 分组日志
console.group('工作流步骤');
console.log('Step 1: Concept');
console.log('Step 2: Storyboard');
console.groupEnd();
```

#### Network 面板

检查点：
- **Request Headers**: 确认 `Authorization` 携带正确的 JWT
- **Request Payload**: 确认请求参数格式正确
- **Response**: 查看后端返回的错误信息
- **Timing**: 分析请求耗时

### 4.2 React DevTools

安装 [React Developer Tools](https://chrome.google.com/webstore/detail/react-developer-tools) 扩展：

- **Components**: 查看组件树和 props/state
- **Profiler**: 分析组件渲染性能

### 4.3 状态调试

```tsx
// GridWorkflow.tsx - 添加状态调试

const [state, setState] = useState<WorkflowState>(INITIAL_STATE);

// 状态变化时打印
useEffect(() => {
  console.log('[WorkflowState] 状态更新:', {
    step: state.step,
    isLoading: state.isLoading,
    error: state.error,
  });
}, [state]);

// 调试 hooks
const { session, loading } = useAuth();
useEffect(() => {
  console.log('[Auth] session:', session?.user?.email, 'loading:', loading);
}, [session, loading]);
```

### 4.4 API 调用调试

```typescript
// frontend/src/services/apiClient.ts

// 请求拦截器添加调试
apiClient.interceptors.request.use(
  async (config) => {
    console.log('[API Request]', config.method?.toUpperCase(), config.url);
    console.log('[API Request] Headers:', config.headers);
    console.log('[API Request] Data:', config.data);
    
    const { data: { session } } = await supabase.auth.getSession();
    if (session?.access_token) {
      config.headers.Authorization = `Bearer ${session.access_token}`;
      console.log('[API Request] Token:', session.access_token.slice(0, 20) + '...');
    }
    return config;
  },
  (error) => {
    console.error('[API Request Error]', error);
    return Promise.reject(error);
  }
);

// 响应拦截器添加调试
apiClient.interceptors.response.use(
  (response) => {
    console.log('[API Response]', response.config.url, response.status);
    console.log('[API Response] Data:', response.data);
    return response.data;
  },
  (error) => {
    console.error('[API Response Error]', {
      url: error.config?.url,
      status: error.response?.status,
      data: error.response?.data,
    });
    return Promise.reject(error);
  }
);
```

### 4.5 Supabase Auth 调试

```typescript
// 查看当前 session
const { data: { session } } = await supabase.auth.getSession();
console.log('[Supabase] Session:', session);
console.log('[Supabase] User:', session?.user);
console.log('[Supabase] Token expires:', new Date(session?.expires_at * 1000));

// 监听 auth 状态变化
supabase.auth.onAuthStateChange((event, session) => {
  console.log('[Supabase Auth Event]', event, session?.user?.email);
});
```

---

## 5. API 调试

### 5.1 使用 cURL

```bash
# 获取 Supabase token (从浏览器开发者工具复制)
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# 测试 concept 接口
curl -X POST http://localhost:8000/api/v1/concept \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "style": "Anime style",
    "plot": "樱花树下的少女",
    "aspect_ratio": "16:9"
  }'

# 测试视频生成
curl -X POST http://localhost:8000/api/v1/video/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "prompt": "A girl walking under cherry blossoms",
    "model": "sora-2",
    "aspect_ratio": "16:9",
    "duration": 5
  }'

# 查询任务状态
curl http://localhost:8000/api/v1/video/status/task-id-123 \
  -H "Authorization: Bearer $TOKEN"
```

### 5.2 使用 HTTPie (更友好)

```bash
# 安装
pip install httpie

# 测试接口
http POST localhost:8000/api/v1/concept \
  Authorization:"Bearer $TOKEN" \
  style="Anime style" \
  plot="樱花树下的少女" \
  aspect_ratio="16:9"
```

### 5.3 使用 Postman/Insomnia

导入 OpenAPI 规范：
1. 访问 http://localhost:8000/openapi.json
2. 导入到 Postman/Insomnia
3. 设置环境变量 `{{token}}` 和 `{{base_url}}`

### 5.4 请求追踪

每个响应都包含 `X-Request-ID` 头，用于追踪：

```bash
# 获取 request_id
curl -i http://localhost:8000/api/v1/concept ... 2>&1 | grep X-Request-ID
# X-Request-ID: abc-123-def-456

# 在后端日志中搜索
grep "request_id=abc-123-def-456" logs/app.log
```

---

## 6. 常见问题排查

### 6.1 认证问题

#### 问题：401 Unauthorized

```json
{"ok": false, "error": {"code": "UNAUTHORIZED", "message": "鉴权失败"}}
```

**排查步骤：**

```bash
# 1. 检查 token 是否存在
# 浏览器 Console:
const { data: { session } } = await supabase.auth.getSession();
console.log(session?.access_token);

# 2. 检查 token 是否过期
# 解析 JWT (https://jwt.io)
# 查看 exp 字段

# 3. 检查后端 JWT Secret 配置
# backend/.env
SUPABASE_JWT_SECRET=your-secret

# 4. 查看后端日志
grep "UNAUTHORIZED" logs/app.log
```

#### 问题：Token 刷新失败

```typescript
// 手动刷新 token
const { data, error } = await supabase.auth.refreshSession();
if (error) {
  console.error('Token 刷新失败:', error);
  // 重新登录
  await supabase.auth.signOut();
}
```

### 6.2 CORS 问题

#### 问题：跨域请求被阻止

```
Access to XMLHttpRequest at 'http://localhost:8000/api/v1/concept' 
from origin 'http://localhost:5173' has been blocked by CORS policy
```

**排查步骤：**

```bash
# 1. 检查后端 CORS 配置
# backend/.env
CORS_ALLOW_ORIGINS=http://localhost:5173,http://localhost:3000

# 2. 验证 CORS 中间件
# main.py 中确认 allow_origins 正确

# 3. 重启后端服务
uvicorn app.main:app --reload
```

### 6.3 API 调用失败

#### 问题：502 Bad Gateway / UPSTREAM_ERROR

```json
{"ok": false, "error": {"code": "UPSTREAM_ERROR", "message": "上游服务异常"}}
```

**排查步骤：**

```bash
# 1. 检查 AI Gateway 配置
# backend/.env
AI_GATEWAY_BASE_URL=https://ai.t8star.cn/v1
AI_GATEWAY_API_KEY=your-key

# 2. 测试上游服务连通性
curl https://ai.t8star.cn/v1/models \
  -H "Authorization: Bearer your-key"

# 3. 查看详细错误日志
grep "UPSTREAM_ERROR" logs/app.log -A 5

# 4. 检查超时配置
# backend/app/core/config.py
text_timeout_sec: int = 120
image_timeout_sec: int = 180
```

#### 问题：504 Gateway Timeout

```json
{"ok": false, "error": {"code": "TIMEOUT", "message": "请求超时"}}
```

**排查步骤：**

```bash
# 1. 检查超时设置
# backend/app/core/config.py
text_timeout_sec = 120   # 增大超时时间
image_timeout_sec = 180

# 2. 检查网络连接
ping ai.t8star.cn

# 3. 前端也要调整超时
# frontend/src/services/apiClient.ts
timeout: 180000,  // 3 分钟
```

### 6.4 视频生成问题

#### 问题：任务一直 pending/running

**排查步骤：**

```bash
# 1. 检查任务 ID 格式
# 有效格式: 字母数字和短横线

# 2. 查询任务状态
curl http://localhost:8000/api/v1/video/status/$TASK_ID \
  -H "Authorization: Bearer $TOKEN"

# 3. 检查上游任务状态
# 可能需要直接调用 T8Star API 确认

# 4. 查看后端日志
grep "task_id=$TASK_ID" logs/app.log
```

### 6.5 图片/媒体问题

#### 问题：图片上传失败

**排查步骤：**

```bash
# 1. 检查 COS 配置
# backend/.env
COS_SECRET_ID=your-id
COS_SECRET_KEY=your-key
COS_BUCKET=your-bucket
COS_REGION=ap-guangzhou

# 2. 检查 Base64 格式
# 有效格式: data:image/png;base64,iVBORw0KGgo...

# 3. 检查文件大小
# 默认限制可能需要调整

# 4. 查看 COS 错误日志
grep "COS" logs/app.log | grep -i error
```

---

## 7. 性能调试

### 7.1 后端性能分析

```python
# 使用 cProfile
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()
# ... 要分析的代码
profiler.disable()
stats = pstats.Stats(profiler).sort_stats('cumulative')
stats.print_stats(10)

# 或使用装饰器
import time
from functools import wraps

def timing(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = await func(*args, **kwargs)
        duration = (time.perf_counter() - start) * 1000
        logger.info("%s 耗时: %.2fms", func.__name__, duration)
        return result
    return wrapper

@timing
async def analyze_text(...):
    ...
```

### 7.2 前端性能分析

```typescript
// 使用 Performance API
const start = performance.now();
await videoService.generateConcept(style, plot, anchors);
const duration = performance.now() - start;
console.log(`generateConcept 耗时: ${duration.toFixed(2)}ms`);

// 使用 React Profiler
import { Profiler } from 'react';

<Profiler id="GridWorkflow" onRender={(id, phase, actualDuration) => {
  console.log(`${id} ${phase} 渲染耗时: ${actualDuration.toFixed(2)}ms`);
}}>
  <GridWorkflow />
</Profiler>
```

### 7.3 请求耗时分析

后端日志自动记录每个请求的耗时：

```
request completed request_id=abc-123 step=concept model=gpt-4o latency_ms=1523.45
```

批量分析：

```bash
# 统计各步骤平均耗时
grep "request completed" logs/app.log | \
  awk -F'step=' '{print $2}' | \
  awk -F' ' '{step[$1]++; sum[$1]+=$3} END {for (s in step) print s, sum[s]/step[s]}'
```

---

## 8. 生产环境调试

### 8.1 Vercel 日志

```bash
# 安装 Vercel CLI
npm i -g vercel

# 查看实时日志
vercel logs your-project.vercel.app --follow

# 查看部署日志
vercel logs your-project.vercel.app --since 1h
```

### 8.2 远程调试技巧

#### 添加调试端点（仅开发/测试环境）

```python
# backend/app/api/routes/health.py

@router.get("/debug/config")
async def debug_config(settings: Settings = Depends(get_settings)):
    """仅在非生产环境可用"""
    if settings.env == "production":
        raise HTTPException(403, "Not available in production")
    
    return {
        "env": settings.env,
        "ai_gateway_base_url": settings.ai_gateway_base_url,
        "cors_origins": settings.cors_allow_origins,
        # 不要暴露敏感信息如 API Key
    }
```

#### 临时启用详细日志

```bash
# Vercel 环境变量临时修改
vercel env add LOG_LEVEL development
# 设置为 DEBUG

# 问题解决后恢复
vercel env add LOG_LEVEL production
# 设置回 INFO
```

### 8.3 错误追踪 (Sentry)

如果已集成 Sentry，可以：

```python
import sentry_sdk

# 手动上报错误
sentry_sdk.capture_exception(exc)

# 添加上下文
sentry_sdk.set_context("request", {
    "request_id": request_id,
    "user_id": user_id,
    "step": step,
})

# 添加面包屑
sentry_sdk.add_breadcrumb(
    category="api",
    message=f"调用 {endpoint}",
    level="info",
)
```

### 8.4 健康检查

```bash
# 检查服务健康状态
curl https://your-api.vercel.app/health

# 预期响应
{"status": "ok", "version": "1.0.0"}
```

---

## 📎 附录

### A. 调试工具清单

| 工具 | 用途 | 安装 |
|------|------|------|
| VS Code + Debugpy | Python 断点调试 | 内置 |
| React DevTools | React 组件调试 | Chrome 扩展 |
| Postman/Insomnia | API 测试 | 独立应用 |
| HTTPie | 命令行 API 测试 | `pip install httpie` |
| jq | JSON 格式化 | `brew install jq` |

### B. 常用调试命令

```bash
# 查看日志尾部
tail -f logs/app.log

# 搜索错误
grep -i error logs/app.log | tail -20

# 按 request_id 追踪
grep "request_id=abc-123" logs/app.log

# 统计错误类型
grep "error" logs/app.log | awk -F'code=' '{print $2}' | sort | uniq -c | sort -rn

# 查看慢请求 (>3000ms)
grep "latency_ms=" logs/app.log | awk -F'latency_ms=' '{if ($2 > 3000) print}'
```

### C. 调试检查清单

开始调试前确认：

- [ ] 环境变量正确配置
- [ ] 后端服务正常启动
- [ ] 前端能连接后端
- [ ] Supabase 认证正常
- [ ] 日志级别设为 DEBUG
- [ ] 浏览器开发者工具已打开

---

**维护者**: GridWorkflow Team  
**最后更新**: 2026-01-07



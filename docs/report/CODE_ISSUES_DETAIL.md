# GridWorkflow 代码问题详细清单

**生成日期**: 2026-01-07  
**关联报告**: CODE_AUDIT_REPORT_2026-01-07.md  

---

## 🔴 严重问题修复指南

### S1: listTasks 后端未实现

**问题描述**: 前端调用 `videoService.listTasks()` 但后端无对应端点

**影响范围**:
- `frontend/src/pages/VideoStudio.tsx:13-28`
- `frontend/src/services/videoService.ts:114-129`

**当前代码**:
```typescript
// videoService.ts
listTasks: async () => {
  // 注释说明后端未实现
  return [] as VideoTask[];
},
```

**修复方案 A** (临时): 前端移除调用
```typescript
// VideoStudio.tsx - 移除 fetchTasks 轮询
// 只在 GridWorkflow 生成任务后手动刷新
```

**修复方案 B** (推荐): 后端实现端点
```python
# backend/app/api/routes/video.py

@router.get("/tasks", dependencies=[Depends(require_user)])
async def list_user_tasks(
    request: Request,
    settings: Settings = Depends(get_settings),
    user_id: str = Depends(require_user),
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
) -> JSONResponse:
    """获取当前用户的视频任务列表"""
    # TODO: 需要实现持久化层
    # 临时返回空列表
    return JSONResponse(
        status_code=200,
        content=success_response({"tasks": [], "total": 0}),
    )
```

---

### S2: task.progress 属性未定义

**问题描述**: `VideoTask` 接口缺少 `progress` 字段，但 UI 中使用

**影响范围**:
- `frontend/src/components/video/TaskList.tsx:67`
- `frontend/src/components/video/VideoPreview.tsx:42`

**问题代码**:
```typescript
// TaskList.tsx:67
{getStatusText(task.status, task.progress)}

// VideoPreview.tsx:42
<p className="text-sm opacity-60">
  {task.status === 'queued' ? '正在排队...' : `进度: ${task.progress}%`}
</p>
```

**修复方案**:
```typescript
// videoService.ts - 添加 progress 字段
export interface VideoTask {
  task_id: string;
  status: 'queued' | 'running' | 'succeeded' | 'failed';
  prompt?: string;
  created_at?: number;
  video_url?: string;
  error_message?: string | null;
  provider?: string;
  progress?: number;  // 添加此行
}

// TaskList.tsx - 安全访问
{getStatusText(task.status, task.progress ?? 0)}

// VideoPreview.tsx - 安全访问
{task.status === 'queued' ? '正在排队...' : `进度: ${task.progress ?? 0}%`}
```

---

### S3: CORS 默认配置过于宽松

**问题描述**: 默认允许所有源访问 API

**问题代码**:
```python
# main.py:20-25
def _parse_cors_origins(raw: str) -> list[str]:
    if not raw:
        return ["*"]  # 危险：默认允许所有源
    if raw.strip() == "*":
        return ["*"]
    return [origin.strip() for origin in raw.split(",") if origin.strip()]
```

**修复方案**:
```python
# 方案 A: 生产环境强制配置
def _parse_cors_origins(raw: str, env: str) -> list[str]:
    if env.lower() == "production" and not raw:
        raise ValueError("CORS_ALLOW_ORIGINS must be set in production")
    if not raw:
        return ["http://localhost:5173", "http://localhost:3000"]  # 开发环境默认
    if raw.strip() == "*":
        return ["*"]
    return [origin.strip() for origin in raw.split(",") if origin.strip()]

# 方案 B: 环境变量配置
# .env.production
CORS_ALLOW_ORIGINS=https://gridworkflow.vercel.app,https://your-custom-domain.com
```

---

## 🟡 中等问题修复指南

### M1: httpx 客户端无连接复用

**问题代码**:
```python
# ai_service.py:197-203
async with httpx.AsyncClient(timeout=settings.text_timeout_sec) as client:
    resp = await client.post(
        f"{_normalize_base_url(settings)}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json=body,
    )
```

**修复方案**:
```python
# 创建 backend/app/core/http_client.py
from functools import lru_cache
import httpx

@lru_cache
def get_http_client() -> httpx.AsyncClient:
    """获取共享的 HTTP 客户端"""
    return httpx.AsyncClient(
        limits=httpx.Limits(
            max_connections=100,
            max_keepalive_connections=20,
        ),
        timeout=httpx.Timeout(30.0, connect=5.0),
    )

# 使用方式
from app.core.http_client import get_http_client

async def analyze_text(...):
    client = get_http_client()
    resp = await client.post(...)
```

---

### M2: 无 Rate Limiting

**修复方案**:
```python
# 安装依赖
# pip install slowapi

# backend/app/core/rate_limit.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# backend/app/main.py
from app.core.rate_limit import limiter
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# backend/app/api/routes/video.py
from app.core.rate_limit import limiter

@router.post("/generate")
@limiter.limit("5/minute")
async def generate_video(request: Request, ...):
    ...
```

---

### M3: 工作流状态无持久化

**当前问题**:
```typescript
// GridWorkflow.tsx - 刷新页面后状态丢失
const [state, setState] = useState<WorkflowState>(INITIAL_STATE);
```

**修复方案 A** (localStorage):
```typescript
// GridWorkflow.tsx
import { useEffect } from 'react';

const STORAGE_KEY = 'gridworkflow_state';

export const GridWorkflow: React.FC = () => {
  // 从 localStorage 恢复状态
  const [state, setState] = useState<WorkflowState>(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    return saved ? JSON.parse(saved) : INITIAL_STATE;
  });

  // 状态变化时保存
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }, [state]);

  const handleReset = () => {
    if (confirm('确定要重置所有内容吗？')) {
      localStorage.removeItem(STORAGE_KEY);
      setState(INITIAL_STATE);
      setEditedPrompt('');
    }
  };
  // ...
};
```

**修复方案 B** (Supabase 持久化):
```typescript
// 需要后端配合，存储到数据库
```

---

### M4: Pydantic v1 语法

**问题代码**:
```python
# backend/app/schemas/video.py
from pydantic import BaseModel, Field, validator  # v1 语法

@validator("prompt", "model", "aspect_ratio", "provider")
def strip_strings(cls, value: str) -> str:
    return value.strip()
```

**修复方案** (Pydantic v2):
```python
from pydantic import BaseModel, Field, field_validator

class VideoGenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    model: str = Field(..., min_length=1)
    images: list[str] | None = None
    aspect_ratio: str = Field(..., min_length=1)
    hd: bool = False
    duration: int = Field(..., ge=1)
    provider: str = Field("t8star")

    @field_validator("prompt", "model", "aspect_ratio", "provider", mode="before")
    @classmethod
    def strip_strings(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("images", mode="before")
    @classmethod
    def validate_images(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return value
        if len(value) == 0:
            raise ValueError("images must not be empty")
        return [v.strip() for v in value if v.strip()]

    @field_validator("provider", mode="after")
    @classmethod
    def normalize_provider(cls, value: str) -> str:
        return value.lower()
```

---

## 🟢 低优先级问题

### L1: EMPTY_1X1_PNG 硬编码

**当前代码**: `ai_service.py:13-83` 包含 71 行字节数组

**修复方案**:
```python
# 方案 A: 使用 base64 字符串
import base64

EMPTY_1X1_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAA"
    "CklEQVR4nGMAAQAABQABDQottAAAAABJRU5ErkJggg=="
)
EMPTY_1X1_PNG = base64.b64decode(EMPTY_1X1_PNG_B64)

# 方案 B: 外部文件
# backend/app/assets/empty_1x1.png
from importlib.resources import files
EMPTY_1X1_PNG = files("app.assets").joinpath("empty_1x1.png").read_bytes()
```

---

### L2: 注释语言混合

**建议规范**:
```python
# 推荐：关键业务逻辑使用中文，技术实现使用英文
# 或统一使用中文（根据团队约定）

# 示例 - 统一中文
def analyze_text(...):
    """调用 AI 网关进行文本分析
    
    Args:
        payload: 分析请求参数
        user_key: 用户自定义 API Key（可选）
        settings: 应用配置
        
    Returns:
        AI 模型返回的分析结果
        
    Raises:
        APIError: 上游服务异常时抛出
    """
```

---

### L3: 缺少暗色主题

**修复方案**:
```css
/* frontend/src/index.css */
@layer base {
  :root {
    /* Light Theme (已有) */
    --md-sys-color-primary: #0061A4;
    /* ... */
  }

  /* 添加暗色主题 */
  @media (prefers-color-scheme: dark) {
    :root {
      --md-sys-color-primary: #9ECAFF;
      --md-sys-color-on-primary: #003258;
      --md-sys-color-primary-container: #004880;
      --md-sys-color-on-primary-container: #D1E4FF;
      
      --md-sys-color-background: #1A1C1E;
      --md-sys-color-on-background: #E2E2E6;
      
      --md-sys-color-surface: #1A1C1E;
      --md-sys-color-on-surface: #E2E2E6;
      
      --md-sys-color-surface-container-lowest: #0F1113;
      --md-sys-color-surface-container-low: #1E2022;
      --md-sys-color-surface-container: #22252A;
      --md-sys-color-surface-container-high: #2C2F34;
      --md-sys-color-surface-container-highest: #373A3F;
      
      --glass-border: rgba(255, 255, 255, 0.1);
      --glass-surface: rgba(26, 28, 30, 0.9);
    }
  }
}
```

---

## 📊 代码统计

### 文件行数统计

| 模块 | 文件数 | 总行数 | 平均行数 |
|------|--------|--------|----------|
| backend/app/api/routes | 5 | 443 | 89 |
| backend/app/core | 4 | 267 | 67 |
| backend/app/services | 3 | 304 | 101 |
| backend/app/schemas | 4 | 95 | 24 |
| backend/app/storage | 1 | 209 | 209 |
| frontend/src/components | 7 | 654 | 93 |
| frontend/src/contexts | 3 | 124 | 41 |
| frontend/src/services | 2 | 197 | 99 |

### 复杂度热点

| 文件 | 行数 | 复杂度 | 建议 |
|------|------|--------|------|
| GridWorkflow.tsx | 469 | 高 | 拆分为子组件 |
| cos_client.py | 209 | 中 | 可接受 |
| workflow.py (route) | 252 | 中 | 提取业务逻辑 |
| video.py (route) | 192 | 低 | 良好 |

---

## ✅ 已确认的良好实践

### 后端
1. ✅ 统一响应格式 (`success_response` / `error_response`)
2. ✅ 请求追踪 (`request_id` 中间件)
3. ✅ 结构化日志 (包含 step, model, latency)
4. ✅ 配置单例 (`@lru_cache`)
5. ✅ 敏感信息脱敏 (`mask_task_id`)

### 前端
1. ✅ Context API 合理使用
2. ✅ 组件类型定义完整
3. ✅ 拦截器统一处理
4. ✅ CSS 变量系统
5. ✅ 响应式布局

---

**文档版本**: v1.0  
**最后更新**: 2026-01-07


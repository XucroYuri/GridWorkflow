# PLAN-v1.1-03: Sentry 监控告警接入

**版本**: v1.1  
**优先级**: P1  
**预估工时**: 2-3 天  
**状态**: 📝 规划中  

---

## 1. 概述

### 1.1 背景

当前项目缺乏统一的错误监控和告警机制：
- 前端错误仅通过 console.error 输出
- 后端异常仅记录到日志文件
- 无法实时感知线上问题
- 难以追踪错误发生的上下文

### 1.2 目标

- 前端 JS 错误自动上报
- 后端异常自动追踪
- 性能监控 (Performance Monitoring)
- 配置告警通知 (Slack/Email)

---

## 2. 当前状态分析

### 2.1 现有错误处理

```tsx
// 前端 - apiClient.ts
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('API Error:', error);  // 仅控制台输出
    return Promise.reject(error);
  }
);
```

```python
# 后端 - main.py
except Exception:
    logger.exception(...)  # 仅日志记录
    response = JSONResponse(status_code=500, ...)
```

### 2.2 问题清单

| 问题 | 影响 |
|------|------|
| 无错误聚合 | 相同错误重复上报 |
| 无上下文信息 | 难以复现问题 |
| 无性能基线 | 无法发现性能退化 |
| 无告警通知 | 延迟发现问题 |

---

## 3. 技术方案

### 3.1 Sentry 项目配置

```
Sentry Organization: gridworkflow
├── Project: gridworkflow-frontend (React)
└── Project: gridworkflow-backend (Python/FastAPI)
```

### 3.2 前端集成

#### 3.2.1 安装依赖

```bash
npm install @sentry/react @sentry/vite-plugin
```

#### 3.2.2 Sentry 初始化

```typescript
// frontend/src/lib/sentry.ts
import * as Sentry from '@sentry/react';

export function initSentry() {
  if (import.meta.env.PROD) {
    Sentry.init({
      dsn: import.meta.env.VITE_SENTRY_DSN,
      environment: import.meta.env.MODE,
      release: import.meta.env.VITE_APP_VERSION || '1.0.0',
      
      // 性能监控
      integrations: [
        Sentry.browserTracingIntegration(),
        Sentry.replayIntegration(),
      ],
      
      // 采样率
      tracesSampleRate: 0.2,  // 20% 性能追踪
      replaysSessionSampleRate: 0.1,  // 10% 会话回放
      replaysOnErrorSampleRate: 1.0,  // 错误时100%回放
      
      // 过滤敏感信息
      beforeSend(event) {
        // 移除敏感数据
        if (event.request?.headers) {
          delete event.request.headers['Authorization'];
        }
        return event;
      },
      
      // 忽略特定错误
      ignoreErrors: [
        'ResizeObserver loop',
        'Network request failed',
      ],
    });
  }
}
```

#### 3.2.3 入口文件集成

```tsx
// frontend/src/main.tsx
import { initSentry } from './lib/sentry';
import * as Sentry from '@sentry/react';

// 初始化 Sentry
initSentry();

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Sentry.ErrorBoundary
      fallback={<ErrorFallback />}
      showDialog
    >
      <App />
    </Sentry.ErrorBoundary>
  </StrictMode>,
);
```

#### 3.2.4 错误边界组件

```tsx
// frontend/src/components/ErrorFallback.tsx
import * as Sentry from '@sentry/react';

export const ErrorFallback: React.FC = () => {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100">
      <div className="bg-white p-8 rounded-lg shadow-lg text-center max-w-md">
        <h1 className="text-2xl font-bold text-red-600 mb-4">
          出错了
        </h1>
        <p className="text-gray-600 mb-6">
          应用遇到了意外错误，我们已收到通知并会尽快修复。
        </p>
        <button
          onClick={() => window.location.reload()}
          className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700"
        >
          刷新页面
        </button>
        <button
          onClick={() => Sentry.showReportDialog()}
          className="ml-4 text-blue-600 hover:underline"
        >
          报告问题
        </button>
      </div>
    </div>
  );
};
```

#### 3.2.5 API 错误上报

```typescript
// frontend/src/services/apiClient.ts
import * as Sentry from '@sentry/react';

apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    // 上报到 Sentry
    Sentry.withScope((scope) => {
      scope.setTag('api_error', true);
      scope.setContext('request', {
        url: error.config?.url,
        method: error.config?.method,
        status: error.response?.status,
      });
      Sentry.captureException(error);
    });
    
    return Promise.reject(error);
  }
);
```

#### 3.2.6 Vite 插件配置

```typescript
// frontend/vite.config.ts
import { sentryVitePlugin } from '@sentry/vite-plugin';

export default defineConfig({
  build: {
    sourcemap: true,  // 启用 sourcemap
  },
  plugins: [
    react(),
    // 仅生产构建时上传 sourcemap
    process.env.NODE_ENV === 'production' && sentryVitePlugin({
      org: 'gridworkflow',
      project: 'gridworkflow-frontend',
      authToken: process.env.SENTRY_AUTH_TOKEN,
    }),
  ].filter(Boolean),
});
```

### 3.3 后端集成

#### 3.3.1 安装依赖

```bash
pip install sentry-sdk[fastapi]
```

#### 3.3.2 Sentry 初始化

```python
# backend/app/core/sentry.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.httpx import HttpxIntegration

from app.core.config import get_settings


def init_sentry() -> None:
    """初始化 Sentry SDK"""
    settings = get_settings()
    
    if settings.env.lower() != 'production':
        return
    
    dsn = settings.sentry_dsn
    if not dsn:
        return
    
    sentry_sdk.init(
        dsn=dsn,
        environment=settings.env,
        release=settings.app_version or '1.0.0',
        
        # 集成
        integrations=[
            FastApiIntegration(transaction_style='endpoint'),
            HttpxIntegration(),
        ],
        
        # 采样率
        traces_sample_rate=0.2,
        profiles_sample_rate=0.1,
        
        # 过滤敏感信息
        before_send=_before_send,
        
        # 关联前端错误
        enable_tracing=True,
    )


def _before_send(event, hint):
    """发送前处理"""
    # 移除敏感 headers
    if 'request' in event and 'headers' in event['request']:
        headers = event['request']['headers']
        for key in ['Authorization', 'X-User-Gemini-Key', 'Cookie']:
            headers.pop(key, None)
    
    return event
```

#### 3.3.3 配置扩展

```python
# backend/app/core/config.py - 新增字段
class Settings(BaseModel):
    # ... 现有字段
    
    sentry_dsn: str | None = Field(
        default_factory=lambda: os.getenv("SENTRY_DSN")
    )
    app_version: str | None = Field(
        default_factory=lambda: os.getenv("APP_VERSION", "1.0.0")
    )
```

#### 3.3.4 Main.py 集成

```python
# backend/app/main.py
from app.core.sentry import init_sentry

# 初始化 Sentry（在创建 app 之前）
init_sentry()

app = FastAPI(title=settings.app_name)
```

#### 3.3.5 手动错误上报

```python
# backend/app/services/ai_service.py
import sentry_sdk

async def analyze_text(...):
    try:
        # ... 业务逻辑
    except httpx.TimeoutException as exc:
        sentry_sdk.capture_exception(exc)
        raise APIError(...)
```

### 3.4 告警配置

#### 3.4.1 告警规则

```yaml
# Sentry Alert Rules
alerts:
  - name: "高频错误告警"
    conditions:
      - type: event_frequency
        value: 10  # 10分钟内超过10次
        interval: 10m
    actions:
      - type: slack
        channel: "#gridworkflow-alerts"
      - type: email
        recipients: ["team@example.com"]

  - name: "新错误告警"
    conditions:
      - type: first_seen_event
    actions:
      - type: slack
        channel: "#gridworkflow-alerts"

  - name: "性能退化告警"
    conditions:
      - type: performance
        metric: p95
        threshold: 3000ms  # P95 超过 3 秒
    actions:
      - type: slack
        channel: "#gridworkflow-perf"
```

---

## 4. 实施计划

### Phase 1: 账号与项目配置 (Day 1 上午)

| 任务 | 工时 | 产出 |
|------|------|------|
| 注册 Sentry 账号 | 0.5h | 组织创建 |
| 创建前后端项目 | 0.5h | DSN 获取 |
| 配置环境变量 | 0.5h | Vercel Env |
| 配置 Slack 集成 | 0.5h | Webhook |

### Phase 2: 后端集成 (Day 1 下午)

| 任务 | 工时 | 产出 |
|------|------|------|
| 安装 sentry-sdk | 0.5h | requirements.txt |
| 创建 sentry.py | 1h | 初始化代码 |
| 集成到 main.py | 0.5h | 启动集成 |
| 测试错误上报 | 1h | 验证功能 |

### Phase 3: 前端集成 (Day 2)

| 任务 | 工时 | 产出 |
|------|------|------|
| 安装 @sentry/react | 0.5h | package.json |
| 创建 sentry.ts | 1h | 初始化代码 |
| 配置 ErrorBoundary | 1h | 错误边界 |
| 集成 Vite 插件 | 1h | Sourcemap 上传 |
| API 错误上报 | 1h | apiClient 改造 |
| 测试验证 | 1.5h | 端到端测试 |

### Phase 4: 告警与文档 (Day 3)

| 任务 | 工时 | 产出 |
|------|------|------|
| 配置告警规则 | 1.5h | Alert Rules |
| 配置 Dashboard | 1h | 监控面板 |
| 编写运维文档 | 1.5h | 告警响应指南 |
| 团队培训 | 1h | 使用指南 |

---

## 5. 环境变量配置

```bash
# Vercel Environment Variables

# 后端
SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx
APP_VERSION=1.1.0

# 前端
VITE_SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx
VITE_APP_VERSION=1.1.0

# CI/CD (仅构建时)
SENTRY_AUTH_TOKEN=sntrys_xxx
SENTRY_ORG=gridworkflow
SENTRY_PROJECT=gridworkflow-frontend
```

---

## 6. 风险评估

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 敏感信息泄露 | 中 | 高 | beforeSend 过滤 |
| 采样率过高 | 低 | 中 | 逐步调整采样率 |
| 告警疲劳 | 中 | 中 | 合理配置阈值 |
| 成本超支 | 低 | 低 | 使用免费额度 |

---

## 7. 验收标准

### 7.1 功能验证

- [ ] 前端 JS 错误自动上报
- [ ] 后端异常自动追踪
- [ ] 错误详情包含完整堆栈
- [ ] 用户上下文正确关联

### 7.2 告警验证

- [ ] 高频错误触发 Slack 通知
- [ ] 新错误触发告警
- [ ] 性能退化触发告警

### 7.3 安全验证

- [ ] 无敏感信息泄露
- [ ] Authorization Header 已过滤
- [ ] API Key 未上报

---

## 8. 参考资料

- [Sentry React 文档](https://docs.sentry.io/platforms/javascript/guides/react/)
- [Sentry Python 文档](https://docs.sentry.io/platforms/python/guides/fastapi/)
- [Sentry Alerts 配置](https://docs.sentry.io/product/alerts/)
- [Sentry Pricing](https://sentry.io/pricing/)

---

**作者**: AI Planner  
**最后更新**: 2026-01-07


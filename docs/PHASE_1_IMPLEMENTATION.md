# Phase 1: 稳定加固实施方案

> **执行周期**: 2026年1月第2周 - 2月第1周 (4周)  
> **优先级**: P0 - 必须完成  
> **目标**: 解决刷新丢失问题、建立测试基础、接入监控告警

---

## 📋 任务总览

| 任务 | 工时 | 负责 | 依赖 |
|------|------|------|------|
| 1.1 工作流持久化 | 5-7天 | 后端+前端 | Supabase |
| 1.2 测试体系基础 | 10-15天 | 后端+前端 | 无 |
| 1.3 Sentry 监控 | 2-3天 | 联合 | 无 |

---

## 1.1 工作流持久化

### 目标

解决用户刷新页面后工作流进度完全丢失的问题。

### 当前问题

1. 工作流状态仅存在于 React 组件状态
2. 视频任务列表未持久化到数据库
3. 用户无法恢复中断的工作

### 实施步骤

#### Step 1: 创建 Supabase 数据表 (1天)

```sql
-- 工作流会话表
CREATE TABLE workflow_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id),
  status TEXT NOT NULL DEFAULT 'draft',
  current_step INTEGER NOT NULL DEFAULT 1,
  input_data JSONB DEFAULT '{}',
  concept_result JSONB,
  storyboard_result JSONB,
  video_prompt_result JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 视频任务表
CREATE TABLE video_tasks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID REFERENCES workflow_sessions(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id),
  task_id TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  progress INTEGER DEFAULT 0,
  result_url TEXT,
  error_message TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS 策略
ALTER TABLE workflow_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE video_tasks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "用户只能访问自己的会话" ON workflow_sessions
  FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "用户只能访问自己的任务" ON video_tasks
  FOR ALL USING (auth.uid() = user_id);

-- 索引
CREATE INDEX idx_sessions_user ON workflow_sessions(user_id);
CREATE INDEX idx_tasks_session ON video_tasks(session_id);
CREATE INDEX idx_tasks_user ON video_tasks(user_id);
```

#### Step 2: 实现后端 API (2天)

**新增路由文件**: `backend/app/api/routes/sessions.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID
from typing import Optional
from pydantic import BaseModel

from app.core.auth import get_current_user

router = APIRouter(prefix="/sessions", tags=["sessions"])


class SessionCreate(BaseModel):
    input_data: dict = {}


class SessionUpdate(BaseModel):
    status: Optional[str] = None
    current_step: Optional[int] = None
    input_data: Optional[dict] = None
    concept_result: Optional[dict] = None
    storyboard_result: Optional[dict] = None
    video_prompt_result: Optional[dict] = None


@router.post("")
async def create_session(
    data: SessionCreate,
    user = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """创建新的工作流会话"""
    result = supabase.table('workflow_sessions').insert({
        'user_id': user.id,
        'input_data': data.input_data
    }).execute()
    
    return {"ok": True, "data": result.data[0], "error": None}


@router.get("/{session_id}")
async def get_session(
    session_id: UUID,
    user = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """获取会话详情"""
    result = supabase.table('workflow_sessions').select('*').eq(
        'id', str(session_id)
    ).eq('user_id', user.id).single().execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"ok": True, "data": result.data, "error": None}


@router.patch("/{session_id}")
async def update_session(
    session_id: UUID,
    data: SessionUpdate,
    user = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """更新会话状态"""
    update_data = {k: v for k, v in data.dict().items() if v is not None}
    update_data['updated_at'] = 'now()'
    
    result = supabase.table('workflow_sessions').update(update_data).eq(
        'id', str(session_id)
    ).eq('user_id', user.id).execute()
    
    return {"ok": True, "data": result.data[0], "error": None}


@router.get("/{session_id}/tasks")
async def list_session_tasks(
    session_id: UUID,
    user = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """获取会话下的所有视频任务"""
    result = supabase.table('video_tasks').select('*').eq(
        'session_id', str(session_id)
    ).eq('user_id', user.id).order('created_at', desc=True).execute()
    
    return {"ok": True, "data": result.data, "error": None}
```

#### Step 3: 实现前端 Hook (2天)

**新增文件**: `frontend/src/hooks/useWorkflowPersistence.ts`

```typescript
import { useState, useEffect, useCallback } from 'react';
import { supabase } from '../lib/supabase';
import { useAuth } from '../contexts/AuthContext';

interface WorkflowSession {
  id: string;
  status: string;
  current_step: number;
  input_data: Record<string, any>;
  concept_result?: Record<string, any>;
  storyboard_result?: Record<string, any>;
  video_prompt_result?: Record<string, any>;
}

interface VideoTask {
  id: string;
  task_id: string;
  status: string;
  progress: number;
  result_url?: string;
  error_message?: string;
}

const STORAGE_KEY = 'gridworkflow_session_id';

export function useWorkflowPersistence() {
  const { user } = useAuth();
  const [session, setSession] = useState<WorkflowSession | null>(null);
  const [tasks, setTasks] = useState<VideoTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 初始化：恢复或创建会话
  useEffect(() => {
    if (!user) {
      setSession(null);
      setLoading(false);
      return;
    }

    const initSession = async () => {
      try {
        const cachedId = localStorage.getItem(STORAGE_KEY);
        
        if (cachedId) {
          // 尝试恢复缓存的会话
          const { data, error } = await supabase
            .from('workflow_sessions')
            .select('*')
            .eq('id', cachedId)
            .single();

          // 显式检查：error 必须为 null 且 data 必须存在
          if (error === null && data !== null) {
            setSession(data);
            await loadTasks(data.id);
            setLoading(false);
            return;
          }
          // 缓存无效，清理
          localStorage.removeItem(STORAGE_KEY);
        }

        // 创建新会话
        const { data: newData, error: createError } = await supabase
          .from('workflow_sessions')
          .insert({ user_id: user.id })
          .select()
          .single();

        if (createError !== null) throw createError;
        if (newData === null) throw new Error('创建会话失败：返回数据为空');

        localStorage.setItem(STORAGE_KEY, newData.id);
        setSession(newData);
      } catch (err) {
        setError(err instanceof Error ? err.message : '会话初始化失败');
      } finally {
        setLoading(false);
      }
    };

    initSession();
  }, [user]);

  // 加载任务列表
  const loadTasks = async (sessionId: string) => {
    const { data, error } = await supabase
      .from('video_tasks')
      .select('*')
      .eq('session_id', sessionId)
      .order('created_at', { ascending: false });

    if (error === null && data !== null) {
      setTasks(data);
    }
  };

  // 更新会话数据
  const updateSession = useCallback(async (updates: Partial<WorkflowSession>) => {
    if (!session) return;

    const { data, error } = await supabase
      .from('workflow_sessions')
      .update({ ...updates, updated_at: new Date().toISOString() })
      .eq('id', session.id)
      .select()
      .single();

    if (error === null && data !== null) {
      setSession(data);
    }
  }, [session]);

  // 保存步骤结果
  const saveStepResult = useCallback(async (
    step: number,
    result: Record<string, any>
  ) => {
    const fieldMap: Record<number, string> = {
      1: 'concept_result',
      2: 'storyboard_result',
      4: 'video_prompt_result',
    };

    const field = fieldMap[step];
    if (!field) return;

    await updateSession({
      current_step: step + 1,
      [field]: result,
    });
  }, [updateSession]);

  // 添加视频任务
  const addTask = useCallback(async (taskId: string) => {
    if (!session || !user) return;

    const { data, error } = await supabase
      .from('video_tasks')
      .insert({
        session_id: session.id,
        user_id: user.id,
        task_id: taskId,
        status: 'pending',
      })
      .select()
      .single();

    if (error === null && data !== null) {
      setTasks(prev => [data, ...prev]);
    }
  }, [session, user]);

  // 更新任务状态
  const updateTask = useCallback(async (
    taskId: string,
    updates: Partial<VideoTask>
  ) => {
    const { data, error } = await supabase
      .from('video_tasks')
      .update({ ...updates, updated_at: new Date().toISOString() })
      .eq('task_id', taskId)
      .select()
      .single();

    if (error === null && data !== null) {
      setTasks(prev => prev.map(t => t.task_id === taskId ? data : t));
    }
  }, []);

  // 开始新会话
  const startNewSession = useCallback(async () => {
    if (!user) return;

    localStorage.removeItem(STORAGE_KEY);
    const { data, error } = await supabase
      .from('workflow_sessions')
      .insert({ user_id: user.id })
      .select()
      .single();

    if (error === null && data !== null) {
      localStorage.setItem(STORAGE_KEY, data.id);
      setSession(data);
      setTasks([]);
    }
  }, [user]);

  return {
    session,
    tasks,
    loading,
    error,
    updateSession,
    saveStepResult,
    addTask,
    updateTask,
    startNewSession,
    refreshTasks: () => session && loadTasks(session.id),
  };
}
```

#### Step 4: 改造 GridWorkflow 组件 (2天)

修改 `frontend/src/components/video/GridWorkflow.tsx`：

```typescript
// 引入 Hook
import { useWorkflowPersistence } from '../../hooks/useWorkflowPersistence';

export default function GridWorkflow() {
  const {
    session,
    tasks,
    loading,
    updateSession,
    saveStepResult,
    addTask,
    updateTask,
    startNewSession,
  } = useWorkflowPersistence();

  // 从会话恢复状态
  useEffect(() => {
    if (session) {
      setCurrentStep(session.current_step);
      setInputData(session.input_data);
      if (session.concept_result) setConceptResult(session.concept_result);
      if (session.storyboard_result) setStoryboardResult(session.storyboard_result);
      if (session.video_prompt_result) setVideoPromptResult(session.video_prompt_result);
    }
  }, [session]);

  // 步骤完成时保存
  const handleStepComplete = async (step: number, result: any) => {
    await saveStepResult(step, result);
    // ... 原有逻辑
  };

  // 视频生成时保存任务
  const handleVideoGenerate = async (taskId: string) => {
    await addTask(taskId);
    // ... 原有轮询逻辑
  };

  // 任务状态更新
  const handleTaskStatusChange = async (taskId: string, status: string, resultUrl?: string) => {
    await updateTask(taskId, { status, result_url: resultUrl });
  };

  // ... 其余组件逻辑
}
```

### 验收标准

- [ ] Supabase 表创建成功
- [ ] 后端 API 可正常调用
- [ ] 刷新页面后状态可恢复
- [ ] 视频任务列表持久化
- [ ] RLS 策略正确隔离用户数据

---

## 1.2 测试体系基础

### 目标

建立基础测试框架，覆盖关键路径。

### 实施步骤

#### Step 1: 后端测试配置 (1天)

**安装依赖**:
```bash
pip install pytest pytest-asyncio pytest-cov httpx
```

**配置文件**: `backend/pytest.ini`
```ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_functions = test_*
addopts = --cov=app --cov-report=term-missing
```

**测试工具**: `backend/tests/conftest.py`
```python
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_supabase(mocker):
    """Mock Supabase 客户端"""
    mock = mocker.patch('app.core.auth.supabase')
    return mock
```

#### Step 2: 后端单元测试 (3-5天)

**健康检查测试**: `backend/tests/test_health.py`
```python
def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["data"]["status"] == "ok"
```

**AI 服务测试**: `backend/tests/test_ai_service.py`
```python
import pytest
from unittest.mock import patch, AsyncMock

from app.services.ai_service import analyze_text, generate_image


@pytest.mark.asyncio
async def test_analyze_text_success():
    with patch('app.services.ai_service.httpx.AsyncClient') as mock_client:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{'message': {'content': 'Test response'}}]
        }
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        result = await analyze_text("Test prompt")
        assert result == "Test response"


@pytest.mark.asyncio
async def test_analyze_text_error():
    with patch('app.services.ai_service.httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.post.side_effect = Exception("API Error")
        
        with pytest.raises(Exception):
            await analyze_text("Test prompt")
```

**视频服务测试**: `backend/tests/test_video_service.py`
```python
import pytest
from unittest.mock import patch, AsyncMock

from app.services.video_service import create_video_task, get_task_status


@pytest.mark.asyncio
async def test_create_video_task():
    with patch('app.services.video_service.httpx.AsyncClient') as mock_client:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'task_id': 'test-123'}
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        result = await create_video_task("Test prompt", duration=10)
        assert result['task_id'] == 'test-123'
```

#### Step 3: 前端测试配置 (1天)

**安装依赖**:
```bash
npm install -D vitest @testing-library/react @testing-library/jest-dom jsdom
```

**配置文件**: `frontend/vitest.config.ts`
```typescript
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.ts',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
    },
  },
});
```

**Setup 文件**: `frontend/src/test/setup.ts`
```typescript
import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Mock Supabase
vi.mock('../lib/supabase', () => ({
  supabase: {
    auth: {
      getSession: vi.fn(),
      onAuthStateChange: vi.fn(() => ({ data: { subscription: { unsubscribe: vi.fn() } } })),
    },
    from: vi.fn(() => ({
      select: vi.fn().mockReturnThis(),
      insert: vi.fn().mockReturnThis(),
      update: vi.fn().mockReturnThis(),
      eq: vi.fn().mockReturnThis(),
      single: vi.fn(),
    })),
  },
}));
```

#### Step 4: 前端组件测试 (3-5天)

**GridWorkflow 测试**: `frontend/src/components/video/GridWorkflow.test.tsx`
```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import GridWorkflow from './GridWorkflow';
import { AuthProvider } from '../../contexts/AuthContext';
import { ToastProvider } from '../../contexts/ToastContext';

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <AuthProvider>
    <ToastProvider>
      {children}
    </ToastProvider>
  </AuthProvider>
);

describe('GridWorkflow', () => {
  it('renders step 1 by default', () => {
    render(<GridWorkflow />, { wrapper });
    expect(screen.getByText(/概念图生成/i)).toBeInTheDocument();
  });

  it('validates input before proceeding', async () => {
    render(<GridWorkflow />, { wrapper });
    
    const nextButton = screen.getByText(/下一步/i);
    fireEvent.click(nextButton);
    
    await waitFor(() => {
      expect(screen.getByText(/请填写/i)).toBeInTheDocument();
    });
  });
});
```

#### Step 5: CI 配置 (1天)

**GitHub Actions**: `.github/workflows/test.yml`
```yaml
name: Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov httpx
      - name: Run tests
        run: |
          cd backend
          pytest --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v4

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      - name: Run tests
        run: |
          cd frontend
          npm run test:coverage
```

### 验收标准

- [ ] pytest 配置完成，可运行
- [ ] 后端测试覆盖率 > 50%
- [ ] vitest 配置完成，可运行
- [ ] 关键组件有测试用例
- [ ] GitHub Actions CI 运行通过

---

## 1.3 Sentry 监控

### 目标

接入 Sentry 实现错误追踪和性能监控。

### 实施步骤

#### Step 1: 创建 Sentry 项目 (0.5天)

1. 访问 https://sentry.io
2. 创建新项目：
   - 后端: Python + FastAPI
   - 前端: JavaScript + React
3. 获取 DSN

#### Step 2: 后端集成 (1天)

**安装**:
```bash
pip install sentry-sdk[fastapi]
```

**配置**: `backend/app/core/sentry.py`
```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from app.core.config import settings


def init_sentry():
    if not settings.SENTRY_DSN:
        return
    
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.APP_ENV,
        integrations=[
            StarletteIntegration(),
            FastApiIntegration(),
        ],
        traces_sample_rate=0.1,  # 10% 采样
        profiles_sample_rate=0.1,
        send_default_pii=False,  # 不发送敏感信息
        before_send=filter_sensitive_data,
    )


def filter_sensitive_data(event, hint):
    """过滤敏感数据"""
    # 移除 API Key
    if 'request' in event and 'headers' in event['request']:
        headers = event['request']['headers']
        if 'authorization' in headers:
            headers['authorization'] = '[FILTERED]'
        if 'x-user-gemini-key' in headers:
            headers['x-user-gemini-key'] = '[FILTERED]'
    
    return event
```

**集成到 main.py**:
```python
from app.core.sentry import init_sentry

# 在 app 创建之前
init_sentry()
```

#### Step 3: 前端集成 (1天)

**安装**:
```bash
npm install @sentry/react
```

**配置**: `frontend/src/lib/sentry.ts`
```typescript
import * as Sentry from '@sentry/react';

export function initSentry() {
  const dsn = import.meta.env.VITE_SENTRY_DSN;
  if (!dsn) return;

  Sentry.init({
    dsn,
    environment: import.meta.env.MODE,
    integrations: [
      Sentry.browserTracingIntegration(),
      Sentry.replayIntegration({
        maskAllText: true,
        blockAllMedia: true,
      }),
    ],
    tracesSampleRate: 0.1,
    replaysSessionSampleRate: 0.1,
    replaysOnErrorSampleRate: 1.0,
    beforeSend(event) {
      // 过滤敏感数据
      if (event.request?.headers) {
        delete event.request.headers['Authorization'];
      }
      return event;
    },
  });
}
```

**集成到 main.tsx**:
```typescript
import { initSentry } from './lib/sentry';

initSentry();
```

**ErrorBoundary**: `frontend/src/components/ErrorBoundary.tsx`
```typescript
import * as Sentry from '@sentry/react';

export const ErrorBoundary = Sentry.ErrorBoundary;

// 使用
<ErrorBoundary fallback={<ErrorFallback />}>
  <App />
</ErrorBoundary>
```

#### Step 4: 配置告警规则 (0.5天)

在 Sentry Dashboard 配置：

1. **错误告警**:
   - 触发条件: 新错误出现
   - 通知: Email / Slack

2. **性能告警**:
   - 触发条件: p95 延迟 > 3s
   - 通知: Email

3. **错误激增告警**:
   - 触发条件: 10分钟内错误数 > 10
   - 通知: Email + Slack

### 验收标准

- [ ] Sentry 后端可收到错误
- [ ] Sentry 前端可收到错误
- [ ] 敏感数据已过滤
- [ ] 告警规则已配置
- [ ] 错误可追踪到具体代码行

---

## 执行时间表

```
Week 1:
├── Day 1-2: Supabase 表创建 + 后端 API
├── Day 3-4: 前端 Hook + 组件改造
└── Day 5: 工作流持久化验收

Week 2:
├── Day 1: 后端测试配置
├── Day 2-4: 后端测试编写
└── Day 5: 前端测试配置

Week 3:
├── Day 1-3: 前端测试编写
├── Day 4: CI 配置
└── Day 5: 测试验收

Week 4:
├── Day 1: Sentry 后端集成
├── Day 2: Sentry 前端集成
├── Day 3: 告警配置
├── Day 4-5: Phase 1 整体验收 + 文档更新
```

---

## 风险与缓解

| 风险 | 概率 | 缓解措施 |
|------|------|----------|
| Supabase 表设计不合理 | 中 | 预留扩展字段 + 分阶段迁移 |
| 测试覆盖率不达标 | 中 | 优先关键路径 + 持续补充 |
| Sentry 数据量过大 | 低 | 采样率控制 + 过滤配置 |

---

**文档维护者**: AI Architect  
**最后更新**: 2026-01-08


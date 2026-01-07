# PLAN-v1.1-02: 工作流进度持久化

**版本**: v1.1  
**优先级**: P0 (阻塞)  
**预估工时**: 5-7 天  
**状态**: 📝 规划中  

---

## 1. 概述

### 1.1 背景

这是代码审查报告中识别的 **P0 级阻塞问题**。当前工作流存在以下问题：

1. **状态丢失**: 刷新页面后所有进度丢失
2. **断点续传缺失**: 无法从中间步骤继续
3. **任务追溯困难**: 无法查看历史任务
4. **listTasks API 未实现**: 后端缺少任务持久化

### 1.2 目标

- 工作流状态在刷新后可恢复
- 支持从任意步骤继续
- 历史任务可查询
- 任务数据持久化到数据库

---

## 2. 当前状态分析

### 2.1 前端状态管理

```tsx
// GridWorkflow.tsx - 当前实现（问题）
const [state, setState] = useState<WorkflowState>(INITIAL_STATE);
// 问题：所有状态存储在内存中，刷新即丢失
```

### 2.2 后端任务管理

```python
# video.py - 缺少的 API
# /api/v1/video/tasks - 未实现
# 任务状态仅存在于上游 T8Star，本地无持久化
```

### 2.3 数据流缺口

```
当前数据流（有缺口）:
用户 → 前端(内存) → 后端(无状态) → T8Star(任务状态)
                 ↑                    ↓
                 └──── 状态丢失 ──────┘

目标数据流:
用户 → 前端 → 后端 → Supabase(持久化) ←→ T8Star
              ↓           ↓
           本地缓存    状态同步
```

---

## 3. 技术方案

### 3.1 方案选型

| 方案 | 优点 | 缺点 | 推荐度 |
|------|------|------|--------|
| **A: localStorage** | 简单快速 | 无跨设备同步、容量限制 | ⭐⭐ |
| **B: Supabase** | 跨设备、可扩展 | 需后端改造 | ⭐⭐⭐⭐⭐ |
| **C: IndexedDB** | 大容量、离线 | 复杂度高 | ⭐⭐⭐ |

**推荐方案**: B + A 组合（Supabase 主存储 + localStorage 缓存）

### 3.2 数据模型设计

#### 3.2.1 Supabase 表结构

```sql
-- 工作流会话表
CREATE TABLE workflow_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  
  -- 当前步骤
  current_step TEXT NOT NULL DEFAULT 'input',
  
  -- 输入数据
  plot TEXT,
  style TEXT,
  anchors JSONB DEFAULT '{}',
  aspect_ratio TEXT DEFAULT '16:9',
  
  -- Step 1-4 结果
  concept_prompt TEXT,
  concept_image_url TEXT,
  storyboard_prompt TEXT,
  grid_image_url TEXT,
  video_prompt TEXT,
  
  -- Step 5 视频任务
  video_task_id TEXT,
  video_status TEXT,
  video_url TEXT,
  
  -- 元数据
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  
  CONSTRAINT valid_step CHECK (current_step IN (
    'input', 'concept', 'storyboard_plan', 
    'storyboard_gen', 'video_prompt', 'video_result'
  ))
);

-- 索引
CREATE INDEX idx_workflow_sessions_user ON workflow_sessions(user_id);
CREATE INDEX idx_workflow_sessions_updated ON workflow_sessions(updated_at DESC);

-- RLS 策略
ALTER TABLE workflow_sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "用户只能访问自己的会话" ON workflow_sessions
  FOR ALL USING (auth.uid() = user_id);

-- 更新触发器
CREATE OR REPLACE FUNCTION update_workflow_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER workflow_sessions_updated
  BEFORE UPDATE ON workflow_sessions
  FOR EACH ROW EXECUTE FUNCTION update_workflow_timestamp();
```

#### 3.2.2 视频任务表（补充）

```sql
-- 视频任务历史表
CREATE TABLE video_tasks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  session_id UUID REFERENCES workflow_sessions(id) ON DELETE SET NULL,
  
  -- 任务信息
  task_id TEXT NOT NULL UNIQUE,
  provider TEXT DEFAULT 't8star',
  
  -- 请求参数
  prompt TEXT NOT NULL,
  model TEXT NOT NULL,
  aspect_ratio TEXT,
  duration INTEGER,
  
  -- 状态
  status TEXT DEFAULT 'queued',
  progress INTEGER DEFAULT 0,
  video_url TEXT,
  error_message TEXT,
  
  -- 时间戳
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  completed_at TIMESTAMPTZ,
  
  CONSTRAINT valid_status CHECK (status IN (
    'queued', 'running', 'succeeded', 'failed', 'cancelled'
  ))
);

-- 索引
CREATE INDEX idx_video_tasks_user ON video_tasks(user_id);
CREATE INDEX idx_video_tasks_status ON video_tasks(status);
CREATE INDEX idx_video_tasks_task_id ON video_tasks(task_id);

-- RLS
ALTER TABLE video_tasks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "用户只能访问自己的任务" ON video_tasks
  FOR ALL USING (auth.uid() = user_id);
```

### 3.3 前端实现

#### 3.3.1 工作流持久化 Hook

```typescript
// hooks/useWorkflowPersistence.ts
import { useState, useEffect, useCallback } from 'react';
import { supabase } from '../lib/supabase';
import { useAuth } from '../contexts/AuthContext';

export interface WorkflowSession {
  id: string;
  current_step: string;
  plot: string;
  style: string;
  anchors: Record<string, { text: string; image_base64?: string }>;
  aspect_ratio: string;
  concept_prompt?: string;
  concept_image_url?: string;
  storyboard_prompt?: string;
  grid_image_url?: string;
  video_prompt?: string;
  video_task_id?: string;
  video_status?: string;
  video_url?: string;
}

const STORAGE_KEY = 'gridworkflow_session_id';

export function useWorkflowPersistence() {
  const { user } = useAuth();
  const [session, setSession] = useState<WorkflowSession | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 加载或创建会话
  const initSession = useCallback(async () => {
    if (!user) return;
    
    setLoading(true);
    try {
      // 先检查 localStorage 中的会话 ID
      const cachedId = localStorage.getItem(STORAGE_KEY);
      
      if (cachedId) {
        // 尝试恢复已有会话
        const { data, error } = await supabase
          .from('workflow_sessions')
          .select('*')
          .eq('id', cachedId)
          .single();
        
        if (data && !error) {
          setSession(data);
          setLoading(false);
          return;
        }
      }
      
      // 创建新会话
      const { data, error } = await supabase
        .from('workflow_sessions')
        .insert({ user_id: user.id })
        .select()
        .single();
      
      if (error) throw error;
      
      localStorage.setItem(STORAGE_KEY, data.id);
      setSession(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载会话失败');
    } finally {
      setLoading(false);
    }
  }, [user]);

  // 更新会话
  const updateSession = useCallback(async (updates: Partial<WorkflowSession>) => {
    if (!session?.id) return;
    
    try {
      const { data, error } = await supabase
        .from('workflow_sessions')
        .update(updates)
        .eq('id', session.id)
        .select()
        .single();
      
      if (error) throw error;
      setSession(data);
      
      // 同步到 localStorage 作为缓存
      localStorage.setItem(`${STORAGE_KEY}_cache`, JSON.stringify(data));
    } catch (err) {
      setError(err instanceof Error ? err.message : '保存失败');
    }
  }, [session?.id]);

  // 重置会话
  const resetSession = useCallback(async () => {
    if (!user) return;
    
    try {
      localStorage.removeItem(STORAGE_KEY);
      localStorage.removeItem(`${STORAGE_KEY}_cache`);
      
      const { data, error } = await supabase
        .from('workflow_sessions')
        .insert({ user_id: user.id })
        .select()
        .single();
      
      if (error) throw error;
      
      localStorage.setItem(STORAGE_KEY, data.id);
      setSession(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : '重置失败');
    }
  }, [user]);

  useEffect(() => {
    initSession();
  }, [initSession]);

  return {
    session,
    loading,
    error,
    updateSession,
    resetSession,
  };
}
```

#### 3.3.2 GridWorkflow 改造

```tsx
// GridWorkflow.tsx - 改造后
import { useWorkflowPersistence } from '../../hooks/useWorkflowPersistence';

export const GridWorkflow: React.FC = () => {
  const { session, loading, updateSession, resetSession } = useWorkflowPersistence();
  const [editedPrompt, setEditedPrompt] = useState('');

  // 从会话恢复状态
  const state: WorkflowState = useMemo(() => {
    if (!session) return INITIAL_STATE;
    return {
      step: session.current_step as WorkflowStep,
      isLoading: false,
      error: null,
      plot: session.plot || '',
      style: session.style || 'Anime style, OLM studio',
      anchors: session.anchors || INITIAL_STATE.anchors,
      aspectRatio: session.aspect_ratio || '16:9',
      conceptPrompt: session.concept_prompt,
      conceptImageUrl: session.concept_image_url,
      storyboardPrompt: session.storyboard_prompt,
      gridImageUrl: session.grid_image_url,
      videoPrompt: session.video_prompt,
      videoTaskId: session.video_task_id,
    };
  }, [session]);

  // 更新状态时同步到数据库
  const updateState = useCallback((updates: Partial<WorkflowState>) => {
    const dbUpdates: Partial<WorkflowSession> = {};
    
    if (updates.step) dbUpdates.current_step = updates.step;
    if (updates.plot !== undefined) dbUpdates.plot = updates.plot;
    if (updates.style !== undefined) dbUpdates.style = updates.style;
    if (updates.anchors) dbUpdates.anchors = updates.anchors;
    if (updates.aspectRatio) dbUpdates.aspect_ratio = updates.aspectRatio;
    if (updates.conceptPrompt) dbUpdates.concept_prompt = updates.conceptPrompt;
    if (updates.conceptImageUrl) dbUpdates.concept_image_url = updates.conceptImageUrl;
    if (updates.storyboardPrompt) dbUpdates.storyboard_prompt = updates.storyboardPrompt;
    if (updates.gridImageUrl) dbUpdates.grid_image_url = updates.gridImageUrl;
    if (updates.videoPrompt) dbUpdates.video_prompt = updates.videoPrompt;
    if (updates.videoTaskId) dbUpdates.video_task_id = updates.videoTaskId;
    
    updateSession(dbUpdates);
  }, [updateSession]);

  // 显示加载状态
  if (loading) {
    return <GridWorkflowSkeleton />;
  }

  // ... 其余组件实现
};
```

### 3.4 后端实现

#### 3.4.1 任务列表 API

```python
# backend/app/api/routes/video.py - 新增

@router.get("/tasks", dependencies=[Depends(require_user)])
async def list_user_tasks(
    request: Request,
    user_id: str = Depends(require_user),
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    status: Optional[str] = Query(default=None),
) -> JSONResponse:
    """获取用户的视频任务列表"""
    from app.core.supabase import get_supabase_client
    
    client = get_supabase_client()
    query = client.table('video_tasks').select('*').eq('user_id', user_id)
    
    if status:
        query = query.eq('status', status)
    
    query = query.order('created_at', desc=True).range(offset, offset + limit - 1)
    
    result = query.execute()
    
    return JSONResponse(
        status_code=200,
        content=success_response({
            "tasks": result.data,
            "total": len(result.data),
            "limit": limit,
            "offset": offset,
        }),
    )


@router.post("/tasks", dependencies=[Depends(require_user)])
async def create_task_record(
    request: Request,
    task_id: str,
    prompt: str,
    model: str,
    aspect_ratio: str,
    duration: int,
    user_id: str = Depends(require_user),
    session_id: Optional[str] = None,
) -> JSONResponse:
    """创建任务记录"""
    from app.core.supabase import get_supabase_client
    
    client = get_supabase_client()
    
    result = client.table('video_tasks').insert({
        'user_id': user_id,
        'session_id': session_id,
        'task_id': task_id,
        'prompt': prompt,
        'model': model,
        'aspect_ratio': aspect_ratio,
        'duration': duration,
        'status': 'queued',
    }).execute()
    
    return JSONResponse(
        status_code=201,
        content=success_response(result.data[0] if result.data else None),
    )
```

#### 3.4.2 Supabase 客户端

```python
# backend/app/core/supabase.py
from functools import lru_cache
from supabase import create_client, Client

from app.core.config import get_settings


@lru_cache
def get_supabase_client() -> Client:
    """获取 Supabase 客户端（单例）"""
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise RuntimeError("Supabase 配置缺失")
    
    return create_client(
        settings.supabase_url,
        settings.supabase_service_role_key,
    )
```

---

## 4. 实施计划

### Phase 1: 数据库设计 (Day 1-2)

| 任务 | 工时 | 产出 |
|------|------|------|
| 设计表结构 | 2h | SQL DDL |
| 创建 Supabase 表 | 2h | workflow_sessions, video_tasks |
| 配置 RLS 策略 | 2h | 行级安全 |
| 编写迁移脚本 | 2h | 版本化 DDL |

### Phase 2: 后端实现 (Day 3-4)

| 任务 | 工时 | 产出 |
|------|------|------|
| 创建 Supabase 客户端 | 2h | supabase.py |
| 实现 /tasks API | 4h | GET/POST 端点 |
| 任务状态同步 | 4h | 轮询更新逻辑 |
| 单元测试 | 4h | pytest 测试 |

### Phase 3: 前端实现 (Day 5-6)

| 任务 | 工时 | 产出 |
|------|------|------|
| 创建持久化 Hook | 4h | useWorkflowPersistence |
| 改造 GridWorkflow | 4h | 状态同步 |
| 改造 TaskList | 2h | API 对接 |
| 离线缓存策略 | 2h | localStorage 备份 |

### Phase 4: 测试验收 (Day 7)

| 任务 | 工时 | 产出 |
|------|------|------|
| 集成测试 | 3h | 端到端验证 |
| 边界场景测试 | 2h | 网络中断、并发 |
| 文档更新 | 2h | API 文档、用户指南 |

---

## 5. 风险评估

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| Supabase 延迟 | 中 | 中 | localStorage 缓存 |
| 并发写入冲突 | 低 | 高 | 乐观锁 + updated_at |
| 大文件存储 | 中 | 中 | 图片 URL 而非 Base64 |
| RLS 配置错误 | 低 | 高 | 详细测试 + 审计日志 |

---

## 6. 验收标准

### 6.1 功能验证

- [ ] 刷新页面后工作流状态恢复
- [ ] 关闭浏览器后再次打开可继续
- [ ] 历史任务列表正确显示
- [ ] 任务状态实时更新

### 6.2 性能指标

- [ ] 会话加载 < 500ms
- [ ] 状态更新 < 200ms
- [ ] 任务列表加载 < 1s

### 6.3 可靠性

- [ ] 网络中断后本地缓存可用
- [ ] 恢复网络后自动同步
- [ ] 无数据丢失

---

## 7. 参考资料

- [Supabase 文档](https://supabase.com/docs)
- [RLS 最佳实践](https://supabase.com/docs/guides/auth/row-level-security)
- [React Query 状态同步](https://tanstack.com/query/latest)
- 内部文档: `docs/WORKPACKS/gridworkflow/WP-GW-09_AUTH_SUPABASE.md`

---

**作者**: AI Planner  
**最后更新**: 2026-01-07


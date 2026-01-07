# PLAN-v1.2-03: 任务队列系统

**版本**: v1.2  
**优先级**: P0 (阻塞)  
**预估工时**: 7-10 天  
**状态**: 📝 规划中  
**前置依赖**: v1.1-02 工作流持久化  

---

## 1. 概述

### 1.1 背景

当前视频生成依赖客户端轮询，存在以下问题：
- 用户需保持页面打开
- 轮询浪费资源
- Vercel Serverless 30s 超时限制
- 无法处理高并发场景

### 1.2 目标

- 异步任务处理
- 任务状态推送（替代轮询）
- 支持任务取消/重试
- 高可用队列基础设施

---

## 2. 当前状态分析

### 2.1 现有流程

```
当前流程（轮询）:
┌────────┐  POST /generate  ┌────────┐  调用上游  ┌────────┐
│ 前端   │ ───────────────► │ 后端   │ ─────────► │ T8Star │
└────────┘                  └────────┘            └────────┘
    │                                                  │
    │  GET /status (每3秒)                             │
    │ ◄───────────────────────────────────────────────┘
    │
    └── 循环直到 succeeded/failed
```

### 2.2 问题分析

| 问题 | 影响 | 严重度 |
|------|------|--------|
| 轮询浪费 | 无效 API 调用 | 高 |
| 页面依赖 | 关闭页面丢失任务 | 高 |
| 30s 超时 | 长任务无法处理 | 高 |
| 无重试 | 瞬时失败无法恢复 | 中 |

---

## 3. 技术方案

### 3.1 方案选型

| 方案 | 优点 | 缺点 | 成本 | 推荐度 |
|------|------|------|------|--------|
| **A: Upstash Redis** | Serverless、低延迟 | 消息可能丢失 | $10/月起 | ⭐⭐⭐⭐ |
| **B: Upstash QStash** | 专为 Serverless 设计 | 学习曲线 | 免费额度 | ⭐⭐⭐⭐⭐ |
| **C: Supabase Realtime** | 已有集成 | 非任务队列设计 | 包含 | ⭐⭐⭐ |
| **D: 自建 Redis** | 完全控制 | 运维成本 | 较高 | ⭐⭐ |

**推荐方案**: B (Upstash QStash) + C (Supabase Realtime 推送)

### 3.2 架构设计

```
新架构:
┌────────┐  POST /generate  ┌────────┐  enqueue  ┌─────────┐
│ 前端   │ ───────────────► │ 后端   │ ────────► │ QStash  │
└────────┘                  └────────┘           └─────────┘
    │                            │                    │
    │  WebSocket                 │                    │ callback
    │  (Supabase Realtime)       │                    ▼
    │                       ┌────┴────┐         ┌─────────┐
    │ ◄─────────────────────┤ 状态    │ ◄──────┤ Worker  │
    │                       │ 推送    │         │ Function│
    │                       └─────────┘         └─────────┘
    │                                                │
    │                                                │ 调用
    │                                                ▼
    │                                           ┌─────────┐
    └──────────────────────────────────────────►│ T8Star  │
                                                └─────────┘
```

### 3.3 Upstash QStash 集成

#### 3.3.1 安装依赖

```bash
pip install upstash-qstash
```

#### 3.3.2 QStash 客户端

```python
# backend/app/core/qstash.py
from functools import lru_cache
from qstash import QStash

from app.core.config import get_settings


@lru_cache
def get_qstash_client() -> QStash:
    """获取 QStash 客户端"""
    settings = get_settings()
    if not settings.qstash_token:
        raise RuntimeError("QSTASH_TOKEN 未配置")
    
    return QStash(token=settings.qstash_token)


async def enqueue_video_task(
    task_id: str,
    provider: str,
    prompt: str,
    model: str,
    user_api_key: str | None = None,
) -> str:
    """将视频任务入队"""
    client = get_qstash_client()
    settings = get_settings()
    
    # 回调 URL（Worker 端点）
    callback_url = f"{settings.app_base_url}/api/v1/internal/video-worker"
    
    # 发布消息
    response = client.message.create(
        url=callback_url,
        body={
            "task_id": task_id,
            "provider": provider,
            "prompt": prompt,
            "model": model,
            "user_api_key": user_api_key,
        },
        retries=3,
        delay="0s",
        # 去重（避免重复处理）
        deduplication_id=task_id,
    )
    
    return response.message_id
```

#### 3.3.3 配置扩展

```python
# backend/app/core/config.py - 新增
class Settings(BaseModel):
    # ... 现有字段
    
    qstash_token: str | None = Field(
        default_factory=lambda: os.getenv("QSTASH_TOKEN")
    )
    qstash_signing_key: str | None = Field(
        default_factory=lambda: os.getenv("QSTASH_CURRENT_SIGNING_KEY")
    )
    app_base_url: str = Field(
        default_factory=lambda: os.getenv("APP_BASE_URL", "https://gridworkflow.vercel.app")
    )
```

### 3.4 Worker 实现

```python
# backend/app/api/routes/internal.py
import hashlib
import hmac
from fastapi import APIRouter, HTTPException, Header, Request
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.supabase import get_supabase_client
from app.services.video_service import get_video_provider_registry

router = APIRouter(prefix="/api/v1/internal", tags=["internal"])


class VideoWorkerPayload(BaseModel):
    task_id: str
    provider: str
    prompt: str
    model: str
    user_api_key: str | None = None


def verify_qstash_signature(
    request_body: bytes,
    signature: str,
    signing_key: str
) -> bool:
    """验证 QStash 签名"""
    expected = hmac.new(
        signing_key.encode(),
        request_body,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("/video-worker")
async def video_worker(
    request: Request,
    upstash_signature: str = Header(..., alias="Upstash-Signature"),
):
    """视频任务 Worker（由 QStash 调用）"""
    settings = get_settings()
    
    # 验证签名
    body = await request.body()
    if not verify_qstash_signature(
        body,
        upstash_signature,
        settings.qstash_signing_key
    ):
        raise HTTPException(401, "Invalid signature")
    
    # 解析 payload
    payload = VideoWorkerPayload.parse_raw(body)
    
    client = get_supabase_client()
    
    try:
        # 更新状态为 running
        client.table('video_tasks').update({
            'status': 'running',
            'updated_at': 'now()',
        }).eq('task_id', payload.task_id).execute()
        
        # 调用上游
        registry = get_video_provider_registry()
        provider = registry.get(payload.provider)
        
        if not provider:
            raise ValueError(f"Unknown provider: {payload.provider}")
        
        # 轮询直到完成（Worker 内部）
        result = await poll_until_complete(
            provider,
            payload.task_id,
            payload.user_api_key,
            max_attempts=60,  # 最多轮询 60 次（约 3 分钟）
            interval=3,
        )
        
        # 更新最终状态
        client.table('video_tasks').update({
            'status': result['status'],
            'video_url': result.get('video_url'),
            'progress': 100 if result['status'] == 'succeeded' else 0,
            'error_message': result.get('error_message'),
            'completed_at': 'now()' if result['status'] in ['succeeded', 'failed'] else None,
            'updated_at': 'now()',
        }).eq('task_id', payload.task_id).execute()
        
        return {"ok": True}
        
    except Exception as e:
        # 更新失败状态
        client.table('video_tasks').update({
            'status': 'failed',
            'error_message': str(e)[:200],
            'updated_at': 'now()',
        }).eq('task_id', payload.task_id).execute()
        
        raise HTTPException(500, str(e))


async def poll_until_complete(
    provider,
    task_id: str,
    user_api_key: str | None,
    max_attempts: int = 60,
    interval: int = 3,
) -> dict:
    """轮询直到任务完成"""
    import asyncio
    
    for _ in range(max_attempts):
        result = await provider.status(task_id, user_api_key)
        
        status = result.get('status', '').upper()
        
        if status == 'SUCCESS':
            return {
                'status': 'succeeded',
                'video_url': result.get('data', {}).get('output'),
            }
        elif status == 'FAILURE':
            return {
                'status': 'failed',
                'error_message': result.get('fail_reason'),
            }
        
        # 继续等待
        await asyncio.sleep(interval)
    
    return {
        'status': 'failed',
        'error_message': '任务超时',
    }
```

### 3.5 视频生成 API 改造

```python
# backend/app/api/routes/video.py - 改造

@router.post("/generate", dependencies=[Depends(require_user)])
async def generate_video(
    payload: VideoGenerateRequest,
    request: Request,
    user_id: str = Depends(require_user),
    settings: Settings = Depends(get_settings),
    x_user_gemini_key: str | None = Header(default=None),
) -> JSONResponse:
    # ... 参数验证（保持不变）
    
    # 1. 先调用上游获取 task_id
    registry = get_video_provider_registry(settings)
    provider = registry.get(payload.provider)
    
    upstream_payload = {
        "prompt": payload.prompt,
        "model": payload.model,
        "aspect_ratio": payload.aspect_ratio,
        "hd": payload.hd,
        "duration": str(payload.duration),
    }
    if payload.images:
        upstream_payload["images"] = payload.images
    
    try:
        result = await provider.generate(upstream_payload, x_user_gemini_key)
    except UpstreamServiceError as exc:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response(exc.code, exc.message),
        )
    
    task_id = result.get("task_id")
    if not task_id or not is_valid_task_id(task_id):
        return JSONResponse(
            status_code=502,
            content=error_response("UPSTREAM_ERROR", "上游返回异常"),
        )
    
    # 2. 保存任务记录
    client = get_supabase_client()
    client.table('video_tasks').insert({
        'user_id': user_id,
        'task_id': task_id,
        'provider': payload.provider,
        'prompt': payload.prompt,
        'model': payload.model,
        'aspect_ratio': payload.aspect_ratio,
        'duration': payload.duration,
        'status': 'queued',
    }).execute()
    
    # 3. 入队异步处理
    from app.core.qstash import enqueue_video_task
    
    await enqueue_video_task(
        task_id=task_id,
        provider=payload.provider,
        prompt=payload.prompt,
        model=payload.model,
        user_api_key=x_user_gemini_key,
    )
    
    return JSONResponse(
        status_code=200,
        content=success_response({"task_id": task_id}),
    )
```

### 3.6 Supabase Realtime 状态推送

```typescript
// frontend/src/hooks/useTaskSubscription.ts
import { useEffect, useCallback } from 'react';
import { supabase } from '../lib/supabase';
import type { VideoTask } from '../services/videoService';

export function useTaskSubscription(
  taskId: string | null,
  onUpdate: (task: VideoTask) => void
) {
  useEffect(() => {
    if (!taskId) return;
    
    // 订阅任务状态变化
    const subscription = supabase
      .channel(`task:${taskId}`)
      .on(
        'postgres_changes',
        {
          event: 'UPDATE',
          schema: 'public',
          table: 'video_tasks',
          filter: `task_id=eq.${taskId}`,
        },
        (payload) => {
          const task = payload.new as VideoTask;
          onUpdate(task);
        }
      )
      .subscribe();
    
    return () => {
      subscription.unsubscribe();
    };
  }, [taskId, onUpdate]);
}

// 使用示例
function VideoStudio() {
  const [currentTask, setCurrentTask] = useState<VideoTask | null>(null);
  
  const handleTaskUpdate = useCallback((task: VideoTask) => {
    setCurrentTask(task);
    
    if (task.status === 'succeeded') {
      toast.success('视频生成完成！');
    } else if (task.status === 'failed') {
      toast.error(`生成失败: ${task.error_message}`);
    }
  }, []);
  
  useTaskSubscription(currentTask?.task_id ?? null, handleTaskUpdate);
  
  // ...
}
```

### 3.7 任务取消/重试

```python
# backend/app/api/routes/video.py - 新增

@router.post("/cancel/{task_id}", dependencies=[Depends(require_user)])
async def cancel_task(
    task_id: str,
    user_id: str = Depends(require_user),
) -> JSONResponse:
    """取消任务"""
    client = get_supabase_client()
    
    # 检查任务存在且属于当前用户
    task = client.table('video_tasks').select('status').eq(
        'task_id', task_id
    ).eq('user_id', user_id).single().execute()
    
    if not task.data:
        return JSONResponse(404, content=error_response("NOT_FOUND", "任务不存在"))
    
    if task.data['status'] not in ['queued', 'running']:
        return JSONResponse(400, content=error_response("BAD_REQUEST", "任务已完成"))
    
    # 更新状态为 cancelled
    client.table('video_tasks').update({
        'status': 'cancelled',
        'updated_at': 'now()',
    }).eq('task_id', task_id).execute()
    
    return success_response(None)


@router.post("/retry/{task_id}", dependencies=[Depends(require_user)])
async def retry_task(
    task_id: str,
    user_id: str = Depends(require_user),
) -> JSONResponse:
    """重试失败的任务"""
    client = get_supabase_client()
    
    task = client.table('video_tasks').select('*').eq(
        'task_id', task_id
    ).eq('user_id', user_id).single().execute()
    
    if not task.data:
        return JSONResponse(404, content=error_response("NOT_FOUND", "任务不存在"))
    
    if task.data['status'] != 'failed':
        return JSONResponse(400, content=error_response("BAD_REQUEST", "只能重试失败的任务"))
    
    # 重新入队
    from app.core.qstash import enqueue_video_task
    
    await enqueue_video_task(
        task_id=task_id,
        provider=task.data['provider'],
        prompt=task.data['prompt'],
        model=task.data['model'],
    )
    
    # 更新状态
    client.table('video_tasks').update({
        'status': 'queued',
        'error_message': None,
        'updated_at': 'now()',
    }).eq('task_id', task_id).execute()
    
    return success_response({"task_id": task_id})
```

---

## 4. 实施计划

### Phase 1: 基础设施 (Day 1-2)

| 任务 | 工时 | 产出 |
|------|------|------|
| 注册 Upstash 账号 | 1h | QStash 配置 |
| QStash 客户端实现 | 4h | qstash.py |
| 配置环境变量 | 2h | Vercel Env |
| Worker 端点基础 | 4h | internal.py |

### Phase 2: Worker 实现 (Day 3-5)

| 任务 | 工时 | 产出 |
|------|------|------|
| 签名验证 | 2h | 安全机制 |
| 轮询逻辑 | 4h | poll_until_complete |
| 状态更新 | 4h | 数据库同步 |
| 错误处理 | 4h | 重试/失败处理 |
| 单元测试 | 6h | pytest |

### Phase 3: API 改造 (Day 6-7)

| 任务 | 工时 | 产出 |
|------|------|------|
| 改造 /generate | 4h | 入队逻辑 |
| 实现 /cancel | 2h | 取消端点 |
| 实现 /retry | 2h | 重试端点 |
| 集成测试 | 4h | E2E 验证 |

### Phase 4: 前端改造 (Day 8-9)

| 任务 | 工时 | 产出 |
|------|------|------|
| Realtime 订阅 | 4h | useTaskSubscription |
| 移除轮询逻辑 | 2h | 清理代码 |
| 取消/重试 UI | 4h | 按钮交互 |
| 状态提示优化 | 2h | Toast 通知 |

### Phase 5: 测试与文档 (Day 10)

| 任务 | 工时 | 产出 |
|------|------|------|
| 压力测试 | 3h | 并发验证 |
| 故障模拟 | 2h | 降级验证 |
| 文档编写 | 3h | 架构文档 |

---

## 5. 风险评估

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| QStash 服务中断 | 低 | 高 | 回退到轮询 |
| Worker 超时 | 中 | 中 | 分段处理 |
| 消息丢失 | 低 | 高 | 死信队列 |
| 成本超支 | 低 | 低 | 监控用量 |

---

## 6. 验收标准

### 6.1 功能验证

- [ ] 任务异步处理正常
- [ ] 状态实时推送
- [ ] 取消任务生效
- [ ] 重试任务生效
- [ ] 关闭页面后任务继续

### 6.2 性能验证

- [ ] 状态更新延迟 < 3s
- [ ] 支持 100 并发任务
- [ ] Worker 处理时间 < 5min

### 6.3 可靠性验证

- [ ] 网络中断恢复
- [ ] Worker 失败重试
- [ ] 无消息丢失

---

## 7. 参考资料

- [Upstash QStash 文档](https://upstash.com/docs/qstash)
- [Supabase Realtime](https://supabase.com/docs/guides/realtime)
- [Vercel Serverless Functions](https://vercel.com/docs/functions)

---

**作者**: AI Planner  
**最后更新**: 2026-01-07


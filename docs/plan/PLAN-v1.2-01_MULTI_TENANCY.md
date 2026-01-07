# PLAN-v1.2-01: 多租户支持

**版本**: v1.2  
**优先级**: P1  
**预估工时**: 10-15 天  
**状态**: 📝 规划中  
**前置依赖**: v1.1-02 工作流持久化  

---

## 1. 概述

### 1.1 背景

随着用户增长，需要支持：
- 用户数据隔离
- 资源配额管理
- 使用量统计
- 计费准备

### 1.2 目标

- 完整的用户数据隔离
- 可配置的资源配额
- 使用量追踪
- 为未来计费奠定基础

---

## 2. 当前状态分析

### 2.1 现有隔离机制

```sql
-- 当前 RLS 策略（基础）
CREATE POLICY "用户只能访问自己的数据" ON workflow_sessions
  FOR ALL USING (auth.uid() = user_id);
```

### 2.2 缺失能力

| 能力 | 现状 | 需求 |
|------|------|------|
| 数据隔离 | 基础 RLS | 完整隔离 |
| 配额限制 | 无 | API 调用/存储配额 |
| 使用统计 | 无 | 实时统计 |
| 组织管理 | 无 | 团队/组织 |

---

## 3. 技术方案

### 3.1 数据模型扩展

#### 3.1.1 租户/组织表

```sql
-- 组织表
CREATE TABLE organizations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  slug TEXT UNIQUE NOT NULL,
  
  -- 配额配置
  plan TEXT DEFAULT 'free',
  api_quota_daily INTEGER DEFAULT 100,
  storage_quota_bytes BIGINT DEFAULT 1073741824,  -- 1GB
  
  -- 元数据
  settings JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- 组织成员表
CREATE TABLE organization_members (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  role TEXT DEFAULT 'member',
  
  created_at TIMESTAMPTZ DEFAULT now(),
  
  UNIQUE(organization_id, user_id),
  CONSTRAINT valid_role CHECK (role IN ('owner', 'admin', 'member', 'viewer'))
);

-- 索引
CREATE INDEX idx_org_members_user ON organization_members(user_id);
CREATE INDEX idx_org_members_org ON organization_members(organization_id);
```

#### 3.1.2 配额追踪表

```sql
-- 使用量统计表
CREATE TABLE usage_stats (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  
  -- 统计周期
  period_start DATE NOT NULL,
  period_end DATE NOT NULL,
  
  -- 使用量
  api_calls_count INTEGER DEFAULT 0,
  video_generations INTEGER DEFAULT 0,
  image_generations INTEGER DEFAULT 0,
  storage_bytes_used BIGINT DEFAULT 0,
  
  -- 时间戳
  updated_at TIMESTAMPTZ DEFAULT now(),
  
  UNIQUE(organization_id, period_start)
);

-- 每日使用量记录
CREATE TABLE daily_usage (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  
  date DATE NOT NULL DEFAULT CURRENT_DATE,
  
  -- 分类计数
  api_calls INTEGER DEFAULT 0,
  video_tasks INTEGER DEFAULT 0,
  image_tasks INTEGER DEFAULT 0,
  
  UNIQUE(organization_id, user_id, date)
);

CREATE INDEX idx_daily_usage_date ON daily_usage(date);
```

#### 3.1.3 扩展现有表

```sql
-- 扩展 workflow_sessions
ALTER TABLE workflow_sessions 
  ADD COLUMN organization_id UUID REFERENCES organizations(id);

-- 扩展 video_tasks
ALTER TABLE video_tasks 
  ADD COLUMN organization_id UUID REFERENCES organizations(id);

-- 创建索引
CREATE INDEX idx_workflow_sessions_org ON workflow_sessions(organization_id);
CREATE INDEX idx_video_tasks_org ON video_tasks(organization_id);
```

### 3.2 RLS 策略升级

```sql
-- 组织级 RLS
CREATE POLICY "组织成员可访问组织数据" ON workflow_sessions
  FOR ALL USING (
    organization_id IN (
      SELECT organization_id FROM organization_members
      WHERE user_id = auth.uid()
    )
  );

-- 函数：获取用户所属组织
CREATE OR REPLACE FUNCTION get_user_organizations()
RETURNS SETOF UUID AS $$
  SELECT organization_id FROM organization_members
  WHERE user_id = auth.uid();
$$ LANGUAGE sql SECURITY DEFINER;
```

### 3.3 配额检查服务

```python
# backend/app/services/quota_service.py
from dataclasses import dataclass
from datetime import date
from typing import Optional

from app.core.supabase import get_supabase_client


@dataclass
class QuotaStatus:
    allowed: bool
    current: int
    limit: int
    message: Optional[str] = None


class QuotaService:
    def __init__(self, organization_id: str):
        self.organization_id = organization_id
        self.client = get_supabase_client()
    
    async def check_api_quota(self) -> QuotaStatus:
        """检查 API 调用配额"""
        # 获取组织配额配置
        org = self.client.table('organizations').select(
            'api_quota_daily'
        ).eq('id', self.organization_id).single().execute()
        
        limit = org.data.get('api_quota_daily', 100)
        
        # 获取今日使用量
        today = date.today().isoformat()
        usage = self.client.table('daily_usage').select(
            'api_calls'
        ).eq('organization_id', self.organization_id).eq(
            'date', today
        ).execute()
        
        current = sum(u['api_calls'] for u in usage.data) if usage.data else 0
        
        if current >= limit:
            return QuotaStatus(
                allowed=False,
                current=current,
                limit=limit,
                message=f"已达到每日 API 调用上限 ({limit} 次)"
            )
        
        return QuotaStatus(allowed=True, current=current, limit=limit)
    
    async def increment_usage(self, user_id: str, usage_type: str) -> None:
        """增加使用量计数"""
        today = date.today().isoformat()
        
        # Upsert 使用量记录
        self.client.rpc('increment_daily_usage', {
            'p_organization_id': self.organization_id,
            'p_user_id': user_id,
            'p_date': today,
            'p_usage_type': usage_type,
        }).execute()
```

### 3.4 配额中间件

```python
# backend/app/core/quota_middleware.py
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from app.services.quota_service import QuotaService


class QuotaMiddleware(BaseHTTPMiddleware):
    """配额检查中间件"""
    
    # 需要配额检查的端点
    QUOTA_ENDPOINTS = {
        '/api/v1/concept': 'api_calls',
        '/api/v1/storyboard/plan': 'api_calls',
        '/api/v1/storyboard/generate': 'image_tasks',
        '/api/v1/video/prompt': 'api_calls',
        '/api/v1/video/generate': 'video_tasks',
    }
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        if path in self.QUOTA_ENDPOINTS:
            org_id = getattr(request.state, 'organization_id', None)
            if org_id:
                quota_service = QuotaService(org_id)
                status = await quota_service.check_api_quota()
                
                if not status.allowed:
                    raise HTTPException(
                        status_code=429,
                        detail={
                            'code': 'QUOTA_EXCEEDED',
                            'message': status.message,
                            'current': status.current,
                            'limit': status.limit,
                        }
                    )
        
        response = await call_next(request)
        return response
```

### 3.5 前端组织选择器

```tsx
// components/OrganizationSelector.tsx
import { useState, useEffect } from 'react';
import { supabase } from '../lib/supabase';
import { useAuth } from '../contexts/AuthContext';

interface Organization {
  id: string;
  name: string;
  slug: string;
  role: string;
}

export const OrganizationSelector: React.FC = () => {
  const { user } = useAuth();
  const [orgs, setOrgs] = useState<Organization[]>([]);
  const [current, setCurrent] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;
    
    supabase
      .from('organization_members')
      .select(`
        role,
        organization:organizations(id, name, slug)
      `)
      .eq('user_id', user.id)
      .then(({ data }) => {
        if (data) {
          const mapped = data.map(d => ({
            id: d.organization.id,
            name: d.organization.name,
            slug: d.organization.slug,
            role: d.role,
          }));
          setOrgs(mapped);
          
          // 默认选择第一个或从 localStorage 恢复
          const saved = localStorage.getItem('current_org');
          if (saved && mapped.find(o => o.id === saved)) {
            setCurrent(saved);
          } else if (mapped.length > 0) {
            setCurrent(mapped[0].id);
            localStorage.setItem('current_org', mapped[0].id);
          }
        }
      });
  }, [user]);

  const handleChange = (orgId: string) => {
    setCurrent(orgId);
    localStorage.setItem('current_org', orgId);
    window.location.reload();  // 刷新以应用新组织上下文
  };

  if (orgs.length <= 1) return null;

  return (
    <select
      value={current || ''}
      onChange={(e) => handleChange(e.target.value)}
      className="bg-gray-100 border border-gray-300 rounded-md px-3 py-1.5 text-sm"
    >
      {orgs.map(org => (
        <option key={org.id} value={org.id}>
          {org.name} ({org.role})
        </option>
      ))}
    </select>
  );
};
```

---

## 4. 实施计划

### Phase 1: 数据模型 (Day 1-3)

| 任务 | 工时 | 产出 |
|------|------|------|
| 设计组织表结构 | 4h | DDL |
| 设计配额表结构 | 4h | DDL |
| 扩展现有表 | 4h | ALTER TABLE |
| RLS 策略升级 | 4h | 安全策略 |
| 数据迁移脚本 | 4h | 迁移工具 |

### Phase 2: 后端服务 (Day 4-7)

| 任务 | 工时 | 产出 |
|------|------|------|
| QuotaService 实现 | 8h | 配额服务 |
| 配额中间件 | 4h | Middleware |
| 组织 API | 8h | CRUD 端点 |
| 使用量统计 API | 4h | 统计端点 |

### Phase 3: 前端实现 (Day 8-11)

| 任务 | 工时 | 产出 |
|------|------|------|
| OrganizationContext | 4h | 上下文管理 |
| 组织选择器 | 4h | UI 组件 |
| 配额展示 | 4h | 使用量面板 |
| 管理界面 | 8h | 组织设置页 |

### Phase 4: 测试与文档 (Day 12-15)

| 任务 | 工时 | 产出 |
|------|------|------|
| 集成测试 | 8h | 测试用例 |
| 权限测试 | 4h | RLS 验证 |
| 性能测试 | 4h | 配额查询优化 |
| 文档编写 | 4h | 用户/管理员指南 |

---

## 5. 风险评估

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| RLS 性能影响 | 中 | 中 | 索引优化 |
| 配额绕过 | 低 | 高 | 服务端强制检查 |
| 数据迁移失败 | 低 | 高 | 备份 + 回滚脚本 |
| 组织切换复杂 | 中 | 中 | 简化 UI 流程 |

---

## 6. 验收标准

### 6.1 功能验证

- [ ] 用户可创建/加入组织
- [ ] 数据完全隔离
- [ ] 配额限制生效
- [ ] 使用量正确统计

### 6.2 安全验证

- [ ] 跨组织数据不可访问
- [ ] 配额无法绕过
- [ ] 权限分级正确

### 6.3 性能验证

- [ ] 配额检查 < 50ms
- [ ] 组织切换 < 1s

---

## 7. 参考资料

- [Supabase 多租户指南](https://supabase.com/docs/guides/getting-started/architecture#multi-tenancy)
- [RLS 性能优化](https://supabase.com/docs/guides/auth/row-level-security#performance)
- 内部文档: `docs/specs/SPEC-ARCH-03_MULTI_TENANCY_BYOK.md`

---

**作者**: AI Planner  
**最后更新**: 2026-01-07


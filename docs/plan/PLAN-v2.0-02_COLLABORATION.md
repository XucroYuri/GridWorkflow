# PLAN-v2.0-02: 协作功能

**版本**: v2.0  
**优先级**: P2  
**预估工时**: 20-30 天  
**状态**: 📝 规划中  
**前置依赖**: v1.2-01 多租户支持  

---

## 1. 概述

### 1.1 背景

为支持团队协作场景，需要实现：
- 团队工作空间
- 项目共享
- 实时协作（可选）
- 版本历史

### 1.2 目标

- 组织成员可查看共享项目
- 项目可设置访问权限
- 支持评论和反馈
- 可追溯修改历史

---

## 2. 功能规划

### 2.1 项目管理

```
项目 (Project)
├── 基本信息 (名称、描述、封面)
├── 权限设置 (私有/组织内/公开)
├── 工作流会话 (workflow_sessions)
├── 版本历史 (snapshots)
└── 评论 (comments)
```

### 2.2 权限模型

| 角色 | 查看 | 编辑 | 删除 | 管理 |
|------|------|------|------|------|
| Owner | ✅ | ✅ | ✅ | ✅ |
| Admin | ✅ | ✅ | ❌ | ✅ |
| Member | ✅ | ✅ | ❌ | ❌ |
| Viewer | ✅ | ❌ | ❌ | ❌ |

### 2.3 核心表结构

```sql
-- 项目表
CREATE TABLE projects (
  id UUID PRIMARY KEY,
  organization_id UUID REFERENCES organizations(id),
  name TEXT NOT NULL,
  description TEXT,
  cover_url TEXT,
  visibility TEXT DEFAULT 'private',  -- private/organization/public
  created_by UUID REFERENCES auth.users(id),
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 项目成员表
CREATE TABLE project_members (
  project_id UUID REFERENCES projects(id),
  user_id UUID REFERENCES auth.users(id),
  role TEXT DEFAULT 'viewer',
  PRIMARY KEY (project_id, user_id)
);

-- 项目评论表
CREATE TABLE project_comments (
  id UUID PRIMARY KEY,
  project_id UUID REFERENCES projects(id),
  user_id UUID REFERENCES auth.users(id),
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 项目快照（版本历史）
CREATE TABLE project_snapshots (
  id UUID PRIMARY KEY,
  project_id UUID REFERENCES projects(id),
  workflow_state JSONB NOT NULL,
  created_by UUID REFERENCES auth.users(id),
  created_at TIMESTAMPTZ DEFAULT now()
);
```

---

## 3. 实施路线

### Phase 1: 项目基础 (Week 1-2)
- 项目 CRUD
- 基本权限控制
- 项目列表页

### Phase 2: 共享与权限 (Week 3)
- 项目成员管理
- 邀请机制
- RLS 策略

### Phase 3: 版本与评论 (Week 4)
- 快照保存
- 历史回溯
- 评论功能

### Phase 4: 实时协作（可选）(Week 5-6)
- Supabase Realtime
- 协同编辑冲突处理
- 在线状态显示

---

## 4. 验收标准

- [ ] 可创建/管理项目
- [ ] 项目可设置不同可见性
- [ ] 组织成员可访问共享项目
- [ ] 可查看项目历史版本
- [ ] 可在项目中添加评论

---

**详细设计文档待 v1.2 完成后补充**

---

**作者**: AI Planner  
**最后更新**: 2026-01-07


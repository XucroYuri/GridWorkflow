# GridWorkflow 迭代规划验证与建议报告

**审核日期**: 2026-01-07  
**审核版本**: v1.0  
**状态**: 🔍 审核完成  

---

## 📋 总体评估

### 优势

| 方面 | 评价 | 说明 |
|------|------|------|
| 整体规划 | ⭐⭐⭐⭐ | 路线图清晰，优先级合理 |
| 技术选型 | ⭐⭐⭐⭐ | 主流方案，生态成熟 |
| 文档质量 | ⭐⭐⭐⭐⭐ | 结构完整，细节丰富 |
| 依赖管理 | ⭐⭐⭐ | 有依赖图，但存在隐藏耦合 |
| 工时估计 | ⭐⭐⭐ | 偏乐观，需增加缓冲 |

### 风险概览

```
风险热力图:
┌─────────────────────────────────────────────────────┐
│ 高  │ 任务队列(中)  │ BYOK密钥安全(高) │            │
│ 影  │               │                  │            │
│ 响  │───────────────┼──────────────────┼────────────│
│     │ 测试覆盖(低)  │ 多租户RLS(中)    │ 模型扩展   │
│ 低  │               │                  │ (低)       │
│     └───────────────┴──────────────────┴────────────│
│               低概率          中概率        高概率    │
└─────────────────────────────────────────────────────┘
```

---

## 🔬 方案逐项验证

---

### 1. PLAN-v1.1-01: 前端性能优化

#### ✅ 可行性: 高

**优点:**
- 使用原生 `loading="lazy"` 简单有效
- React.memo/useMemo 是标准优化手段
- Vite 代码分割配置成熟

**🟡 需要注意的问题:**

| 问题 | 风险 | 建议调整 |
|------|------|----------|
| FCP < 1.5s 目标过于激进 | Vercel 冷启动可能导致首屏 > 2s | 目标调整为 FCP < 2s |
| ProgressiveImage 增加复杂度 | 引入额外状态管理 | 先用原生 loading="lazy"，效果不佳再升级 |
| manualChunks 配置 | 可能导致 chunk 过多 | 建议只分离 vendor-react，其他按需 |

**📌 建议调整:**

```typescript
// 原方案 - 过度分割
manualChunks: {
  'vendor-react': ['react', 'react-dom', 'react-router-dom'],
  'vendor-supabase': ['@supabase/supabase-js'],
  'vendor-ui': ['lucide-react', 'clsx'],
}

// 建议方案 - 简化
manualChunks: {
  'vendor': ['react', 'react-dom', 'react-router-dom', '@supabase/supabase-js'],
}
// lucide-react 和 clsx 体积小，无需单独分割
```

**⏱️ 工时评估:**
- 原估计: 3-4 天
- 建议: 4-5 天 (增加性能测试和回归验证)

---

### 2. PLAN-v1.1-02: 工作流持久化

#### ✅ 可行性: 高 (核心功能)

**优点:**
- Supabase + localStorage 双保险策略合理
- 数据模型设计完整
- RLS 策略正确

**🔴 关键问题与调整:**

| 问题 | 严重度 | 建议 |
|------|--------|------|
| `workflow_sessions` 存储 Base64 图片 | 高 | 改为仅存储 URL，图片存 COS |
| localStorage 同步时机不明确 | 中 | 明确：每步骤完成后同步 |
| 未考虑并发编辑 | 中 | 增加乐观锁 (版本号) |
| 会话恢复 UX 缺失 | 中 | 增加"是否继续上次进度"提示 |

**📌 数据模型建议调整:**

```sql
-- 原方案问题：anchors 可能含 Base64
CREATE TABLE workflow_sessions (
  -- ...
  anchors JSONB DEFAULT '{}',  -- ❌ 可能存大量 Base64
);

-- 建议调整：拆分锚点图片
CREATE TABLE workflow_sessions (
  -- ...
  anchors JSONB DEFAULT '{}',  -- ✅ 仅存文本
  anchor_image_urls JSONB DEFAULT '{}',  -- ✅ 图片 URL 单独存储
  version INTEGER DEFAULT 1,  -- ✅ 乐观锁
);
```

**📌 前端恢复逻辑建议:**

```tsx
// 增加恢复提示
useEffect(() => {
  if (session && session.current_step !== 'input') {
    const shouldRestore = window.confirm(
      `检测到未完成的工作流 (步骤: ${session.current_step})，是否继续？`
    );
    if (!shouldRestore) {
      resetSession();
    }
  }
}, [session]);
```

**⏱️ 工时评估:**
- 原估计: 5-7 天
- 建议: 7-9 天 (增加乐观锁、恢复 UX、图片分离处理)

---

### 3. PLAN-v1.1-03: Sentry 监控

#### ✅ 可行性: 高

**优点:**
- 标准方案，文档完整
- 采样率配置合理
- 敏感信息过滤考虑周全

**🟡 需要注意的问题:**

| 问题 | 建议 |
|------|------|
| Sentry 免费额度有限 (5K events/月) | 初期够用，需监控用量 |
| beforeSend 过滤可能遗漏新字段 | 建议用白名单而非黑名单 |
| replaysSessionSampleRate 10% 偏高 | 初期降为 5%，节省配额 |

**📌 建议调整:**

```typescript
// 原方案 - 黑名单过滤
beforeSend(event) {
  if (event.request?.headers) {
    delete event.request.headers['Authorization'];
  }
  return event;
}

// 建议 - 白名单过滤
beforeSend(event) {
  const SAFE_HEADERS = ['Content-Type', 'Accept', 'X-Request-ID'];
  if (event.request?.headers) {
    const safeHeaders: Record<string, string> = {};
    for (const key of SAFE_HEADERS) {
      if (event.request.headers[key]) {
        safeHeaders[key] = event.request.headers[key];
      }
    }
    event.request.headers = safeHeaders;
  }
  return event;
}
```

**⏱️ 工时评估:**
- 原估计: 2-3 天
- 建议: 2-3 天 ✅ 合理

---

### 4. PLAN-v1.2-01: 多租户支持

#### 🟡 可行性: 中高 (复杂度被低估)

**优点:**
- 数据模型设计合理
- RLS 策略正确
- 配额服务抽象清晰

**🔴 关键问题:**

| 问题 | 严重度 | 详情 |
|------|--------|------|
| **用户-组织映射缺失** | 高 | 新用户注册后如何加入默认组织？ |
| **单用户多组织切换** | 中 | 切换时需刷新页面，体验差 |
| **RLS 性能** | 中 | `organization_id IN (SELECT ...)` 每次查询需关联 |
| **初始化迁移** | 高 | 现有用户如何迁移？ |

**📌 关键缺失：用户注册流程**

```sql
-- 建议：注册时自动创建个人组织
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
DECLARE
  new_org_id UUID;
BEGIN
  -- 创建个人组织
  INSERT INTO organizations (name, slug, plan)
  VALUES (
    NEW.email || '''s Workspace',
    'personal-' || NEW.id,
    'free'
  )
  RETURNING id INTO new_org_id;
  
  -- 添加为 owner
  INSERT INTO organization_members (organization_id, user_id, role)
  VALUES (new_org_id, NEW.id, 'owner');
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION handle_new_user();
```

**📌 RLS 性能优化:**

```sql
-- 原方案 - 每次子查询
CREATE POLICY "..." ON workflow_sessions
  FOR ALL USING (
    organization_id IN (SELECT organization_id FROM organization_members WHERE user_id = auth.uid())
  );

-- 建议 - 使用函数 + 索引
CREATE OR REPLACE FUNCTION user_organizations()
RETURNS UUID[] AS $$
  SELECT array_agg(organization_id) FROM organization_members WHERE user_id = auth.uid();
$$ LANGUAGE sql STABLE SECURITY DEFINER;

CREATE POLICY "..." ON workflow_sessions
  FOR ALL USING (organization_id = ANY(user_organizations()));
```

**⏱️ 工时评估:**
- 原估计: 10-15 天
- 建议: **15-20 天** (增加用户迁移、注册流程、RLS 优化)

---

### 5. PLAN-v1.2-02: BYOK

#### 🟡 可行性: 中 (安全复杂度高)

**优点:**
- 加密方案正确 (Fernet 对称加密)
- Key 预览设计合理
- 验证 API 考虑周全

**🔴 关键安全问题:**

| 问题 | 严重度 | 详情 |
|------|--------|------|
| **固定 Salt** | 高 | `salt=b'gridworkflow_api_key_salt'` 降低安全性 |
| **派生密钥泄露风险** | 高 | 如果 JWT Secret 泄露，所有 Key 可被解密 |
| **Key 轮换机制缺失** | 中 | 无法在不影响用户的情况下更换加密密钥 |
| **审计日志缺失** | 中 | Key 的使用/创建/删除需记录 |

**📌 安全增强建议:**

```python
# 方案 A: 每用户独立 Salt (推荐)
class KeyEncryption:
    def _derive_key(self, user_id: str) -> bytes:
        """为每个用户派生独立密钥"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=f"gw_key_{user_id}".encode(),  # 用户特定 salt
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(self.master_secret))

# 方案 B: 使用 Supabase Vault (更安全)
# Supabase 提供内置的密钥管理功能
# https://supabase.com/docs/guides/database/vault
```

**📌 审计日志表:**

```sql
CREATE TABLE key_audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id),
  key_id UUID REFERENCES user_api_keys(id),
  action TEXT NOT NULL,  -- 'created', 'used', 'deleted', 'verified'
  ip_address INET,
  user_agent TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);
```

**📌 替代方案考虑:**

| 方案 | 安全性 | 复杂度 | 推荐度 |
|------|--------|--------|--------|
| 自研加密 (当前) | 中 | 中 | ⭐⭐⭐ |
| Supabase Vault | 高 | 低 | ⭐⭐⭐⭐ |
| AWS Secrets Manager | 最高 | 高 | ⭐⭐ (成本高) |
| HashiCorp Vault | 最高 | 最高 | ⭐ (运维复杂) |

**🎯 建议: 优先调研 Supabase Vault，若不满足需求再自研**

**⏱️ 工时评估:**
- 原估计: 5-7 天
- 建议: **8-10 天** (增加安全评审、审计日志、密钥轮换设计)

---

### 6. PLAN-v1.2-03: 任务队列

#### ✅ 可行性: 高 (架构设计优秀)

**优点:**
- QStash + Supabase Realtime 组合巧妙
- 签名验证保证安全
- 取消/重试机制完整

**🟡 需要注意的问题:**

| 问题 | 风险 | 建议 |
|------|------|------|
| QStash 回调 URL 公开 | 中 | 除签名验证外，增加 IP 白名单 |
| Worker 超时 (Vercel 10s 限制) | 高 | 需使用 Vercel Pro 或 Edge Function |
| 任务取消不彻底 | 中 | 仅更新本地状态，上游任务仍在执行 |
| 消息幂等性 | 中 | 需处理重复投递 |

**🔴 关键问题：Vercel Serverless 超时**

```
问题分析:
- Vercel Hobby: 10s 超时
- Vercel Pro: 60s 超时  
- Worker 需轮询 3 分钟 (60 次 × 3s)

解决方案:
1. 升级 Vercel Pro (推荐)
2. 分段处理 (复杂)
3. 使用 Edge Function (部分解决)
```

**📌 建议方案：分段处理 + 多次回调**

```python
# 改进版 Worker - 分段处理
async def video_worker(request: Request):
    # ... 签名验证
    
    # 单次只轮询 5 次 (约 15 秒)
    MAX_POLLS_PER_CALL = 5
    
    for _ in range(MAX_POLLS_PER_CALL):
        result = await provider.status(task_id, user_api_key)
        status = result.get('status', '').upper()
        
        if status in ['SUCCESS', 'FAILURE']:
            # 完成，更新数据库
            await update_final_status(task_id, result)
            return {"ok": True, "final": True}
        
        await asyncio.sleep(3)
    
    # 未完成，重新入队继续轮询
    await enqueue_video_task(
        task_id=task_id,
        provider=payload.provider,
        prompt=payload.prompt,
        model=payload.model,
        user_api_key=payload.user_api_key,
        delay="5s",  # 5 秒后重试
    )
    
    return {"ok": True, "final": False, "requeued": True}
```

**📌 幂等性处理:**

```python
# 使用数据库锁防止重复处理
async def video_worker(request: Request):
    # 获取任务锁
    lock_result = await client.rpc('acquire_task_lock', {
        'p_task_id': payload.task_id,
        'p_worker_id': os.getenv('VERCEL_DEPLOYMENT_ID', 'unknown'),
    }).execute()
    
    if not lock_result.data.get('acquired'):
        return {"ok": True, "skipped": True, "reason": "Another worker processing"}
    
    try:
        # ... 处理逻辑
    finally:
        await client.rpc('release_task_lock', {'p_task_id': payload.task_id}).execute()
```

**⏱️ 工时评估:**
- 原估计: 7-10 天
- 建议: **10-12 天** (增加分段处理、幂等性、Vercel 升级评估)

---

### 7. PLAN-v2.0-01: 模型扩展

#### 🟡 可行性: 中 (依赖外部 API 稳定性)

**评估:**

| 模型 | API 成熟度 | 集成难度 | 建议 |
|------|-----------|----------|------|
| Runway Gen-3 | 高 | 中 | ✅ 优先 |
| Pika 1.5 | 中 | 中 | ✅ 第二 |
| Kling | 低 | 高 | ⚠️ 需调研 |
| MiniMax | 低 | 高 | ⏸️ 延后 |

**📌 建议:**
- 先完成 Provider 抽象层
- 仅集成 Runway + Pika，后续按需扩展
- 工时调整: 15-20 天 → **10-12 天 (仅含 2 个新 Provider)**

---

### 8. PLAN-v2.0-02: 协作功能

#### 🟡 可行性: 中 (功能范围过大)

**问题:**
- 20-30 天工时估计偏乐观
- 实时协作 (Supabase Realtime) 复杂度被低估
- 版本历史需要快照存储，占用空间大

**📌 建议分阶段:**

| 阶段 | 功能 | 工时 | 优先级 |
|------|------|------|--------|
| Phase 1 | 项目基础 CRUD | 5 天 | P1 |
| Phase 2 | 共享与权限 | 7 天 | P1 |
| Phase 3 | 评论功能 | 5 天 | P2 |
| Phase 4 | 版本历史 | 7 天 | P2 |
| Phase 5 | 实时协作 | 15+ 天 | **P3 (可能延后到 v2.1)** |

**总计: 实际 35-40 天，建议将实时协作延后**

---

### 9. PLAN-v2.0-03: 移动端适配

#### ✅ 可行性: 高

**评估:**
- 方案合理，Tailwind 响应式成熟
- PWA 可作为可选功能
- 工时估计合理

**📌 小建议:**
- 优先适配 iOS Safari (用户占比高)
- 视频播放使用原生 `<video>` 而非自定义播放器
- 考虑添加 "桌面版" 切换按钮

---

### 10. PLAN-DEBT-01: 测试体系

#### ✅ 可行性: 高 (重要且紧急)

**优点:**
- 测试金字塔策略正确
- 技术选型成熟 (pytest, Vitest, Playwright)
- CI/CD 配置完整

**🟡 需要注意:**

| 问题 | 建议 |
|------|------|
| 70% 覆盖率目标初期难达成 | 先定 50%，逐步提升 |
| E2E 测试维护成本高 | 仅覆盖 3-5 个核心流程 |
| Mock 外部 API 复杂 | 使用 VCR 录制/回放模式 |

**📌 建议优先级调整:**

```
原计划:
1. 后端单元测试 (Day 1-5)
2. 后端集成测试 (Day 6-8)
3. 前端测试 (Day 9-13)
4. E2E (Day 14-15)

建议调整:
1. 后端核心服务单元测试 (Day 1-3) -- 聚焦 ai_service, video_service
2. 前端核心组件测试 (Day 4-6) -- 聚焦 GridWorkflow
3. 关键路径集成测试 (Day 7-9) -- /concept, /video/generate
4. 最小 E2E (Day 10-12) -- 仅完整工作流
5. CI/CD + 覆盖率报告 (Day 13-15)
```

---

### 11. PLAN-DEBT-02: API 文档

#### ✅ 可行性: 高

**评估:**
- 方案简单有效
- FastAPI 原生支持好
- 工时合理

**📌 唯一建议:**
- 增加 Postman Collection 导出
- 为重要字段添加 `deprecated` 标记规范

---

## 🔄 依赖关系分析与调整

### 原依赖图问题

```
发现的隐藏依赖:
1. v1.2-03 任务队列 → 需要 Vercel Pro 升级 (外部依赖)
2. v1.2-02 BYOK → 应在 v1.1-02 持久化之后 (数据结构依赖)
3. DEBT-01 测试 → 应与各版本并行，而非单独阶段
```

### 建议调整后的依赖图

```
                        ┌──────────────────────┐
                        │ DEBT-01 测试 (持续)  │
                        └──────────┬───────────┘
                                   │ 并行
           ┌───────────────────────┼───────────────────────┐
           │                       │                       │
           ▼                       ▼                       ▼
┌──────────────────┐    ┌─────────────────────┐   ┌───────────────────┐
│ v1.1-01 性能优化 │    │ v1.1-02 工作流持久化│   │ v1.1-03 Sentry    │
└────────┬─────────┘    └──────────┬──────────┘   └────────┬──────────┘
         │                         │                       │
         └─────────────────────────┼───────────────────────┘
                                   │
                                   ▼
                         ┌─────────────────────┐
                         │ v1.1 发布 Milestone │
                         └──────────┬──────────┘
                                    │
           ┌────────────────────────┼────────────────────────┐
           │                        │                        │
           ▼                        ▼                        ▼
┌──────────────────┐    ┌─────────────────────┐   ┌───────────────────┐
│ v1.2-01 多租户   │    │ v1.2-03 任务队列    │   │ DEBT-02 API文档   │
│ (含BYOK基础)     │    │ (+Vercel Pro)       │   │                   │
└────────┬─────────┘    └──────────┬──────────┘   └───────────────────┘
         │                         │
         │      ┌──────────────────┘
         │      │
         ▼      ▼
┌──────────────────────────┐
│ v1.2-02 BYOK (完整版)    │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│ v1.2 发布 Milestone      │
└──────────────────────────┘
```

---

## 📅 调整后的时间线

### v1.1 (预计 6-8 周)

| 任务 | 原估计 | 调整后 | 变化 |
|------|--------|--------|------|
| v1.1-01 性能优化 | 3-4 天 | 4-5 天 | +1 天 |
| v1.1-02 持久化 | 5-7 天 | 7-9 天 | +2 天 |
| v1.1-03 Sentry | 2-3 天 | 2-3 天 | 不变 |
| DEBT-01 测试 (Phase 1) | - | 5 天 | 新增 |
| **v1.1 总计** | 10-14 天 | **18-22 天** | +8 天 |

### v1.2 (预计 3-4 月)

| 任务 | 原估计 | 调整后 | 变化 |
|------|--------|--------|------|
| v1.2-01 多租户 | 10-15 天 | 15-20 天 | +5 天 |
| v1.2-02 BYOK | 5-7 天 | 8-10 天 | +3 天 |
| v1.2-03 任务队列 | 7-10 天 | 10-12 天 | +2 天 |
| DEBT-01 测试 (Phase 2) | - | 5 天 | 新增 |
| DEBT-02 API 文档 | 3-5 天 | 3-5 天 | 不变 |
| **v1.2 总计** | 25-37 天 | **41-52 天** | +16 天 |

### v2.0 (预计 6-8 月)

| 任务 | 原估计 | 调整后 | 变化 |
|------|--------|--------|------|
| v2.0-01 模型扩展 | 15-20 天 | 10-12 天 | -8 天 (精简范围) |
| v2.0-02 协作功能 | 20-30 天 | 25 天 (不含实时协作) | 精简 |
| v2.0-03 移动端 | 10-15 天 | 10-15 天 | 不变 |
| **v2.0 总计** | 45-65 天 | **45-52 天** | 略减 |

---

## 🎯 最终建议

### 1. 优先级调整

```
高优先级 (P0):
├── v1.1-02 工作流持久化 (用户痛点)
├── DEBT-01 测试体系 (质量基础)
└── v1.2-03 任务队列 (架构瓶颈)

中高优先级 (P1):
├── v1.1-01 性能优化
├── v1.1-03 Sentry
├── v1.2-01 多租户
└── DEBT-02 API 文档

中优先级 (P1.5):
└── v1.2-02 BYOK (安全敏感，需额外评审)

低优先级 (P2):
├── v2.0-01 模型扩展
├── v2.0-02 协作功能 (精简版)
└── v2.0-03 移动端
```

### 2. 关键决策点

| 决策 | 选项 | 建议 |
|------|------|------|
| BYOK 加密方案 | 自研 vs Supabase Vault | 先调研 Vault，3 天内决定 |
| 任务队列部署 | Vercel Hobby vs Pro | 评估成本，预计需升级 Pro |
| 测试策略 | 全覆盖 vs 核心路径 | 先核心路径，50% 覆盖率 |
| 协作实时功能 | v2.0 vs v2.1 | 延后到 v2.1 |

### 3. 风险缓解措施

| 风险 | 措施 | 责任人 |
|------|------|--------|
| BYOK 密钥泄露 | 安全评审 + 审计日志 | 待分配 |
| Vercel 超时 | 预算 Pro 升级费用 | 待分配 |
| 工时超支 | 每周进度检查点 | PM |
| 技术债积累 | 测试与功能并行开发 | Tech Lead |

### 4. 下一步行动

1. **本周内**: 完成 v1.1-02 数据模型评审
2. **本周内**: 评估 Supabase Vault 是否满足 BYOK 需求
3. **下周**: 启动 v1.1-01 性能优化
4. **持续**: 测试体系与功能开发并行

---

## 📎 附录

### A. 成本估算

| 服务 | 当前 | v1.2 后 | 备注 |
|------|------|---------|------|
| Vercel | $0 (Hobby) | $20/月 (Pro) | 任务队列需要 |
| Supabase | $0 (Free) | $25/月 (Pro) | 多租户 + Realtime |
| Sentry | $0 (Free) | $0 | 免费额度足够 |
| Upstash QStash | $0 (Free) | $0 | 免费额度足够 |
| **月总计** | $0 | **~$45/月** | |

### B. 团队技能要求

| 技能 | v1.1 | v1.2 | v2.0 |
|------|------|------|------|
| React/TypeScript | ✅ | ✅ | ✅ |
| FastAPI/Python | ✅ | ✅ | ✅ |
| Supabase/PostgreSQL | ✅ | ⭐⭐ | ⭐⭐ |
| 安全/加密 | - | ⭐⭐ | - |
| 消息队列 | - | ⭐ | - |
| 移动端开发 | - | - | ⭐ |

---

**审核人**: AI Reviewer  
**下次审核**: v1.1 发布后



# 多 Agent 工作流推进方案（指挥用作战单）

> **状态**: 📋 **规划中**  
> **完成度**: 0%  
> **最后更新**: 2026-01-08  
> **适用范围**: Phase 1 (稳定加固) + Phase 2 (生产就绪)

---

## ⚠️ 重要说明

本文档针对**当前活跃阶段**（Phase 1 和 Phase 2）的任务，而非已完成的 v1.0 MVP 阶段。

- **v1.0 已完成工作包**: 已归档至 `docs/archive/legacy-workpacks/`，仅作历史参考
- **当前活跃任务**: Phase 1 (工作流持久化、测试体系、Sentry) + Phase 2 (安全改进)
- **详细执行方案**: 参见 [MULTI_AGENT_EXECUTION_PLAN.md](./MULTI_AGENT_EXECUTION_PLAN.md)

---

## 0. 使用方式（给 Agent 下指令）

- 指定角色：`Expert (Claude)` / `Backend (Codex)` / `Frontend (Gemini)`
- 把对应的 **PLAN 文档**或 **Stage 详细方案**整份发送给该 Agent
- 要求"只改工作包范围内文件，并按验收 Checklist 交付证据"
- 若需跨包改动：先更新相关 PLAN 的"依赖/输入输出/验收"，再改实现

---

## 1. 当前阶段任务总览

### Phase 1: 稳定加固 (P0 - 必须完成)

| 任务 | 工时 | 负责 | 详细方案 |
|------|------|------|----------|
| 1.1 工作流持久化 | 5-7天 | Backend + Frontend | [PHASE_1_IMPLEMENTATION.md](../phase-1/PHASE_1_IMPLEMENTATION.md#11-工作流持久化) |
| 1.2 测试体系基础 | 10-15天 | Backend + Frontend | [PHASE_1_IMPLEMENTATION.md](../phase-1/PHASE_1_IMPLEMENTATION.md#12-测试体系基础) |
| 1.3 Sentry 监控 | 2-3天 | Joint | [PHASE_1_IMPLEMENTATION.md](../phase-1/PHASE_1_IMPLEMENTATION.md#13-sentry-监控) |

### Phase 2: 生产就绪 (P1 - 安全加固)

| 任务 | 优先级 | 负责 | 详细方案 |
|------|--------|------|----------|
| SEC-01 CORS 配置 | P0 | Backend | [SECURITY_IMPROVEMENT_PLAN.md](../phase-2/SECURITY_IMPROVEMENT_PLAN.md#-sec-01-cors-配置过于宽松) |
| SEC-02 BYOK 密钥存储 | P0 | Backend | [SECURITY_IMPROVEMENT_PLAN.md](../phase-2/SECURITY_IMPROVEMENT_PLAN.md#-sec-02-byok-密钥存储安全) |
| SEC-03 Sentry 敏感信息 | P1 | Joint | [SECURITY_IMPROVEMENT_PLAN.md](../phase-2/SECURITY_IMPROVEMENT_PLAN.md#-sec-03-sentry-敏感信息泄露) |
| SEC-04 JWT 验证 | P1 | Backend | [SECURITY_IMPROVEMENT_PLAN.md](../phase-2/SECURITY_IMPROVEMENT_PLAN.md#-sec-04-jwt-验证配置) |
| SEC-05 API 速率限制 | P1 | Backend | [SECURITY_IMPROVEMENT_PLAN.md](../phase-2/SECURITY_IMPROVEMENT_PLAN.md#-sec-05-api-速率限制缺失) |
| SEC-06 日志敏感信息 | P1 | Backend | [SECURITY_IMPROVEMENT_PLAN.md](../phase-2/SECURITY_IMPROVEMENT_PLAN.md#-sec-06-日志敏感信息) |
| SEC-07 RLS 策略验证 | P2 | Backend | [SECURITY_IMPROVEMENT_PLAN.md](../phase-2/SECURITY_IMPROVEMENT_PLAN.md#-sec-07-rls-策略验证) |
| SEC-08 依赖包安全 | P2 | Joint | [SECURITY_IMPROVEMENT_PLAN.md](../phase-2/SECURITY_IMPROVEMENT_PLAN.md#-sec-08-依赖包安全) |

---

## 2. Phase 1 执行顺序与窗口分配

### 2.1 执行时序

```
Week 1-2: 工作流持久化
├── Stage 1.1: Supabase 数据表设计 (Expert审核 → Backend实现 → Expert验收)
├── Stage 1.2: 后端API + 前端Hook (并行: Backend + Frontend)
└── Stage 1.3: 组件改造 (Frontend实现 → Expert审核)

Week 2-3: 测试体系 (与Stage 1.2并行启动)
├── Stage 2.1: 后端测试 + 前端测试 (并行: Backend + Frontend)
└── Stage 2.2: CI配置 (Expert配置 → Expert审核)

Week 3-4: Sentry 监控
├── Stage 3.1: Sentry集成 (并行: Backend + Frontend)
└── Stage 3.2: 告警规则配置 (Expert配置)
```

### 2.2 窗口编号与Agent分配

| 窗口ID | Agent | Stage | 任务 | 状态 |
|--------|-------|-------|------|------|
| #E1 | Expert (Claude) | 1.1-1.3 | 数据表审核、联调审核、最终验收 | 待启动 |
| #B1 | Backend (Codex) | 1.1 | Supabase 数据表实现 | 待启动 |
| #B2 | Backend (Codex) | 1.2 | 后端 API 实现 | 待启动 |
| #F1 | Frontend (Gemini) | 1.2-1.3 | Hook实现、组件改造 | 待启动 |
| #B3 | Backend (Codex) | 2.1 | 后端测试 (pytest) | 待启动 |
| #F2 | Frontend (Gemini) | 2.1 | 前端测试 (vitest) | 待启动 |
| #E2 | Expert (Claude) | 2.2, 3.2 | CI配置、告警规则配置 | 待启动 |
| #B4 | Backend (Codex) | 3.1 | 后端 Sentry 集成 | 待启动 |
| #F3 | Frontend (Gemini) | 3.1 | 前端 Sentry 集成 | 待启动 |

---

## 3. Phase 2 执行顺序（Phase 1 完成后启动）

### 3.1 优先级排序

**P0 优先级（立即执行）**:
1. SEC-01: CORS 配置修复 (Backend)
2. SEC-02: BYOK 密钥存储安全 (Backend，依赖 v1.2-02)

**P1 优先级（Phase 1 完成后）**:
3. SEC-03: Sentry 敏感信息过滤 (Joint，依赖 Phase 1.3)
4. SEC-04: JWT 验证增强 (Backend)
5. SEC-05: API 速率限制 (Backend)
6. SEC-06: 日志敏感信息过滤 (Backend)

**P2 优先级（后续迭代）**:
7. SEC-07: RLS 策略验证 (Backend，依赖 v1.2-01)
8. SEC-08: 依赖包安全扫描 (Joint)

### 3.2 窗口分配建议

| 窗口ID | Agent | 任务 | 状态 |
|--------|-------|------|------|
| #B5 | Backend (Codex) | SEC-01 CORS 修复 | 待启动 |
| #B6 | Backend (Codex) | SEC-02 BYOK 密钥存储 | 待启动 |
| #J1 | Joint (Codex+Gemini) | SEC-03 Sentry 过滤 | 待启动 |
| #B7 | Backend (Codex) | SEC-04 JWT 验证 | 待启动 |
| #B8 | Backend (Codex) | SEC-05 Rate Limiting | 待启动 |
| #B9 | Backend (Codex) | SEC-06 日志过滤 | 待启动 |

---

## 4. Agent 启动指令（Phase 1）

> 使用方式：在对应窗口发送整段指令；附上对应的 PLAN 文档或 Stage 详细方案。

### Stage 1.1: 工作流持久化 - 数据表设计

```text
【#E1 Expert / Stage 1.1 数据表审核】
角色：Expert (Claude)
任务：审核工作流持久化数据表设计方案，检查 RLS 策略、索引设计、性能考虑
文档：docs/active/phase-1/PHASE_1_IMPLEMENTATION.md (Section 1.1, Step 1)
输出：审核结论、优化建议、最终确认的 SQL DDL
```

```text
【#B1 Backend / Stage 1.1 数据表实现】
角色：Backend (Codex)
任务：在 Supabase 中创建 workflow_sessions 和 video_tasks 表，配置 RLS 策略
文档：docs/active/phase-1/PHASE_1_IMPLEMENTATION.md (Section 1.1, Step 1)
输出：SQL DDL 脚本、执行结果、RLS 策略验证
```

### Stage 1.2: 工作流持久化 - API + Hook

```text
【#B2 Backend / Stage 1.2 后端API实现】
角色：Backend (Codex)
任务：实现 /api/v1/sessions 和 /api/v1/video/tasks 后端接口
文档：docs/active/phase-1/PHASE_1_IMPLEMENTATION.md (Section 1.1, Step 2)
输出：API 实现、单元测试、API 文档
```

```text
【#F1 Frontend / Stage 1.2 Hook实现】
角色：Frontend (Gemini)
任务：实现 useWorkflowPersistence Hook，支持会话保存和恢复
文档：docs/active/phase-1/PHASE_1_IMPLEMENTATION.md (Section 1.1, Step 3)
输出：Hook 实现、类型定义、使用示例
```

### Stage 1.3: 工作流持久化 - 组件改造

```text
【#F1 Frontend / Stage 1.3 组件改造】
角色：Frontend (Gemini)
任务：改造 GridWorkflow 组件，集成 useWorkflowPersistence Hook
文档：docs/active/phase-1/PHASE_1_IMPLEMENTATION.md (Section 1.1, Step 4)
输出：组件改造、状态恢复验证、刷新测试
```

### Stage 2.1: 测试体系

```text
【#B3 Backend / Stage 2.1 后端测试】
角色：Backend (Codex)
任务：配置 pytest，编写 Services 和 API 单元测试，目标覆盖率 > 50%
文档：docs/active/phase-1/PHASE_1_IMPLEMENTATION.md (Section 1.2)
输出：pytest 配置、测试用例、覆盖率报告
```

```text
【#F2 Frontend / Stage 2.1 前端测试】
角色：Frontend (Gemini)
任务：配置 Vitest，编写组件和 Hook 测试，目标覆盖率 > 50%
文档：docs/active/phase-1/PHASE_1_IMPLEMENTATION.md (Section 1.2)
输出：vitest 配置、测试用例、覆盖率报告
```

```text
【#E2 Expert / Stage 2.2 CI配置】
角色：Expert (Claude)
任务：配置 GitHub Actions CI，集成测试和覆盖率检查
文档：docs/active/phase-1/PHASE_1_IMPLEMENTATION.md (Section 1.2, Step 4)
输出：CI 配置、测试通过验证、覆盖率报告
```

### Stage 3.1: Sentry 监控

```text
【#B4 Backend / Stage 3.1 后端Sentry集成】
角色：Backend (Codex)
任务：集成 sentry-sdk，配置错误追踪和性能监控
文档：docs/active/phase-1/PHASE_1_IMPLEMENTATION.md (Section 1.3, Step 2)
输出：Sentry 集成、错误上报验证、性能追踪验证
```

```text
【#F3 Frontend / Stage 3.1 前端Sentry集成】
角色：Frontend (Gemini)
任务：集成 @sentry/react，配置错误边界和性能监控
文档：docs/active/phase-1/PHASE_1_IMPLEMENTATION.md (Section 1.3, Step 3)
输出：Sentry 集成、ErrorBoundary 实现、错误上报验证
```

```text
【#E2 Expert / Stage 3.2 告警规则配置】
角色：Expert (Claude)
任务：在 Sentry Dashboard 配置错误告警和性能告警规则
文档：docs/active/phase-1/PHASE_1_IMPLEMENTATION.md (Section 1.3, Step 4)
输出：告警规则配置、通知渠道验证
```

---

## 5. Agent 启动指令（Phase 2 - 安全改进）

### P0 优先级任务

```text
【#B5 Backend / SEC-01 CORS修复】
角色：Backend (Codex)
任务：修复 CORS 配置，生产环境强制配置，禁止默认 "*"
文档：docs/active/phase-2/SECURITY_IMPROVEMENT_PLAN.md (Section SEC-01)
输出：CORS 配置修复、生产环境验证、安全测试
```

```text
【#B6 Backend / SEC-02 BYOK密钥存储】
角色：Backend (Codex)
任务：实现 BYOK 密钥加密存储，使用 Fernet 加密，密钥存储在 Supabase Vault
文档：docs/active/phase-2/SECURITY_IMPROVEMENT_PLAN.md (Section SEC-02)
输出：密钥加密实现、Supabase Vault 集成、安全验证
```

### P1 优先级任务

```text
【#J1 Joint / SEC-03 Sentry敏感信息过滤】
角色：Joint (Codex + Gemini)
任务：在 Sentry 集成中添加敏感信息过滤，移除 API Key、Token 等
文档：docs/active/phase-2/SECURITY_IMPROVEMENT_PLAN.md (Section SEC-03)
输出：beforeSend 过滤函数、敏感信息验证
```

```text
【#B7 Backend / SEC-04 JWT验证增强】
角色：Backend (Codex)
任务：增强 JWT 验证，添加 issuer 验证、audience 验证
文档：docs/active/phase-2/SECURITY_IMPROVEMENT_PLAN.md (Section SEC-04)
输出：JWT 验证增强、安全测试
```

```text
【#B8 Backend / SEC-05 Rate Limiting】
角色：Backend (Codex)
任务：实现 API 速率限制，使用 slowapi 或自定义中间件
文档：docs/active/phase-2/SECURITY_IMPROVEMENT_PLAN.md (Section SEC-05)
输出：Rate Limiting 实现、限流测试、性能测试
```

```text
【#B9 Backend / SEC-06 日志敏感信息过滤】
角色：Backend (Codex)
任务：增强日志过滤，移除敏感信息（API Key、Token、完整 Prompt）
文档：docs/active/phase-2/SECURITY_IMPROVEMENT_PLAN.md (Section SEC-06)
输出：日志过滤实现、敏感信息验证
```

---

## 6. 验收与门禁执行

### 6.1 全局冻结项（必须遵守）

所有 Agent 必须遵守 [FROZEN_INVARIANTS.md](./FROZEN_INVARIANTS.md) 定义的约束：

- ✅ 统一响应结构 `{ok, data, error}`
- ✅ Prompt 单一来源（后端）
- ✅ API Client 单入口（前端）
- ✅ UI 文案仅简体中文
- ✅ 安全门禁（密钥脱敏、外部调用隔离、错误脱敏）
- ✅ 错误码规范
- ✅ 任务状态枚举

**违反冻结项视为直接退回**

### 6.2 验收 Checklist

每个 Stage 完成后，Agent 需要提供：

- [ ] 代码实现符合工作包范围
- [ ] 通过单元测试（如有）
- [ ] 符合全局冻结项
- [ ] 文档已更新（如有需要）
- [ ] 验收要点已满足（见各 PLAN 文档）

---

## 7. Git 提交流程

> **仓库性质**:
> - **Gitee**: 内部开发主仓库，所有日常开发在此进行
> - **GitHub**: 快速部署临时仓库，仅用于 Vercel 等平台部署

- 每个 Agent 在对应窗口任务通过验收后，默认执行一次提交与推送，保持可审计历史
- 推荐分支/提交规范：
  - 分支：`feature/<Stage>-<window>`（如 `feature/stage-1.1-B1`），合并到 `main` 时走 PR
  - 提交信息：`<window> <Stage> <summary>`（如 `#B1 Stage-1.1 implement workflow tables`）
- 安全与清单：
  - `.env`、密钥、私有证书严禁入库；先确认 `.gitignore` 覆盖
  - 提交前附验收要点：成功/失败用例、风险条目对应的证据
- 推送命令：
  - **日常开发**: `git push gitee main`（推送到 Gitee 主仓库）
  - **需要部署时**: `git push github main`（同步到 GitHub 部署仓库）

---

## 8. 参考文档

### Phase 1 详细方案
- [PHASE_1_IMPLEMENTATION.md](../phase-1/PHASE_1_IMPLEMENTATION.md) - Phase 1 完整实施方案
- [PLAN-v1.1-02_WORKFLOW_PERSISTENCE.md](../../plan/PLAN-v1.1-02_WORKFLOW_PERSISTENCE.md) - 工作流持久化详细计划
- [PLAN-DEBT-01_TESTING.md](../../plan/PLAN-DEBT-01_TESTING.md) - 测试体系建设详细计划
- [PLAN-v1.1-03_SENTRY_MONITORING.md](../../plan/PLAN-v1.1-03_SENTRY_MONITORING.md) - Sentry 监控详细计划

### Phase 2 详细方案
- [SECURITY_IMPROVEMENT_PLAN.md](../phase-2/SECURITY_IMPROVEMENT_PLAN.md) - 安全改进完整方案

### 多 Agent 执行方案
- [MULTI_AGENT_EXECUTION_PLAN.md](./MULTI_AGENT_EXECUTION_PLAN.md) - 详细执行方案和 Agent Prompt
- [FROZEN_INVARIANTS.md](./FROZEN_INVARIANTS.md) - 全局冻结项
- [ROADMAP_MULTI_AGENT.md](./ROADMAP_MULTI_AGENT.md) - 多 Agent 路线图

### 主计划
- [MASTER_PLAN_2026.md](../../MASTER_PLAN_2026.md) - 项目主计划

---

**文档维护者**: AI Architect  
**最后更新**: 2026-01-08

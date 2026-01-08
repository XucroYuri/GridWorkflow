# WP-GW-09_AUTH_SUPABASE（认证与云端数据：Supabase）

**负责人团队**：Codex（后端）+ Gemini（前端）

**目标**：接入 Supabase Auth 与 Postgres，使核心接口只对登录用户开放，并实现基础按用户隔离的数据访问。

---

## 输入

- [PLAN-09_SUPABASE.md](../../PLAN-09_SUPABASE.md)
- [PRECHECK-SEC_ARCH_AGENT.md](../../PRECHECK-SEC_ARCH_AGENT.md)

---

## 输出（交付物）

- 前端 Supabase Auth 登录流程（使用 ANON KEY）
- 后端 JWT 校验中间件，提取 `user_id`
- 基本任务/媒体索引表与 RLS 策略草案

---

## 冻结约束（必须）

> **全局冻结项**：统一遵守 [FROZEN_INVARIANTS.md](../FROZEN_INVARIANTS.md)

**本工作包特定约束**：
- Service Role Key 仅在后端使用，不暴露到前端
- 核心接口必须校验 JWT
- 数据表按 `user_id` 隔离（RLS 策略）
- JWT 校验失败返回 `UNAUTHORIZED` 错误码

---

## Agent 启动上下文（复制即用）

```text
你是 Codex/Gemini 联合 Agent（认证与云端数据负责人）。
目标：接入 Supabase 认证与最小数据索引，使核心接口需要登录才能访问。
验收：未登录无法调用核心接口；登录后可获得 user_id 并仅访问自己的任务与媒体记录。
```

---

## 验收 Checklist

- 登录流程可用，前端拿到 JWT
- 后端可校验 JWT 并提取 user_id
- 未登录访问核心接口被拒绝
- 数据表按用户隔离，RLS 生效

---

## 回滚策略

- 若 Supabase 集成不稳定：短期内仅使用本地/内存索引，保持认证逻辑清晰


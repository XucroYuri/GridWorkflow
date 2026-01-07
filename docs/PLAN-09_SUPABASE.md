# PLAN-09_SUPABASE (认证与云端数据)

**目标**: 使用 Supabase 提供用户认证与云端数据存储，实现全云端运行。

## 范围
**包含**:
- Supabase Auth 登录流程
- 后端 JWT 校验
- 用户/任务/媒体索引写入 Supabase Postgres

**不包含**:
- 复杂的多角色权限模型
- 自建 Auth

## 配置项
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY` (前端)
- `SUPABASE_SERVICE_ROLE_KEY` (后端，仅服务端)

## 关键实现点
- 前端使用 `SUPABASE_ANON_KEY` 获取 JWT
- 后端校验 JWT 并提取 `user_id`
- Row Level Security (RLS) 绑定 `user_id`
- 媒体 URL 与任务记录绑定用户

## Agent 风险点
- 不要把 Service Role Key 放到前端
- 不要绕过 JWT 校验直接访问数据表

## 验收
- 登录后可获得 `user_id`
- 未登录无法调用核心接口
- 数据表按用户隔离

## PDCA 钩子
- **Plan**: 明确认证与数据隔离的边界（所有核心接口必须校验 JWT，所有数据表按 `user_id`/`tenant_id` 隔离）。
- **Do**: 打通 Supabase Auth 登录流程与后端 JWT 校验，落地最小任务/媒体索引表。
- **Check**: 验证未登录用户无法访问核心接口；验证不同用户的任务与媒体记录不会互相泄露。
- **Act**: 若发现权限模型过于复杂或易错，先简化为单一角色模型，再逐步引入更多角色或租户概念。

## Agent 上下文注入包
- **负责人团队**: Joint（Codex + Gemini）
- **本阶段目标**: 接入 Supabase Auth 与后端 JWT 校验，实现按用户隔离的最小数据索引。
- **输入**: 本文档、`PRECHECK-SEC_ARCH_AGENT.md`、Supabase 配置项与 RLS 约束。
- **输出**: 前端登录流程、后端 JWT 校验、最小任务/媒体表与 RLS 方案说明。
- **冻结约束**:
  - `SUPABASE_SERVICE_ROLE_KEY` 仅后端使用
  - 核心接口必须校验 JWT
  - 数据必须按 `user_id` 隔离
- **禁止事项（高风险）**:
  - 把 Service Role Key 放到前端
  - 绕过 JWT 校验直接访问数据表
- **验收 Checklist**:
  - 登录后获得 `user_id`
  - 未登录无法调用核心接口
  - 数据表按用户隔离（RLS 生效）
- **回滚策略**:
  - 若云端数据未就绪，短期以内存/本地索引兜底，保持鉴权链路不变。

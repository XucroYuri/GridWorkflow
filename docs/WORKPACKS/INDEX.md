# WORKPACKS (多 Agent 可执行工作包索引)

**目标**：将 `docs/` 下的文档体系组织为可分配、可并行、可验收的工作包（Work Packages）。每个工作包提供独立上下文启动信息，便于不同 Agent 在不同上下文窗口中独立执行并交付。

---

## 0. 全局冻结项（门禁）

> ⚠️ **重要**：所有工作包必须遵守全局冻结项，违反者直接退回。

- **[FROZEN_INVARIANTS.md](FROZEN_INVARIANTS.md)** — 统一响应结构、Prompt 单一来源、API Client 单入口、UI 中文、输出语种可控、安全门禁

---

## 1. 使用方式（最小流程）

1. 选择一个工作包（WP-xx）。
2. **阅读 [FROZEN_INVARIANTS.md](FROZEN_INVARIANTS.md) 确认全局约束**。
3. 将该工作包中的"Agent 启动上下文（复制即用）"整体提供给对应团队的 Agent（Codex 后端 / Gemini 前端 / Joint）。
4. Agent 只在工作包声明的范围内修改文件，并按"验收 Checklist"产出证据。
5. 若需跨包变更，先更新工作包的"依赖/输入输出/验收"，再实施改动。

---

## 2. GridWorkflow（新项目：多 Agent 主战场）

### 2.1 治理与门禁
- [WP-GW-00_GOVERNANCE](gridworkflow/WP-GW-00_GOVERNANCE.md) — 治理与多 Agent 协作门禁
- [WP-GW-90_RISK_REGISTER](gridworkflow/WP-GW-90_RISK_REGISTER.md) — 风险清单与兜底策略

### 2.2 骨架与基座
- [WP-GW-01_BOOTSTRAP](gridworkflow/WP-GW-01_BOOTSTRAP.md) — 前后端最小可运行骨架

### 2.3 后端主干
- [WP-GW-02_BACKEND_PROXY](gridworkflow/WP-GW-02_BACKEND_PROXY.md) — AI 网关代理（文本/图像）
- [WP-GW-03_VIDEO_SORA2](gridworkflow/WP-GW-03_VIDEO_SORA2.md) — 视频生成与状态查询
- [WP-GW-04_STORAGE_COS](gridworkflow/WP-GW-04_STORAGE_COS.md) — 媒体统一出站（COS）

### 2.4 前端主干
- [WP-GW-05_FRONTEND_SHELL](gridworkflow/WP-GW-05_FRONTEND_SHELL.md) — UI 基座与 Light Theme
- [WP-GW-07_VIDEO_STUDIO_UI](gridworkflow/WP-GW-07_VIDEO_STUDIO_UI.md) — 视频工作台 UI

### 2.5 工作流（契约先行）
- [WP-GW-06A_FLOW_CONTRACT](gridworkflow/WP-GW-06A_FLOW_CONTRACT.md) — 四步工作流契约冻结 ⚡
- [WP-GW-06_GRIDWORKFLOW_FLOW](gridworkflow/WP-GW-06_GRIDWORKFLOW_FLOW.md) — 四步闭环实现

### 2.6 鉴权与安全
- [WP-GW-09_AUTH_SUPABASE](gridworkflow/WP-GW-09_AUTH_SUPABASE.md) — Supabase 认证与数据隔离
- [WP-GW-10_IP_ALLOWLIST](gridworkflow/WP-GW-10_IP_ALLOWLIST.md) — IP 白名单弱鉴权

### 2.7 部署与剥离
- [WP-GW-08_DEPLOY_VERCEL](gridworkflow/WP-GW-08_DEPLOY_VERCEL.md) — Vercel 部署适配
- [WP-GW-11_DETACH_REPO](gridworkflow/WP-GW-11_DETACH_REPO.md) — 仓库剥离（暂停）

### 2.8 路线图与协作
- [ROADMAP_MULTI_AGENT](ROADMAP_MULTI_AGENT.md) — 多 Agent 分步开发路线图
- [WORKFLOW_MULTI_AGENT](WORKFLOW_MULTI_AGENT.md) — 多 Agent 工作流推进方案

---

## 3. Grid-Cine Director（母体项目：参考与审计）

- [MAP_SPECS_TO_WORKPACKS](MAP_SPECS_TO_WORKPACKS.md)
- `../AUDIT_REPORT.md`
- `../FULL_PROJECT_CODE_AUDIT_REPORT.md`
- `../specs/`（架构参考文档）


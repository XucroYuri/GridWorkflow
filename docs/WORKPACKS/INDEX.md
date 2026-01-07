# WORKPACKS (多 Agent 可执行工作包索引)

**目标**：将 `docs/` 下的文档体系组织为可分配、可并行、可验收的工作包（Work Packages）。每个工作包提供独立上下文启动信息，便于不同 Agent 在不同上下文窗口中独立执行并交付。

---

## 1. 使用方式（最小流程）

1. 选择一个工作包（WP-xx）。
2. 将该工作包中的“Agent 启动上下文（复制即用）”整体提供给对应团队的 Agent（Codex 后端 / Gemini 前端 / Joint）。
3. Agent 只在工作包声明的范围内修改文件，并按“验收 Checklist”产出证据。
4. 若需跨包变更，先更新工作包的“依赖/输入输出/验收”，再实施改动。

---

## 2. GridWorkflow（新项目：多 Agent 主战场）

- [WP-GW-00_GOVERNANCE](gridworkflow/WP-GW-00_GOVERNANCE.md)
- [WP-GW-01_BOOTSTRAP](gridworkflow/WP-GW-01_BOOTSTRAP.md)
- [WP-GW-02_BACKEND_PROXY](gridworkflow/WP-GW-02_BACKEND_PROXY.md)
- [WP-GW-03_VIDEO_SORA2](gridworkflow/WP-GW-03_VIDEO_SORA2.md)
- [WP-GW-04_STORAGE_COS](gridworkflow/WP-GW-04_STORAGE_COS.md)
- [WP-GW-05_FRONTEND_SHELL](gridworkflow/WP-GW-05_FRONTEND_SHELL.md)
- [WP-GW-06A_FLOW_CONTRACT](gridworkflow/WP-GW-06A_FLOW_CONTRACT.md)
- [WP-GW-06_GRIDWORKFLOW_FLOW](gridworkflow/WP-GW-06_GRIDWORKFLOW_FLOW.md)
- [WP-GW-07_VIDEO_STUDIO_UI](gridworkflow/WP-GW-07_VIDEO_STUDIO_UI.md)
- [WP-GW-08_DEPLOY_VERCEL](gridworkflow/WP-GW-08_DEPLOY_VERCEL.md)
- [WP-GW-09_AUTH_SUPABASE](gridworkflow/WP-GW-09_AUTH_SUPABASE.md)
- [WP-GW-10_IP_ALLOWLIST](gridworkflow/WP-GW-10_IP_ALLOWLIST.md)
- [WP-GW-11_DETACH_REPO](gridworkflow/WP-GW-11_DETACH_REPO.md)
- [WP-GW-90_RISK_REGISTER](gridworkflow/WP-GW-90_RISK_REGISTER.md)
- [ROADMAP_MULTI_AGENT](ROADMAP_MULTI_AGENT.md)

---

## 3. Grid-Cine Director（母体项目：参考与审计）

- [MAP_SPECS_TO_WORKPACKS](MAP_SPECS_TO_WORKPACKS.md)
- `../AUDIT_REPORT.md`
- `../FULL_PROJECT_CODE_AUDIT_REPORT.md`
- `../specs/`（架构参考文档）


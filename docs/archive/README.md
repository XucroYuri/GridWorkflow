# 📦 归档文档

> **归档日期**: 2026-01-08  
> **说明**: 本目录存放已完成或不再适用的历史文档，仅作参考

---

## 📁 目录结构

```
archive/
├── README.md                    # 本文件
├── v1.0-completed/              # 已完成的 v1.0 版本计划
│   ├── PLAN-00_BOOTSTRAP.md
│   ├── PLAN-01_BACKEND_PROXY.md
│   ├── PLAN-02_VIDEO_SORA2.md
│   ├── PLAN-03_STORAGE_COS.md
│   ├── PLAN-04_FRONTEND_SHELL.md
│   ├── PLAN-05_GRIDWORKFLOW_FLOW.md
│   ├── PLAN-06_VIDEO_STUDIO_UI.md
│   ├── PLAN-07_DATA_FUTURE_MYSQL.md (过时)
│   ├── PLAN-08_VERCEL_DEPLOY.md
│   ├── PLAN-09_SUPABASE.md
│   ├── PLAN-10_IP_ALLOWLIST.md
│   ├── PLAN-11_MIGRATION_ACTIONS.md
│   └── PLAN-12_DETACH_TO_NEW_REPO.md
├── legacy-workpacks/            # 旧的工作包执行证据
│   ├── gridworkflow/            # GridWorkflow 项目工作包
│   │   ├── WP-GW-*.md           # 工作包定义
│   │   ├── EVIDENCE_WP-*.md     # 执行证据
│   │   └── evidence/            # SQL 脚本等证据文件
│   ├── INDEX.md                 # 工作包索引
│   └── MAP_SPECS_TO_WORKPACKS.md
├── AGENT-00_WORKSTREAMS.md      # 旧的 Agent 协作规范
├── PDCA-00_PROJECT_GOVERNANCE.md # PDCA 治理协议
├── PRECHECK-SEC_ARCH_AGENT.md   # 安全/架构门禁清单
├── AUDIT_REPORT.md              # 母体仓库遗留审计
└── FULL_PROJECT_CODE_AUDIT_REPORT.md # 母体仓库审计
```

---

## 📋 归档原因

### v1.0-completed/ (已完成的计划)

| 文档 | 状态 | 说明 |
|------|------|------|
| PLAN-00_BOOTSTRAP.md | ✅ 完成 | 项目骨架已建立 |
| PLAN-01_BACKEND_PROXY.md | ✅ 完成 | AI Gateway 代理已实现 |
| PLAN-02_VIDEO_SORA2.md | ✅ 完成 | 视频生成接口已实现 |
| PLAN-03_STORAGE_COS.md | ✅ 完成 | COS 存储已集成 |
| PLAN-04_FRONTEND_SHELL.md | ✅ 完成 | 前端基座已迁移 |
| PLAN-05_GRIDWORKFLOW_FLOW.md | ✅ 完成 | 四步工作流已实现 |
| PLAN-06_VIDEO_STUDIO_UI.md | ✅ 完成 | 视频工作台 UI 已完成 |
| PLAN-07_DATA_FUTURE_MYSQL.md | ⚪ 过时 | 已选用 Supabase PostgreSQL |
| PLAN-08_VERCEL_DEPLOY.md | ✅ 完成 | Vercel 部署已适配 |
| PLAN-09_SUPABASE.md | ✅ 完成 | Supabase 认证已集成 |
| PLAN-10_IP_ALLOWLIST.md | ✅ 完成 | IP 白名单已实现 |
| PLAN-11_MIGRATION_ACTIONS.md | ✅ 完成 | 迁移已完成 |
| PLAN-12_DETACH_TO_NEW_REPO.md | ✅ 完成 | 仓库已独立 |

### legacy-workpacks/ (旧工作包)

| 内容 | 说明 |
|------|------|
| 工作包定义 (WP-GW-*.md) | v1.0 开发时的任务分解，已完成 |
| 执行证据 (EVIDENCE_*.md) | 记录了 v1.0 各阶段的实施过程 |
| SQL 脚本 (evidence/*.sql) | Supabase RLS 配置等 |

### 其他过时文档

| 文档 | 原因 | 替代文档 |
|------|------|----------|
| AGENT-00_WORKSTREAMS.md | 已整合到新方案 | active/multi-agent/MULTI_AGENT_EXECUTION_PLAN.md |
| PDCA-00_PROJECT_GOVERNANCE.md | 已整合到新方案 | active/multi-agent/FROZEN_INVARIANTS.md |
| AUDIT_REPORT.md | 母体仓库遗留 | report/CODE_AUDIT_REPORT_*.md |
| FULL_PROJECT_CODE_AUDIT_REPORT.md | 母体仓库审计 | report/CODE_AUDIT_REPORT_*.md |

---

## ⚠️ 使用说明

1. **这些文档不应再被修改**
2. **仅作为历史决策和演进参考**
3. **如需类似功能，请参考当前活跃文档**：
   - 多Agent协作 → `docs/active/multi-agent/`
   - 迭代计划 → `docs/plan/`
   - 指导手册 → `docs/guides/`

---

## 🔍 查找历史决策

如果你需要了解某个功能的历史决策背景：

1. **查看对应的已完成计划** → `v1.0-completed/PLAN-*.md`
2. **查看执行证据** → `legacy-workpacks/gridworkflow/EVIDENCE_*.md`
3. **查看工作包定义** → `legacy-workpacks/gridworkflow/WP-*.md`

---

**归档人**: AI Architect  
**最后更新**: 2026-01-08

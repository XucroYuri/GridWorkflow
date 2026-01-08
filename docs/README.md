# GridWorkflow 文档中心

> **更新日期**: 2026-01-08  
> **文档版本**: 2.0  
> **项目阶段**: MVP 完成 → 生产加固

---

## 📖 文档导航

### 🎯 核心文档

| 文档 | 说明 | 优先阅读 |
|------|------|----------|
| [MASTER_PLAN_2026.md](./MASTER_PLAN_2026.md) | 项目主计划，包含路线图和阶段规划 | ⭐⭐⭐ |
| [CODE_REVIEW_FINDINGS.md](./CODE_REVIEW_FINDINGS.md) | 代码审查发现的关键问题 | ⭐⭐ |

---

### 📂 目录结构

```
docs/
├── 📄 README.md                 # 本文档 - 导航入口
├── 📄 MASTER_PLAN_2026.md       # 主计划文档
├── 📄 CODE_REVIEW_FINDINGS.md   # 代码审查发现
│
├── 📁 active/                   # 当前活跃的执行文档
│   ├── 📁 phase-1/              # Phase 1: 稳定加固
│   │   └── PHASE_1_IMPLEMENTATION.md
│   ├── 📁 phase-2/              # Phase 2: 生产就绪
│   │   └── SECURITY_IMPROVEMENT_PLAN.md
│   └── 📁 multi-agent/          # 多Agent协作方案
│       ├── MULTI_AGENT_EXECUTION_PLAN.md  # 执行方案 (主文档)
│       ├── FROZEN_INVARIANTS.md # 全局冻结项
│       ├── ROADMAP_MULTI_AGENT.md
│       └── WORKFLOW_MULTI_AGENT.md
│
├── 📁 plan/                     # 迭代计划文档
│   ├── INDEX.md                 # 计划索引
│   ├── PLAN-v1.1-*.md           # v1.1 版本计划
│   ├── PLAN-v1.2-*.md           # v1.2 版本计划
│   ├── PLAN-v2.0-*.md           # v2.0 版本计划
│   ├── PLAN-DEBT-*.md           # 技术债务计划
│   └── REVIEW_AND_RECOMMENDATIONS.md
│
├── 📁 guides/                   # 指导手册
│   ├── DEBUG_GUIDE.md           # 调试指南
│   ├── DEPLOY_GUIDE.md          # 部署指南
│   ├── GIT_REMOTE_SETUP.md      # Git 双云端配置
│   └── RUNTIME_REQUIREMENTS.md  # 运行环境要求
│
├── 📁 archive/                  # 归档文档 (历史参考)
│   ├── README.md                # 归档说明
│   ├── 📁 v1.0-completed/       # 已完成的 v1.0 计划
│   └── 📁 legacy-workpacks/     # 旧工作包执行证据
│
├── 📁 report/                   # 报告文档
│   ├── CODE_AUDIT_REPORT_*.md   # 代码审计报告
│   ├── ARCHITECTURE_DIAGRAM.md  # 架构图
│   └── TECH_DEBT_TRACKER.md     # 技术债务追踪
│
├── 📁 specs/                    # 技术规范
│   └── SPEC-*.md                # 各类技术规范
│
├── 📁 api/                      # API 文档
│   └── ai.t8star.cn/            # AI Gateway API 参考
│
├── 📁 reference/                # 参考代码 (只读)
│   └── mother/                  # 母体项目参考
│
└── 📁 requirements/             # 需求文档
    └── PRD_*.md                 # 产品需求文档
```

---

## 🚀 快速开始

### 新开发者入门

1. **了解项目** → 阅读 [MASTER_PLAN_2026.md](./MASTER_PLAN_2026.md)
2. **环境配置** → 参考 [guides/RUNTIME_REQUIREMENTS.md](./guides/RUNTIME_REQUIREMENTS.md)
3. **本地调试** → 参考 [guides/DEBUG_GUIDE.md](./guides/DEBUG_GUIDE.md)
4. **部署上线** → 参考 [guides/DEPLOY_GUIDE.md](./guides/DEPLOY_GUIDE.md)

### 多Agent协作开发

1. **了解规范** → 阅读 [active/multi-agent/FROZEN_INVARIANTS.md](./active/multi-agent/FROZEN_INVARIANTS.md)
2. **执行方案** → 参考 [active/multi-agent/MULTI_AGENT_EXECUTION_PLAN.md](./active/multi-agent/MULTI_AGENT_EXECUTION_PLAN.md)
3. **阶段任务** → 查看 [active/phase-1/](./active/phase-1/) 或 [active/phase-2/](./active/phase-2/)

### 查看迭代计划

1. **计划索引** → [plan/INDEX.md](./plan/INDEX.md)
2. **计划评审** → [plan/REVIEW_AND_RECOMMENDATIONS.md](./plan/REVIEW_AND_RECOMMENDATIONS.md)

---

## 📋 当前阶段任务

### Phase 1: 稳定加固 (进行中)

| 任务 | 优先级 | 状态 | 文档 |
|------|--------|------|------|
| 工作流持久化 | P0 | 待实施 | [PLAN-v1.1-02](./plan/PLAN-v1.1-02_WORKFLOW_PERSISTENCE.md) |
| 测试体系建设 | P0 | 待实施 | [PLAN-DEBT-01](./plan/PLAN-DEBT-01_TESTING.md) |
| Sentry 监控 | P1 | 待实施 | [PLAN-v1.1-03](./plan/PLAN-v1.1-03_SENTRY_MONITORING.md) |
| 前端性能优化 | P1 | 待实施 | [PLAN-v1.1-01](./plan/PLAN-v1.1-01_PERFORMANCE.md) |

### Phase 2: 生产就绪 (待启动)

| 任务 | 优先级 | 状态 | 文档 |
|------|--------|------|------|
| 安全加固 | P1 | 待实施 | [SECURITY_IMPROVEMENT_PLAN](./active/phase-2/SECURITY_IMPROVEMENT_PLAN.md) |
| API 文档 | P1 | 待实施 | [PLAN-DEBT-02](./plan/PLAN-DEBT-02_API_DOCS.md) |

---

## 🔗 相关链接

| 资源 | 链接 |
|------|------|
| Gitee 仓库 (主) | https://gitee.com/chengdu-flower-food/grid-workflow |
| GitHub 仓库 | https://github.com/XucroYuri/GridWorkflow |
| 问题追踪 | [Gitee Issues](https://gitee.com/chengdu-flower-food/grid-workflow/issues) |

---

## 📝 文档维护规范

### 命名规范

| 类型 | 格式 | 示例 |
|------|------|------|
| 计划文档 | `PLAN-v{版本}-{编号}_{功能}.md` | `PLAN-v1.1-01_PERFORMANCE.md` |
| 技术债务 | `PLAN-DEBT-{编号}_{类型}.md` | `PLAN-DEBT-01_TESTING.md` |
| 指导手册 | `{功能}_GUIDE.md` | `DEBUG_GUIDE.md` |
| 报告文档 | `{类型}_REPORT_{日期}.md` | `CODE_AUDIT_REPORT_2026-01-07.md` |

### 目录归属

- **活跃文档** → `active/` (正在执行的方案)
- **计划文档** → `plan/` (待实施的迭代计划)
- **指导手册** → `guides/` (操作指南)
- **归档文档** → `archive/` (已完成或过时)
- **报告文档** → `report/` (审计和分析报告)

---

**文档维护者**: AI Architect  
**最后更新**: 2026-01-08

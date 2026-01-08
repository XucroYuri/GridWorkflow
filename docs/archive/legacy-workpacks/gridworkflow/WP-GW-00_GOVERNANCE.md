# WP-GW-00_GOVERNANCE（治理与多 Agent 协作门禁）

**负责人团队**：Joint

**目标**：建立多 Agent 可执行的文档与协作门禁：分工边界、上下文注入模板、冻结项、安全基线、验收与回滚机制。

---

## 输入

- [PDCA-00_PROJECT_GOVERNANCE.md](../../PDCA-00_PROJECT_GOVERNANCE.md)
- [AGENT-00_WORKSTREAMS.md](../../AGENT-00_WORKSTREAMS.md)
- [PRECHECK-SEC_ARCH_AGENT.md](../../PRECHECK-SEC_ARCH_AGENT.md)

---

## 输出（交付物）

- 工作包体系可用：`docs/WORKPACKS/INDEX.md` 可导航
- 各 WP 有“Agent 启动上下文（复制即用）”
- 冻结项与安全门禁在文档中一致且可执行

---

## 冻结约束（必须）

> **全局冻结项**：统一遵守 [FROZEN_INVARIANTS.md](../FROZEN_INVARIANTS.md)

- 统一响应结构 `{ ok, data, error }`
- Prompt 单一来源（后端）
- 前端 API Client 单一入口（`apiClient.ts`）
- UI 文案仅简体中文
- Prompt 输出语种由显式规则控制（`output_language` / `{{Output_Language_Rule}}`）

**本工作包特定约束**：无额外约束

---

## Agent 启动上下文（复制即用）

```text
你是 Joint Agent（治理与门禁负责人）。
你只允许修改 docs/**。
目标：让文档体系形成可分配的工作包（Work Packages），每个工作包具备独立上下文注入信息并可验收。

输入：
- docs/PDCA-00_PROJECT_GOVERNANCE.md
- docs/AGENT-00_WORKSTREAMS.md
- docs/PRECHECK-SEC_ARCH_AGENT.md

输出：
1) docs/WORKPACKS/INDEX.md（索引）
2) 至少 3 个可执行 WP 样板（含负责人、输入输出、验收、回滚、启动上下文）

验收：
- 不出现跨团队职责混淆
- 冻结项在所有 WP/PLAN 中一致
- 每个 WP 至少提供 1 成功 + 1 失败路径的检查方式
```

---

## 验收 Checklist

- 能从 `docs/WORKPACKS/INDEX.md` 导航到 GridWorkflow 的 WP 清单与路线图
- 任何 Agent 仅凭单个 WP 文档就能启动并产出交付物
- 关键冻结项与安全门禁在文档中无冲突

---

## 回滚策略

- 若工作包结构导致引用混乱：保留原文档不动，只回滚 `docs/WORKPACKS/**` 的组织方式


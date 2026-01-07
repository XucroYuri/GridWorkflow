# WP-GW-06_GRIDWORKFLOW_FLOW（四步闭环：GridWorkflow）

**负责人团队**：Joint（契约由 Claude 先冻结，后端由 Codex 实现，UI 由 Gemini 落地）

**目标**：实现四步闭环：概念图 → 九宫格 Prompt → 九宫格图 → 视频 Prompt，并支持 Reroll（仅重绘图像）。

---

## 输入

- [PLAN-05_GRIDWORKFLOW_FLOW.md](../../PLAN-05_GRIDWORKFLOW_FLOW.md)
- [PRD_AI_Storyboard_Grid.md](../../requirements/PRD_AI_Storyboard_Grid.md)
- [WP-GW-06A_FLOW_CONTRACT.md](WP-GW-06A_FLOW_CONTRACT.md)
- 后端代理/视频/存储工作包：WP-GW-02/03/04

---

## 输出（交付物）

- 前端：四阶段页面与状态机（InputForm/ConceptStage/StoryboardStage/ExportStage）
- 后端：工作流相关接口与契约（以 `ARCH_REFACTOR_PLAN` 为准）
- 验收证据：四步走通 + 失败路径提示 + Reroll 仅重绘

---

## 冻结约束（必须）

- UI 文案仅简体中文
- Prompt 模板与拼接逻辑仅在后端（前端只展示与编辑可见 Prompt）
- Prompt 输出语种受 `output_language` 与 `{{Output_Language_Rule}}` 控制
- Reroll 不触发 LLM，仅重绘图像

---

## Agent 启动上下文（复制即用）

### Claude（契约复核）

```text
你是 Claude Agent（契约复核）。
只允许修改 docs/WORKPACKS/** 与契约相关的描述。
目标：确保 WP-GW-06A 已冻结的字段/错误码/状态枚举被严格沿用，避免实现偏移。
验收：契约字段与 WP-GW-06A 一致；九宫格产物形态一致；错误结构一致。
```

### Codex（后端实现）

```text
你是 Codex Agent（后端负责人）。
只允许修改 backend/** 与 docs/**。
目标：按已冻结契约实现最小链路（可先 mock），保证统一响应结构与错误码。
验收：每一步接口都有成功/失败样例；output_language 可透传并影响输出。
```

### Gemini（状态机与 UI）

```text
你是 Gemini Agent（前端负责人）。
只允许修改 frontend/** 与 docs/**。
目标：实现四步状态机 UI，所有文案简体中文，视觉风格为 Light Theme（Google 风格）。
验收：四步可走通；错误提示清晰；Reroll 不触发 LLM。
```

---

## 验收 Checklist

- 四步流程可走通（至少 1 条完整 happy path）
- 每步都有失败路径提示（字段缺失、上游错误、超时）
- Reroll 仅重绘图像，不重新生成文本
- Prompt 可复制，长文本展示可读

---

## 回滚策略

- 若联调阻塞：前端先使用 mock 数据跑通状态机，后端按契约逐步替换为真实实现

# PLAN-05_GRIDWORKFLOW_FLOW (九宫格自动化流程)

**目标**: 实现四步闭环：概念图 → 九宫格 Prompt → 九宫格图 → 视频 Prompt。

## 范围
**包含**:
- InputForm / ConceptStage / StoryboardStage / ExportStage
- 四步状态机
- 仅重绘图像 (Reroll)

**不包含**:
- 旧脚本分析流水线
- 多场景拆分

## 关键实现点
- 每一步产物必须写入状态
- 文本输出与图像输出分离
- Prompt 必须可编辑

## Agent 风险点
- 不要强行自动化跳步
- 不要将 Prompt 自动结构化成 JSON

## 验收
- 四步流程可走通
- Reroll 不触发 LLM

## PDCA 钩子
- **Plan**: 冻结四步状态机的输入输出与“可编辑 Prompt”原则，明确 Reroll 仅重绘图像。
- **Do**: 按阶段产物入状态的方式实现，确保每一步都可回退到上一步继续迭代。
- **Check**: 逐步验收（Step1→Step4），验证跳步不会被强制自动化；验证 Reroll 不触发 LLM。
- **Act**: 若发现体验上确实需要“复用结果/跳过步骤”，先在文档中明确允许的短路路径与约束，再落实现实交互。

## Agent 上下文注入包
- **负责人团队**: Joint（Codex 先冻结契约，Gemini 落地 UI）
- **本阶段目标**: 实现四步闭环与状态机，并保证可编辑 Prompt 与 Reroll 约束。
- **输入**: 本文档、`PRD_AI_Storyboard_Grid.md`、`ARCH_REFACTOR_PLAN.md`、WP-GW-02/03/04 的接口形态。
- **输出**: 四阶段 UI 与最小后端编排接口（或 mock），验收样例与失败路径说明。
- **冻结约束**:
  - Prompt 模板与拼接逻辑仅在后端
  - UI 文案仅简体中文
  - `output_language` 可控并能影响输出语种
  - Reroll 不触发 LLM，仅重绘图像
- **禁止事项（高风险）**:
  - 自动跳步或强制流程不可回退
  - 将 Prompt 自动改为 JSON/结构化输出
- **验收 Checklist**:
  - Step1→Step4 可走通（至少 1 条完整路径）
  - 每一步有明确失败提示（字段缺失/上游失败/超时）
  - Reroll 不触发 LLM
- **回滚策略**:
  - 若联调阻塞，前端先用 mock 走通状态机，后端按契约逐步替换为真实实现。

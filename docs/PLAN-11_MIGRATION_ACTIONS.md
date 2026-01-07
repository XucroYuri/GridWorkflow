# PLAN-11_MIGRATION_ACTIONS (迁移与资料归档行动方案)

**目标**: 在当前项目内完成知识与资产提取后，先将 `GRIDWORKFLOW_ROOT` 作为新项目的暂存工作区，随后依据 `PLAN-12_DETACH_TO_NEW_REPO` 的路线图，将其整体剥离为独立仓库根目录（例如 `F:\Code\GridWorkflow`），避免环境干扰与路径残留。

## 1. 当前项目内的学习与提取 (阶段 A)
**范围**:
- 仅做代码阅读、功能理解、关键逻辑摘录与清单化。
- 不在旧仓库新增业务代码，不做大规模重构。

**产出**:
- 迁移白名单与禁迁清单
- 可复用逻辑摘要
- API 网关、Prompt、UI 基座的摘录笔记

**落点**:
- 全部整理到 `docs/` 与 `docs/api/`
  - 包含 PDCA 治理与协作协议：`docs/PDCA-00_PROJECT_GOVERNANCE.md`

## 2. 迁移切换点 (阶段 B)
**切换条件**:
1. 新仓库骨架完成 (`PLAN-00_BOOTSTRAP`)
2. 安全/架构/Agent 门禁通过 (`PRECHECK-SEC_ARCH_AGENT`)
3. 文档归档完成 (见第 3 与第 4 节)

**切换动作**:
- 阶段 B：之后所有开发仅在 `GRIDWORKFLOW_ROOT` 暂存目录中进行，旧仓库其他部分只读
- 阶段 C 以后：按 `PLAN-12_DETACH_TO_NEW_REPO` 的步骤，将暂存目录整体迁移为新的仓库根目录，并在迁移完成后彻底停止在母体仓库内对该目录的修改

## 3. 需求与方案文档归档 (阶段 C)
**目标文档**:
- `docs/new/产品需求文档：AI自动化九宫格分镜与视频流工作台.md`
- `docs/new/重构落地方案：AI自动化九宫格分镜与视频流工作台.md`

**归档策略**:
- 在新项目中建立 `docs/requirements/`
- 将上述两份文档复制并归档为:
  - `PRD_AI_Storyboard_Grid.md`
  - `ARCH_REFACTOR_PLAN.md`
- 保留原路径不动，避免破坏旧项目引用

**Agent 阅读权限**:
- 允许读取 `docs/requirements/` 下文档
- 禁止读取旧项目根目录下的非必要历史文件

## 4. API 参考文档归档 (阶段 D)
**目标目录**:
-- 现有: `API参考`（如存在）
**调整策略**:
- 统一改名并迁移至 `docs/api/`
- 推荐结构:
```
docs/api/
├── ai.t8star.cn/
│   ├── index.md
│   ├── llms.txt
│   ├── sora2/
│   │   ├── text-to-video.md
│   │   ├── image-to-video.md
│   │   ├── storyboard-video.md
│   │   ├── query-task.md
│   │   ├── character.md
│   │   └── cameo.md
```

**Agent 阅读权限**:
- 允许读取 `docs/api/**`（仅 API 参考）
- 禁止读取开发过程中的临时草稿

## 5. 验收 (完成标志)
1. 迁移白名单与禁迁清单明确
2. 归档目录完成并可被 Agent 访问
3. 旧仓库进入只读模式

## PDCA 钩子
- **Plan**: 明确阶段 A-D 的产出清单与落点路径，冻结“切换后只在新目录开发”的规则。
- **Do**: 按阶段逐条完成归档与切换动作，确保旧仓库不再引入新业务改动。
- **Check**: 核验关键文档与 API 参考路径一致、可访问；核验 Agent 阅读范围与门禁一致。
- **Act**: 若出现文档分散或重复，优先通过移动/合并到规范目录解决，并同步更新索引与引用路径。

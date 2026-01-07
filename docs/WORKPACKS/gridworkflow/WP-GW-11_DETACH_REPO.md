# WP-GW-11_DETACH_REPO（剥离：迁移到独立目录与仓库）

**负责人团队**：Joint

**目标**：在初步重构完成后，将 `GRIDWORKFLOW_ROOT` 从母体仓库剥离到独立目录（例如 `F:\Code\GridWorkflow`），并消除路径残留干扰。

---

## 输入

- [PLAN-12_DETACH_TO_NEW_REPO.md](../../PLAN-12_DETACH_TO_NEW_REPO.md)
- [PLAN-11_MIGRATION_ACTIONS.md](../../PLAN-11_MIGRATION_ACTIONS.md)

---

## 输出（交付物）

- 新目录 `F:\Code\GridWorkflow`（或等价路径）成为唯一开发工作区
- 文档与配置不依赖母体仓库路径
- 母体仓库进入只读（除非做审计/参考）

---

## 冻结约束（必须）

- 剥离后任何开发只在新目录进行
- 文档内优先相对路径与 `GRIDWORKFLOW_ROOT` 概念，不写死母体绝对路径

---

## Agent 启动上下文（复制即用）

```text
你是 Joint Agent（剥离负责人）。
目标：把 GridWorkflow 从母体仓库剥离为独立目录与仓库根，并确保无路径残留干扰。
验收：文档自洽；启动与运行不依赖母体路径；母体仓库只读。
```

---

## 验收 Checklist

- 文档引用均可在新目录下成立
- 不存在依赖母体仓库的路径说明或脚本依赖
- 新目录可作为独立仓库继续迭代

---

## 回滚策略

- 若剥离后异常：保留母体内暂存目录只读备份，回退排查后再剥离


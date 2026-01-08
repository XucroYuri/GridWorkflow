# WP-GW-03_VIDEO_SORA2（视频服务：Sora2 生成与查询）

**负责人团队**：Codex

**目标**：实现视频生成与状态查询，确保任务可追踪、错误脱敏、避免成本风险与枚举风险。

---

## 输入

- [PLAN-02_VIDEO_SORA2.md](../../PLAN-02_VIDEO_SORA2.md)
- [PRECHECK-SEC_ARCH_AGENT.md](../../PRECHECK-SEC_ARCH_AGENT.md)
- Sora2 API 参考：`../../api/ai.t8star.cn/sora2/*`

---

## 输出（交付物）

- `/api/v1/video/generate`：触发任务并返回 `task_id`
- `/api/v1/video/status/{task_id}`：查询任务状态（可占位但要有标准错误结构）
- `task_id` 校验与状态枚举说明

---

## 冻结约束（必须）

> **全局冻结项**：统一遵守 [FROZEN_INVARIANTS.md](../FROZEN_INVARIANTS.md)

**本工作包特定约束**：
- 异步化：生成接口必须快速返回 `task_id`
- 日志与错误脱敏：不记录完整 `task_id`、不透传上游原始错误体
- provider 只能走注册表，不允许前端自定义 URL
- 任务状态枚举遵循全局冻结（`queued` / `running` / `succeeded` / `failed`）

---

## Agent 启动上下文（复制即用）

```text
你是 Codex Agent（后端负责人）。
只允许修改 backend/** 与 docs/**。
目标：实现 Sora2 generate/status，任务可追踪且不泄露敏感信息。
验收：成功任务返回 task_id 可查询；失败任务错误结构标准化且脱敏；轮询间隔策略明确。
```

---

## 验收 Checklist

- 触发生成返回 `task_id`
- `task_id` 格式/长度校验存在
- 状态查询返回可用于前端渲染的最小字段（成功/失败/进行中）
- 失败原因不包含上游完整错误体与敏感字段

---

## 回滚策略

- 发生不稳定时可禁用视频生成（保留状态查询与历史任务展示占位）


# WP-GW-08_DEPLOY_VERCEL（部署：Vercel 适配）

**负责人团队**：Codex（后端）+ Gemini（前端）串行收敛

**目标**：在 Vercel Serverless 约束下部署可运行版本，验证异步任务与外部状态策略成立。

---

## 输入

- [PLAN-08_VERCEL_DEPLOY.md](../../PLAN-08_VERCEL_DEPLOY.md)
- WP-GW-03_VIDEO_SORA2、WP-GW-04_STORAGE_COS、WP-GW-05_FRONTEND_SHELL

---

## 输出（交付物）

- Vercel 可构建、可访问的前端与后端 API
- 生成任务不被函数超时截断（返回 task_id 并可轮询）

---

## 冻结约束（必须）

> **全局冻结项**：统一遵守 [FROZEN_INVARIANTS.md](../FROZEN_INVARIANTS.md)

**本工作包特定约束**：
- 长任务必须异步化（返回 `task_id` 并轮询状态）
- 媒体必须外置存储（COS）
- 所有密钥仅通过环境变量注入
- Serverless 函数超时设置需匹配异步策略

---

## Agent 启动上下文（复制即用）

```text
你是 Codex/Gemini 联合 Agent（部署收敛负责人）。
目标：让项目在 Vercel 上构建通过并可运行最小闭环。
验收：构建通过；前端可调用 API；视频生成返回 task_id 并可查询状态；不因超时失败。
```

---

## 验收 Checklist

- Vercel 构建通过
- 前端可访问并调用后端 API
- 生成任务返回 task_id，轮询可继续

---

## 验收证据

- `docs/WORKPACKS/gridworkflow/EVIDENCE_WP-GW-08_DEPLOY_VERCEL.md`

---

## 回滚策略

- 若 Serverless 约束不满足：后端迁移到更适合长任务的平台，前端保持不变

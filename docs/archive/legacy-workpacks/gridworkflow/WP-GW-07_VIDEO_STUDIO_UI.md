# WP-GW-07_VIDEO_STUDIO_UI（视频工作台：/video）

**负责人团队**：Gemini（前端主导，后端配合接口契约）

**目标**：打造仿 Sora 的视频工作台 UI：输入 Prompt + 参数，右侧任务列表与进度、预览播放；支持手动与自动入口。

---

## 输入

- [PLAN-06_VIDEO_STUDIO_UI.md](../../PLAN-06_VIDEO_STUDIO_UI.md)
- 后端依赖：WP-GW-03_VIDEO_SORA2、WP-GW-04_STORAGE_COS

---

## 输出（交付物）

- `/video` 路由页面与核心组件（编辑区、参数区、任务列表、预览）
- 任务状态渲染与轮询策略（>= 3s）
- Light Theme（Google 风格）一致性落地

---

## 冻结约束（必须）

> **全局冻结项**：统一遵守 [FROZEN_INVARIANTS.md](../FROZEN_INVARIANTS.md)

**本工作包特定约束**：
- UI 文案仅简体中文
- 不直连外部视频 API，所有调用走后端（通过 `apiClient.ts`）
- 任务列表不能以 localStorage 作为唯一来源
- 任务状态渲染遵循全局冻结枚举（`queued` / `running` / `succeeded` / `failed`）

---

## Agent 启动上下文（复制即用）

```text
你是 Gemini Agent（前端负责人）。
只允许修改 frontend/** 与 docs/**。
目标：实现 /video 页面：输入→生成→任务列表追踪→预览播放。
验收：任务状态可视化清晰；轮询间隔>=3s；刷新后至少可通过服务端任务追踪继续查看状态。
```

---

## 验收 Checklist

- 触发生成后显示 task_id
- 任务列表显示状态变化（进行中/成功/失败）
- 成功后可播放视频（URL 来自 COS 或可访问地址）
- Light Theme 下视觉一致

---

## 回滚策略

- 若后端状态查询未完成：前端先用占位状态展示与 mock 数据，保持 UI 结构不变


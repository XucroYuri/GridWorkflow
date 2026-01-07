# WP-GW-05_FRONTEND_SHELL（前端基座：Light Theme + API Client）

**负责人团队**：Gemini

**目标**：迁移/复刻当前项目的 Light Theme（偏 Google 风格），并建立统一的前端基座（Layout/Toast/Lightbox/路由/apiClient）。

---

## 输入

- [PLAN-04_FRONTEND_SHELL.md](../../PLAN-04_FRONTEND_SHELL.md)
- [PRD_AI_Storyboard_Grid.md](../../requirements/PRD_AI_Storyboard_Grid.md)

---

## 输出（交付物）

- `frontend/src/services/apiClient.ts`（唯一 API 入口）
- 基础 Layout、Toast、Lightbox、路由与主题
- Light Theme 视觉一致性基线（可复用组件样式）

---

## 冻结约束（必须）

- UI 文案仅简体中文
- 所有 API 只走 `apiClient.ts`，禁止散落 `fetch`
- 不直连外部 AI API

---

## Agent 启动上下文（复制即用）

```text
你是 Gemini Agent（前端负责人）。
只允许修改 frontend/** 与 docs/**。
目标：完成 Light Theme（Google 风格）基座迁移，并实现统一 apiClient。
验收：基础页面可渲染；Toast/Lightbox 可用；所有请求入口统一；视觉风格一致且专业现代。
```

---

## 验收 Checklist

- 首页/基础路由可访问
- Toast/Lightbox 可用
- 所有 API 请求均通过 apiClient.ts
- Light Theme 下组件间距/字体/层级一致

---

## 回滚策略

- 若迁移引入不稳定：回退到“仅 Layout + apiClient”的最小骨架，再逐步补齐组件


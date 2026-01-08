# WP-GW-01_BOOTSTRAP（项目骨架：前后端最小可运行）

**负责人团队**：Joint（Codex + Gemini 串行落地）

**目标**：建立前后端最小可运行骨架与环境变量基线，为后续并行开发提供可启动环境。

---

## 输入

- [PLAN-00_BOOTSTRAP.md](../../PLAN-00_BOOTSTRAP.md)
- [PRECHECK-SEC_ARCH_AGENT.md](../../PRECHECK-SEC_ARCH_AGENT.md)

---

## 输出（交付物）

- `backend/`：FastAPI 骨架 + `/health`
- `frontend/`：Vite/React/Tailwind 骨架 + 首页
- `.env.example`：仅包含必需键
- README：启动方式、端口、API Base 说明

---

## 冻结约束（必须）

> **全局冻结项**：统一遵守 [FROZEN_INVARIANTS.md](../FROZEN_INVARIANTS.md)

**本工作包特定约束**：
- UI 文案仅简体中文
- 前端 API 请求统一走 `apiClient.ts`（后续 WP 创建）
- 后端所有响应统一 `{ ok, data, error }`

---

## 并行/串行安排

- **串行 1**（Codex）：先把后端 `/health` 跑通并确定端口
- **串行 2**（Gemini）：再把前端 dev server 与 API Base 配置跑通

---

## Agent 启动上下文（复制即用）

### Codex（后端）

```text
你是 Codex Agent（后端负责人）。
只允许修改 backend/** 与 docs/**。
目标：完成 FastAPI 骨架与 /health，并提供统一响应结构示例。
验收：GET /health 返回 200；响应结构清晰。
```

### Gemini（前端）

```text
你是 Gemini Agent（前端负责人）。
只允许修改 frontend/** 与 docs/**。
目标：完成 Vite/React/Tailwind 骨架并能访问首页；文案仅简体中文。
验收：前端可访问首页；后续能通过配置访问后端 API Base。
```

---

## 验收 Checklist

- 后端 `/health` 返回 200
- 前端首页可访问，且不依赖母体仓库路径
- `.env.example` 不含任何真实密钥

---

## 交付记录（Codex 后端）

- FastAPI 骨架与路由聚合：`backend/app/main.py`、`backend/app/api/`
- 健康检查：`GET /health` 返回 200，示例 `{ "ok": true, "data": { "status": "ok", "env": "<env>", "timestamp": "..." }, "error": null }`
- 响应统一封装：`backend/app/schemas/response.py`
- 日志与 request_id：中间件记录耗时并输出脱敏异常，header 带 `X-Request-ID`
- 配置与启动说明：`backend/.env.example`、`docs/README.md`（API Base `http://localhost:8000`）

---

## 回滚策略

- 若骨架依赖过多或不稳定：回滚到仅保留最小 FastAPI + 最小 Vite/React 的版本


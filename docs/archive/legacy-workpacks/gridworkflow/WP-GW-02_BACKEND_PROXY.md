# WP-GW-02_BACKEND_PROXY（后端代理：文本/图像）

**负责人团队**：Codex

**目标**：实现 AI 网关的文本与图像代理，保持兼容性并满足安全门禁（脱敏、限流、输入门禁）。

---

## 输入

- [PLAN-01_BACKEND_PROXY.md](../../PLAN-01_BACKEND_PROXY.md)
- [ARCH_REFACTOR_PLAN.md](../../requirements/ARCH_REFACTOR_PLAN.md)
- [PRECHECK-SEC_ARCH_AGENT.md](../../PRECHECK-SEC_ARCH_AGENT.md)

---

## 输出（交付物）

- `/api/v1/ai/analyze`：文本代理
- `/api/v1/ai/generate-image`：图像代理（兼容 `/images/edits` 的 `image` 字段兜底）
- 错误码映射与脱敏策略说明（文档/实现一致）

---

## 冻结约束（必须）

> **全局冻结项**：统一遵守 [FROZEN_INVARIANTS.md](../FROZEN_INVARIANTS.md)

**本工作包特定约束**：
- 统一响应结构 `{ ok, data, error }`
- Prompt 模板仅在后端拼接，不在服务层拼接业务 Prompt
- 不透传上游完整错误体，不记录密钥与完整 Prompt

---

## Agent 启动上下文（复制即用）

```text
你是 Codex Agent（后端负责人）。
只允许修改 backend/** 与 docs/** 中与本工作包相关的文档。
目标：实现 AI 文本/图像代理，兼容网关行为并满足安全门禁。

输入：
- docs/PLAN-01_BACKEND_PROXY.md
- docs/PRECHECK-SEC_ARCH_AGENT.md

输出：
- API 路由 + 服务封装
- 至少 1 成功 + 1 失败用例说明（可复现）

禁止：
- 记录密钥、完整 Prompt、签名 URL 参数
- 修改 multipart 结构导致不兼容
```

---

## 验收 Checklist

- 文本/图像各 1 条成功 + 1 条失败请求可复现
- 错误返回为 `{ ok:false, error:{code,message} }` 且不包含敏感信息

---

## 错误码映射与脱敏策略

- 统一输出 `{ ok:false, error:{code,message} }`，不透传上游完整错误体，不记录密钥/完整 Prompt
- 映射规则（实现与文档一致）：
  - `400` -> `BAD_REQUEST`
  - `401` -> `UNAUTHORIZED`
  - `403` -> `FORBIDDEN`
  - `404` -> `NOT_FOUND`
  - `408/504` -> `TIMEOUT`
  - `429` -> `RATE_LIMITED`
  - `5xx/网络异常` -> `UPSTREAM_ERROR`
- 输入门禁：
  - `prompt` 不能为空（空白字符视为无效）
  - `image` base64 最大 2MB（`MAX_IMAGE_BASE64_BYTES`）
  - `response_format`（图像）仅允许 `url` / `b64_json`

---

## 验收证据（可复现）

> 说明：需配置 `AI_GATEWAY_API_KEY` 或请求头 `x-user-gemini-key`。

### 文本成功

```bash
curl -X POST http://localhost:8000/api/v1/ai/analyze \
  -H "Content-Type: application/json" \
  -d "{\"prompt\":\"用一句话概括 AI 网关的作用\"}"
```

期望响应（示例）：

```json
{ "ok": true, "data": "AI 网关用于统一代理模型调用与安全控制。", "error": null }
```

### 文本失败（空白 Prompt）

```bash
curl -X POST http://localhost:8000/api/v1/ai/analyze \
  -H "Content-Type: application/json" \
  -d "{\"prompt\":\" \"}"
```

期望响应（示例）：

```json
{ "ok": false, "data": null, "error": { "code": "BAD_REQUEST", "message": "prompt 不能为空" } }
```

### 图像成功（无参考图，自动兜底 1x1 PNG）

```bash
curl -X POST http://localhost:8000/api/v1/ai/generate-image \
  -H "Content-Type: application/json" \
  -d "{\"prompt\":\"一只戴墨镜的柴犬，插画风\"}"
```

期望响应（示例）：

```json
{ "ok": true, "data": [{ "url": "https://..." }], "error": null }
```

### 图像失败（response_format 非法）

```bash
curl -X POST http://localhost:8000/api/v1/ai/generate-image \
  -H "Content-Type: application/json" \
  -d "{\"prompt\":\"测试\", \"response_format\":\"raw\"}"
```

期望响应（示例）：

```json
{ "ok": false, "data": null, "error": { "code": "BAD_REQUEST", "message": "response_format 不支持" } }
```

---

## 回滚策略

- 若上游兼容性问题严重：保留旧实现并以配置开关回退

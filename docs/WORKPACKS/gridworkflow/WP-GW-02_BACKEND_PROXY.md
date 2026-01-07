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

- 统一响应结构 `{ ok, data, error }`
- 不在后端服务层拼接业务 Prompt
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

## 回滚策略

- 若上游兼容性问题严重：保留旧实现并以配置开关回退


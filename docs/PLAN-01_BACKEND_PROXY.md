# PLAN-01_BACKEND_PROXY (AI Gateway 代理层)

**目标**: 将 `https://ai.t8star.cn/v1` 的文本/图像能力在 FastAPI 中封装成统一代理。

## 范围
**包含**:
- `/api/v1/ai/analyze` (文本/LLM)
- `/api/v1/ai/generate-image` (图像生成)
- 统一响应结构 `{ ok, data, error }`

**不包含**:
- 业务编排逻辑
- 视频生成

## 输入
- `x-user-gemini-key` (可选)
- `AI_GATEWAY_BASE_URL`, `AI_GATEWAY_API_KEY`

## 输出
- 文本响应/图像 URL

## 关键实现点
- `/images/edits` 必须传 `image` 字段 (1x1 PNG 兜底)
- 不要在服务层拼接业务 Prompt
- 保留原始错误信息用于排查

## Agent 风险点
- 不要把 `response_format` 固定成 JSON
- 不要移除 `image` 字段

## 验收
- 文本调用成功返回字符串
- 图像调用返回 URL 或 b64_json

## PDCA 钩子
- **Plan**: 冻结 `/api/v1/ai/analyze` 与 `/api/v1/ai/generate-image` 的输入输出与错误码映射。
- **Do**: 仅做网关代理与鉴权封装，保持 multipart 结构与 `image` 字段兜底策略不变。
- **Check**: 使用 1 个成功样例 + 1 个失败样例验证；确认错误信息对排障有用且不泄露敏感数据。
- **Act**: 若出现兼容性问题，先调整代理层与契约文档，避免在业务层或前端做“补丁式”绕过。

## Agent 上下文注入包
- **负责人团队**: Codex (后端)
- **本阶段目标**: 实现文本/图像统一代理层，兼容现有网关行为并确保安全。
- **输入**: 本文档、`AGENT-00_WORKSTREAMS.md`、`PRECHECK-SEC_ARCH_AGENT.md`、AI 网关 OpenAPI 参考。
- **输出**: FastAPI 路由与服务实现、错误映射、最小验收用例说明。
- **冻结约束**:
  - 统一响应结构 `{ ok, data, error }`
  - 不在服务层拼接业务 Prompt
  - 不返回原样上游错误体中的敏感内容
- **禁止事项（高风险）**:
  - 将密钥写入日志或错误信息
  - 修改 multipart 结构导致与网关不兼容
- **验收 Checklist**:
  - 文本/图像各 1 条成功请求 + 1 条失败请求可复现
  - 错误信息有助排查但无敏感数据
- **回滚策略**:
  - 出现兼容性问题时，保留原始代理实现并以配置开关控制新旧逻辑切换。

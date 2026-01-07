# FROZEN_INVARIANTS（全局冻结项：不可变约束）

**目标**：作为 GridWorkflow 所有工作包的统一约束基准，任何 Agent 在任何 WP 中都必须遵守这些不可变项。

---

## 1. 冻结项清单（必须遵守）

### 1.1 统一响应结构

**所有后端 API 必须返回**：

```json
{
  "ok": true,
  "data": {},
  "error": null
}
```

**失败时**：

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "BAD_REQUEST",
    "message": "..."
  }
}
```

- 禁止返回 raw data
- 禁止透传上游完整错误体
- 错误信息必须脱敏

---

### 1.2 Prompt 单一来源（后端）

- Prompt 模板与拼接逻辑仅存在于后端（`backend/app/core/prompts.py` 或等价位置）
- 前端只展示与编辑可见 Prompt，不做模板拼接
- 禁止在前端暴露完整系统提示词

---

### 1.3 前端 API Client 单一入口

- 所有 API 请求必须通过 `frontend/src/services/apiClient.ts`
- 禁止在组件中散落 `fetch` 或直接调用外部 URL
- 禁止前端直连 `ai.t8star.cn` 或任何外部 AI API

---

### 1.4 UI 文案仅简体中文

- 界面语言统一为简体中文（zh-CN）
- 按钮、标签、提示信息、错误信息均使用中文
- 代码/日志/接口内部可用英文

---

### 1.5 Prompt 输出语种可控

- LLM 输出语种由显式规则控制，不由模型自行选择
- 使用 `output_language` 参数（默认 `zh-CN`）
- 后端模板注入 `{{Output_Language_Rule}}` 规则

---

## 2. 安全门禁（必须遵守）

### 2.1 密钥与敏感信息

- 禁止将 `AI_GATEWAY_API_KEY`、`COS_SECRET_KEY`、`COS_SECRET_ID`、`SUPABASE_SERVICE_ROLE_KEY` 输出到日志
- 禁止在前端保存任何后端密钥或 COS 凭证
- 禁止在日志中记录完整 Prompt、签名 URL 参数
- 日志字段限制为 `request_id`、`model`、`step`、`latency_ms`

### 2.2 外部调用隔离

- 前端禁止直连外部 AI API
- 后端禁止在业务层散落拼接外部 URL
- 外部调用统一走后端代理层

### 2.3 上游错误脱敏

- 禁止将上游返回的完整错误体原样透传给前端
- 错误信息必须经过脱敏处理

---

## 3. 错误码规范（冻结）

| 错误码 | 含义 |
|--------|------|
| `BAD_REQUEST` | 入参缺失/格式不对/超限 |
| `UNAUTHORIZED` | 鉴权失败 |
| `FORBIDDEN` | 无权限访问资源 |
| `NOT_FOUND` | 资源/任务不存在 |
| `UPSTREAM_ERROR` | 上游服务错误（脱敏） |
| `TIMEOUT` | 上游超时或内部超时 |
| `RATE_LIMITED` | 超出限流 |

---

## 4. 任务状态枚举（冻结）

| 状态 | 含义 |
|------|------|
| `queued` | 排队中 |
| `running` | 执行中 |
| `succeeded` | 成功 |
| `failed` | 失败 |

---

## 5. 引用方式

各 WP 在"冻结约束"小节中应声明：

```markdown
- 统一遵守 [FROZEN_INVARIANTS.md](../FROZEN_INVARIANTS.md) 的全局冻结项
- 本工作包特定约束：...
```

---

## 6. 违反后果

- 违反冻结项的变更视为**直接退回**
- Agent 在交付前必须逐项核对冻结项
- 若需修改冻结项，必须先更新本文档并经过治理审批

---

## 变更记录

| 日期 | 版本 | 变更说明 |
|------|------|----------|
| 2026-01-07 | v1.0 | 初始版本，从 WP-GW-00 与 PDCA-00 汇总冻结项 |



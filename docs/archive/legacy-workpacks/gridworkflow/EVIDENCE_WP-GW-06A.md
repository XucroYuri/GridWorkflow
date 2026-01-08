# WP-GW-06A 验收证据记录

**工作包**：WP-GW-06A_FLOW_CONTRACT（四步工作流接口契约冻结版）

**负责人**：Claude

**冻结日期**：2026-01-07

**冻结版本**：v1.0

---

## 验收清单完成状态

### ✅ 1. 契约字段、默认值、枚举全部明确且不自相矛盾

**证据**：

| 接口 | 必填字段 | 可选字段（含默认值） |
|------|----------|----------------------|
| Step1 `/concept` | `style`, `plot`, `aspect_ratio` | `anchors={}`, `image_size="1K"` |
| Step2 `/storyboard/plan` | `style`, `plot` | `anchors={}`, `concept_prompt=null`, `concept_image_url=null`, `output_language="zh-CN"` |
| Step3 `/storyboard/generate` | `storyboard_prompt`, `aspect_ratio` | `reference_image_base64=null`, `image_size="1K"` |
| Step4 `/video/prompt` | `storyboard_prompt`, `original_plot` | `duration=10`, `fps=60`, `output_language="zh-CN"` |
| 视频生成 `/video/generate` | `prompt`, `model`, `aspect_ratio`, `duration` | `images=null`, `hd=false`, `provider="t8star"` |
| 状态查询 `/video/status/{task_id}` | `task_id`（路径参数） | `provider="t8star"` |

**一致性检查**：所有默认值在契约文档中统一列表，无矛盾。

---

### ✅ 2. `output_language` 在 Step2 与 Step4 中存在并有默认值

**证据**：

```markdown
Step2 请求体:
| `output_language` | string | 否 | `"zh-CN"` | LLM 输出语种 |

Step4 请求体:
| `output_language` | string | 否 | `"zh-CN"` | LLM 输出语种 |
```

**验证**：两个接口均已定义 `output_language` 字段，类型为 `string`，可选，默认值为 `"zh-CN"`。

---

### ✅ 3. 九宫格产物形式明确（二选一并冻结）

**冻结决策**：**单张拼图形态** `grid_image_url: string`

**决策理由**：
1. Gemini 模型生成的是完整的 3x3 九宫格拼图，上游直接返回单张图片
2. 避免后端增加复杂的图片拆分逻辑
3. 若未来需要单格 Reroll，可通过前端裁剪或后端增加拆分能力扩展

**弃用方案**：`grid_image_urls: string[]`（9 个独立 URL）

**文档引用**：WP-GW-06A_FLOW_CONTRACT.md - Step3 响应体定义

---

### ✅ 4. 错误码与错误结构统一

**证据**：

**错误结构（与 FROZEN_INVARIANTS.md 一致）**：

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

**错误码清单（与 FROZEN_INVARIANTS.md 一致）**：

| 错误码 | HTTP 状态码 | 含义 |
|--------|-------------|------|
| `BAD_REQUEST` | 400 | 入参缺失/格式不对/超限 |
| `UNAUTHORIZED` | 401 | 鉴权失败 |
| `FORBIDDEN` | 403 | 无权限访问资源 |
| `NOT_FOUND` | 404 | 资源/任务不存在 |
| `UPSTREAM_ERROR` | 502 | 上游服务错误（脱敏） |
| `TIMEOUT` | 504 | 上游超时或内部超时 |
| `RATE_LIMITED` | 429 | 超出限流 |

---

### ✅ 5. 每个接口提供成功/失败示例

**证据**：WP-GW-06A_FLOW_CONTRACT.md 中 6 个接口均包含：

- 成功响应示例（含完整 JSON）
- 失败响应示例（多种错误码场景）

**接口示例完整性**：

| 接口 | 成功示例 | 失败示例（个数） |
|------|----------|------------------|
| Step1 `/concept` | ✅ | 3 个（BAD_REQUEST, UPSTREAM_ERROR, TIMEOUT） |
| Step2 `/storyboard/plan` | ✅ | 2 个（BAD_REQUEST, UPSTREAM_ERROR） |
| Step3 `/storyboard/generate` | ✅ | 3 个（BAD_REQUEST, UPSTREAM_ERROR, TIMEOUT） |
| Step4 `/video/prompt` | ✅ | 2 个（BAD_REQUEST, UPSTREAM_ERROR） |
| 视频生成 `/video/generate` | ✅ | 4 个（BAD_REQUEST ×2, UNAUTHORIZED, RATE_LIMITED） |
| 状态查询 `/video/status` | ✅（4 种状态） | 2 个（BAD_REQUEST, NOT_FOUND） |

---

### ✅ 6. 契约与 FROZEN_INVARIANTS.md 一致

**检查项**：

| 冻结项 | 一致性 |
|--------|--------|
| 统一响应结构 `{ ok, data, error }` | ✅ 一致 |
| 错误码规范（7 个错误码） | ✅ 一致 |
| 任务状态枚举（4 种状态） | ✅ 一致 |
| 错误信息脱敏 | ✅ 一致（所有示例均为脱敏后的中文提示） |

---

## 任务状态枚举一致性验证

**FROZEN_INVARIANTS.md 定义**：

| 状态 | 含义 |
|------|------|
| `queued` | 排队中 |
| `running` | 执行中 |
| `succeeded` | 成功 |
| `failed` | 失败 |

**WP-GW-06A 定义**：✅ 完全一致

---

## 与 ARCH_REFACTOR_PLAN.md 一致性验证

**检查项**：

| 规范 | ARCH_REFACTOR_PLAN | WP-GW-06A | 一致性 |
|------|-------------------|-----------|--------|
| `/concept` 字段 | ✅ | ✅ | 一致 |
| `/storyboard/plan` 字段 | ✅ | ✅ | 一致 |
| `/storyboard/generate` 字段 | ✅ | ✅ | 一致 |
| `/video/prompt` 字段 | ✅ | ✅ | 一致 |
| `/video/generate` 字段 | ✅ | ✅ | 一致 |
| `/video/status` 字段 | ✅ | ✅ | 一致 |
| 响应结构 | `{ ok, data, error }` | `{ ok, data, error }` | 一致 |

**同步更新**：已在 ARCH_REFACTOR_PLAN.md 中添加九宫格产物形态决策引用。

---

## 冻结声明

本文档记录了 WP-GW-06A 工作包的完整验收证据。

**冻结内容**：
1. Step1~Step4 接口契约（字段、类型、必填性、默认值）
2. 九宫格产物形态：单张拼图 `grid_image_url: string`
3. 错误码规范：7 个错误码
4. 任务状态枚举：4 种状态
5. 统一响应结构：`{ ok, data, error }`

**任何变更需遵循**：
1. 先更新 WP-GW-06A_FLOW_CONTRACT.md
2. 同步更新 ARCH_REFACTOR_PLAN.md（如涉及）
3. 更新本证据文档
4. 经过治理审批

---

## 签署

- **契约负责人**：Claude Agent
- **冻结日期**：2026-01-07
- **版本**：v1.0



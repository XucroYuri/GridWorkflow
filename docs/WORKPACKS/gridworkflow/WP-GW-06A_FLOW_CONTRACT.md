# WP-GW-06A_FLOW_CONTRACT（四步工作流接口契约冻结版）

**负责人团队**：Claude

**目标**：在并行开发前，先串行冻结四步工作流与视频生成相关的后端接口契约，减少前后端联调返工。

---

## 输入

- [ARCH_REFACTOR_PLAN.md](../../requirements/ARCH_REFACTOR_PLAN.md)
- [PRD_AI_Storyboard_Grid.md](../../requirements/PRD_AI_Storyboard_Grid.md)
- [PRECHECK-SEC_ARCH_AGENT.md](../../PRECHECK-SEC_ARCH_AGENT.md)
- API 参考：`../../api/ai.t8star.cn/*`

---

## 输出（交付物）

- 冻结的接口清单与字段规范（本文件即契约真相）
- 每个接口的请求/响应示例（成功 + 失败）
- 错误码与错误结构规范

---

## 统一响应结构（冻结）

所有接口统一返回：

```json
{
  "ok": true,
  "data": {},
  "error": null
}
```

失败时：

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

---

## 全局字段与约束（冻结）

- `output_language`：可选，默认 `zh-CN`，用于控制 LLM 输出语种（由后端模板注入规则实现）。
- `anchors`：视觉锚点集合（人设/场景/道具等），字段结构可内部演进，但必须允许“文本描述 + 可选图片 URL”。
- `aspect_ratio`：`16:9` / `9:16`
- `image_size`：如 `1K`（以实际上游支持为准）
- 所有长文本字段（Prompt/Plot）必须支持中文内容。

---

## API 契约（冻结）

### 1) Step 1：概念图

**POST** `/api/v1/concept`

请求体（最小）：

```json
{
  "style": "...",
  "plot": "...",
  "anchors": {},
  "aspect_ratio": "16:9",
  "image_size": "1K"
}
```

成功响应 `data`：

```json
{
  "concept_prompt": "...",
  "concept_image_url": "https://..."
}
```

失败错误码（示例）：`BAD_REQUEST`、`UPSTREAM_ERROR`、`TIMEOUT`

---

### 2) Step 2：九宫格分镜规划（生成九宫格 Prompt）

**POST** `/api/v1/storyboard/plan`

请求体（最小）：

```json
{
  "style": "...",
  "plot": "...",
  "anchors": {},
  "concept_prompt": "...",
  "concept_image_url": "https://...",
  "output_language": "zh-CN"
}
```

成功响应 `data`：

```json
{
  "storyboard_prompt": "..."
}
```

失败错误码（示例）：`BAD_REQUEST`、`UPSTREAM_ERROR`、`TIMEOUT`

---

### 3) Step 3：九宫格生图（生成九张图）

**POST** `/api/v1/storyboard/generate`

请求体（最小）：

```json
{
  "storyboard_prompt": "...",
  "reference_image_base64": null,
  "aspect_ratio": "16:9",
  "image_size": "1K"
}
```

成功响应 `data`：

```json
{
  "grid_image_urls": [
    "https://...",
    "https://..."
  ]
}
```

约束：
- `grid_image_urls` 必须为 9 个 URL（若上游返回单张拼图，也要在后端拆分或明确 `grid_image_url` 单字段；二选一必须在实现前确定并冻结）。

失败错误码（示例）：`BAD_REQUEST`、`UPSTREAM_ERROR`、`TIMEOUT`

---

### 4) Step 4：视频 Prompt 生成

**POST** `/api/v1/video/prompt`

请求体（最小）：

```json
{
  "storyboard_prompt": "...",
  "original_plot": "...",
  "duration": 10,
  "fps": 60,
  "output_language": "zh-CN"
}
```

成功响应 `data`：

```json
{
  "video_prompt": "..."
}
```

失败错误码（示例）：`BAD_REQUEST`、`UPSTREAM_ERROR`、`TIMEOUT`

---

### 5) 视频生成（Sora2）

**POST** `/api/v1/video/generate`

请求体（最小）：

```json
{
  "prompt": "...",
  "model": "sora-2",
  "images": null,
  "aspect_ratio": "16:9",
  "hd": false,
  "duration": 10,
  "provider": "t8star"
}
```

成功响应 `data`：

```json
{
  "task_id": "..."
}
```

失败错误码（示例）：`BAD_REQUEST`、`UPSTREAM_ERROR`、`RATE_LIMITED`

---

### 6) 视频任务状态查询

**GET** `/api/v1/video/status/{task_id}`

成功响应 `data`（最小）：

```json
{
  "task_id": "...",
  "provider": "t8star",
  "status": "queued",
  "video_url": null,
  "error_message": null
}
```

`status` 枚举（冻结）：`queued` / `running` / `succeeded` / `failed`

---

## 错误码规范（冻结）

- `BAD_REQUEST`：入参缺失/格式不对/超限
- `UNAUTHORIZED`：鉴权失败
- `FORBIDDEN`：无权限访问资源
- `NOT_FOUND`：任务不存在
- `UPSTREAM_ERROR`：上游服务错误（脱敏）
- `TIMEOUT`：上游超时或内部超时
- `RATE_LIMITED`：超出限流

---

## Agent 启动上下文（复制即用）

```text
你是 Claude Agent（后端契约负责人）。
目标：冻结四步工作流与视频相关接口契约，产出可直接给前端对接的请求/响应与错误码规范。
只允许修改 docs/WORKPACKS/** 与 docs/requirements/**（如需同步契约描述）。

验收：
1) 契约字段与 ARCH_REFACTOR_PLAN 保持一致（如调整，必须同步更新 ARCH）
2) 每个接口提供成功/失败示例
3) 错误结构统一 `{ ok,data,error }` 且脱敏
```

---

## 验收 Checklist

- 契约字段、默认值、枚举全部明确且不自相矛盾
- `output_language` 在 Step2 与 Step4 中存在并有默认值
- 九宫格产物形式明确（9 个 URL 或单张拼图二选一并冻结）
- 错误码与错误结构统一

---

## 回滚策略

- 若契约设计导致实现困难：回滚到 `ARCH_REFACTOR_PLAN` 的“最小字段规范”版本，仅冻结字段名与默认值，暂缓冻结复杂结构


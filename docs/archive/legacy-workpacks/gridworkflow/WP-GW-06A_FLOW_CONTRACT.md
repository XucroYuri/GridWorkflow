# WP-GW-06A_FLOW_CONTRACT（四步工作流接口契约冻结版）

**负责人团队**：Claude

**目标**：在并行开发前，先串行冻结四步工作流与视频生成相关的后端接口契约，减少前后端联调返工。

**冻结版本**：v1.0 (2026-01-07)

**冻结状态**：✅ 已冻结

---

## 输入

- [ARCH_REFACTOR_PLAN.md](../../requirements/ARCH_REFACTOR_PLAN.md)
- [PRD_AI_Storyboard_Grid.md](../../requirements/PRD_AI_Storyboard_Grid.md)
- [PRECHECK-SEC_ARCH_AGENT.md](../../PRECHECK-SEC_ARCH_AGENT.md)
- API 参考：`../../api/ai.t8star.cn/*`

---

## 输出（交付物）

- ✅ 冻结的接口清单与字段规范（本文件即契约真相）
- ✅ 每个接口的请求/响应示例（成功 + 失败）
- ✅ 错误码与错误结构规范

---

## 冻结约束（必须）

> **全局冻结项**：统一遵守 [FROZEN_INVARIANTS.md](../FROZEN_INVARIANTS.md)

**本工作包特定约束**：
- 本文件为契约冻结版本，任何字段变更需同步更新本文件
- 错误码遵循全局冻结规范
- 任务状态枚举遵循全局冻结规范

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

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `output_language` | string | 否 | `"zh-CN"` | 控制 LLM 输出语种（由后端模板注入规则实现） |
| `anchors` | object | 否 | `{}` | 视觉锚点集合（人设/场景/道具），结构见下文 |
| `aspect_ratio` | string | 是 | - | `"16:9"` 或 `"9:16"` |
| `image_size` | string | 否 | `"1K"` | 图片分辨率，可选 `"1K"` / `"2K"` / `"4K"` |

**`anchors` 结构定义（冻结）**：

```json
{
  "character": { "text": "人物描述", "image_base64": "data:image/png;base64,..." },
  "environment": { "text": "场景描述", "image_base64": null },
  "prop": { "text": "道具描述", "image_base64": null }
}
```

- 每个锚点包含 `text`（string，必填）和 `image_base64`（string | null，可选）
- 所有长文本字段（Prompt/Plot）必须支持中文内容

---

## API 契约（冻结）

### 1) Step 1：概念图生成

**POST** `/api/v1/concept`

**请求体**：

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `style` | string | 是 | - | 风格描述 |
| `plot` | string | 是 | - | 剧情片段 |
| `anchors` | object | 否 | `{}` | 视觉锚点 |
| `aspect_ratio` | string | 是 | - | `"16:9"` 或 `"9:16"` |
| `image_size` | string | 否 | `"1K"` | 图片分辨率 |

**成功响应示例**：

```json
{
  "ok": true,
  "data": {
    "concept_prompt": "Anime artwork, OLM studio style, cel-shaded...",
    "concept_image_url": "https://cos.example.com/concept/xxx.png"
  },
  "error": null
}
```

**失败响应示例**：

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "BAD_REQUEST",
    "message": "style 字段不能为空。"
  }
}
```

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "UPSTREAM_ERROR",
    "message": "上游服务异常，请稍后重试。"
  }
}
```

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "TIMEOUT",
    "message": "请求超时，请稍后重试。"
  }
}
```

---

### 2) Step 2：九宫格分镜规划（生成九宫格 Prompt）

**POST** `/api/v1/storyboard/plan`

**请求体**：

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `style` | string | 是 | - | 风格描述 |
| `plot` | string | 是 | - | 剧情片段 |
| `anchors` | object | 否 | `{}` | 视觉锚点 |
| `concept_prompt` | string | 否 | `null` | 概念图 Prompt（Step1 产物） |
| `concept_image_url` | string | 否 | `null` | 概念图 URL（Step1 产物） |
| `output_language` | string | 否 | `"zh-CN"` | LLM 输出语种 |

**成功响应示例**：

```json
{
  "ok": true,
  "data": {
    "storyboard_prompt": "生成一张3×3的分镜九宫格图片，主题为日系动漫风格的少女乐队演唱会场景，采用OLM工作室风格、宝可梦动画质感、赛璐璐上色..."
  },
  "error": null
}
```

**失败响应示例**：

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "BAD_REQUEST",
    "message": "plot 字段不能为空。"
  }
}
```

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "UPSTREAM_ERROR",
    "message": "上游服务异常，请稍后重试。"
  }
}
```

---

### 3) Step 3：九宫格生图（生成九宫格图片）

**POST** `/api/v1/storyboard/generate`

**请求体**：

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `storyboard_prompt` | string | 是 | - | 九宫格 Prompt（Step2 产物） |
| `reference_image_base64` | string | 否 | `null` | 参考图 base64（概念图） |
| `aspect_ratio` | string | 是 | - | `"16:9"` 或 `"9:16"` |
| `image_size` | string | 否 | `"1K"` | 图片分辨率 |

**九宫格产物形态（冻结决策）**：

> ✅ **冻结为单张拼图形态** `grid_image_url: string`
>
> **决策理由**：
> 1. Gemini 模型生成的是完整的 3x3 九宫格拼图，上游直接返回单张图片
> 2. 避免后端增加复杂的图片拆分逻辑
> 3. 若未来需要单格 Reroll，可通过前端裁剪或后端增加拆分能力扩展
>
> **弃用方案**：`grid_image_urls: string[]`（9 个独立 URL）

**成功响应示例**：

```json
{
  "ok": true,
  "data": {
    "grid_image_url": "https://cos.example.com/storyboard/xxx.png"
  },
  "error": null
}
```

**失败响应示例**：

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "BAD_REQUEST",
    "message": "storyboard_prompt 字段不能为空。"
  }
}
```

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "UPSTREAM_ERROR",
    "message": "上游服务异常，请稍后重试。"
  }
}
```

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "TIMEOUT",
    "message": "请求超时，请稍后重试。"
  }
}
```

---

### 4) Step 4：视频 Prompt 生成

**POST** `/api/v1/video/prompt`

**请求体**：

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `storyboard_prompt` | string | 是 | - | 九宫格 Prompt（Step2 产物） |
| `original_plot` | string | 是 | - | 原始剧情片段 |
| `duration` | int | 否 | `10` | 视频时长（秒），可选 10/15/25 |
| `fps` | int | 否 | `60` | 帧率 |
| `output_language` | string | 否 | `"zh-CN"` | LLM 输出语种 |

**成功响应示例**：

```json
{
  "ok": true,
  "data": {
    "video_prompt": "基于上述3×3分镜九宫格的镜头运镜逻辑，生成一段10秒的流畅动漫风格MV视频，采用宝可梦动画风格，OLM工作室风格，赛璐璐上色，60fps高帧率保证画面丝滑..."
  },
  "error": null
}
```

**失败响应示例**：

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "BAD_REQUEST",
    "message": "storyboard_prompt 字段不能为空。"
  }
}
```

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "UPSTREAM_ERROR",
    "message": "上游服务异常，请稍后重试。"
  }
}
```

---

### 5) 视频生成（Sora2）

**POST** `/api/v1/video/generate`

**请求体**：

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `prompt` | string | 是 | - | 视频 Prompt |
| `model` | string | 是 | - | 模型名称：`"sora-2"` 或 `"sora-2-pro"` |
| `images` | string[] | 否 | `null` | 参考图列表（URL 或 base64） |
| `aspect_ratio` | string | 是 | - | `"16:9"` 或 `"9:16"` |
| `hd` | bool | 否 | `false` | 是否高清（仅 `sora-2-pro` 支持） |
| `duration` | int | 是 | - | 视频时长：10/15/25（25 仅 `sora-2-pro`） |
| `provider` | string | 否 | `"t8star"` | 视频供应商 |

**成功响应示例**：

```json
{
  "ok": true,
  "data": {
    "task_id": "task_abc123xyz"
  },
  "error": null
}
```

**失败响应示例**：

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "BAD_REQUEST",
    "message": "model 参数不支持。"
  }
}
```

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "BAD_REQUEST",
    "message": "duration=25 仅支持 sora-2-pro。"
  }
}
```

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "缺少上游 API Key。"
  }
}
```

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "RATE_LIMITED",
    "message": "请求过于频繁，请稍后重试。"
  }
}
```

---

### 6) 视频任务状态查询

**GET** `/api/v1/video/status/{task_id}?provider=t8star`

**路径参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `task_id` | string | 是 | 任务 ID |

**查询参数**：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `provider` | string | 否 | `"t8star"` | 视频供应商 |

**成功响应示例**：

```json
{
  "ok": true,
  "data": {
    "task_id": "task_abc123xyz",
    "provider": "t8star",
    "status": "queued",
    "video_url": null,
    "error_message": null
  },
  "error": null
}
```

```json
{
  "ok": true,
  "data": {
    "task_id": "task_abc123xyz",
    "provider": "t8star",
    "status": "running",
    "video_url": null,
    "error_message": null
  },
  "error": null
}
```

```json
{
  "ok": true,
  "data": {
    "task_id": "task_abc123xyz",
    "provider": "t8star",
    "status": "succeeded",
    "video_url": "https://cos.example.com/video/xxx.mp4",
    "error_message": null
  },
  "error": null
}
```

```json
{
  "ok": true,
  "data": {
    "task_id": "task_abc123xyz",
    "provider": "t8star",
    "status": "failed",
    "video_url": null,
    "error_message": "内容不符合安全策略。"
  },
  "error": null
}
```

**失败响应示例**：

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "BAD_REQUEST",
    "message": "task_id 格式不正确。"
  }
}
```

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "NOT_FOUND",
    "message": "任务不存在。"
  }
}
```

**响应头（冻结）**：

| Header | 说明 |
|--------|------|
| `X-Poll-Interval-Ms` | 建议的轮询间隔（毫秒），最小 3000 |
| `Retry-After` | 建议的重试等待时间（秒） |

---

## 任务状态枚举（冻结）

| 状态 | 含义 | 说明 |
|------|------|------|
| `queued` | 排队中 | 任务已提交，等待执行 |
| `running` | 执行中 | 任务正在处理 |
| `succeeded` | 成功 | 任务完成，`video_url` 可用 |
| `failed` | 失败 | 任务失败，`error_message` 包含原因（已脱敏） |

---

## 错误码规范（冻结）

| 错误码 | HTTP 状态码 | 含义 | 用户提示示例 |
|--------|-------------|------|--------------|
| `BAD_REQUEST` | 400 | 入参缺失/格式不对/超限 | "xxx 字段不能为空。" |
| `UNAUTHORIZED` | 401 | 鉴权失败 | "缺少上游 API Key。" |
| `FORBIDDEN` | 403 | 无权限访问资源 | "无权限执行此操作。" |
| `NOT_FOUND` | 404 | 任务/资源不存在 | "任务不存在。" |
| `UPSTREAM_ERROR` | 502 | 上游服务错误（脱敏） | "上游服务异常，请稍后重试。" |
| `TIMEOUT` | 504 | 上游超时或内部超时 | "请求超时，请稍后重试。" |
| `RATE_LIMITED` | 429 | 超出限流 | "请求过于频繁，请稍后重试。" |

---

## 字段默认值汇总（冻结）

| 字段 | 默认值 | 适用接口 |
|------|--------|----------|
| `output_language` | `"zh-CN"` | Step2, Step4 |
| `image_size` | `"1K"` | Step1, Step3 |
| `anchors` | `{}` | Step1, Step2 |
| `concept_prompt` | `null` | Step2 |
| `concept_image_url` | `null` | Step2 |
| `reference_image_base64` | `null` | Step3 |
| `duration` | `10` | Step4 |
| `fps` | `60` | Step4 |
| `images` | `null` | 视频生成 |
| `hd` | `false` | 视频生成 |
| `provider` | `"t8star"` | 视频生成/状态查询 |

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

| 检查项 | 状态 | 证据 |
|--------|------|------|
| 契约字段、默认值、枚举全部明确且不自相矛盾 | ✅ 通过 | 见"字段默认值汇总"表 |
| `output_language` 在 Step2 与 Step4 中存在并有默认值 `"zh-CN"` | ✅ 通过 | Step2/Step4 请求体定义 |
| 九宫格产物形式明确（二选一并冻结） | ✅ 通过 | 冻结为 `grid_image_url: string`（单张拼图） |
| 错误码与错误结构统一 | ✅ 通过 | 见"错误码规范"表 |
| 每个接口提供成功/失败示例 | ✅ 通过 | 6 个接口均有完整示例 |
| 契约与 FROZEN_INVARIANTS.md 一致 | ✅ 通过 | 响应结构、错误码、状态枚举一致 |

---

## 回滚策略

- 若契约设计导致实现困难：回滚到 `ARCH_REFACTOR_PLAN` 的"最小字段规范"版本，仅冻结字段名与默认值，暂缓冻结复杂结构

---

## 变更记录

| 日期 | 版本 | 变更说明 |
|------|------|----------|
| 2026-01-07 | v1.0 | 初始冻结版本；Step1~Step4 字段/默认值/错误码全部冻结；九宫格产物冻结为单张拼图形态 |


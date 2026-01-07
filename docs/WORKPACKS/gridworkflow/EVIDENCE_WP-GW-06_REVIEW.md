# WP-GW-06 复核证据记录（Claude）

**工作包**：WP-GW-06_GRIDWORKFLOW_FLOW（四步闭环）

**复核人**：Claude Agent（契约复核）

**复核日期**：2026-01-07

**复核版本**：v1.0

---

## 复核范围

复核 Codex（后端）与 Gemini（前端）的 Joint 实现是否符合 WP-GW-06A 冻结契约。

---

## 发现的问题及修复

### 🚨 严重问题：路由冲突

**问题描述**：
- `video.py` (Gemini) 和 `workflow.py` (Codex) 都定义了 Step1-Step4 接口
- 两者都使用 `/api/v1` 前缀，导致路由冲突
- `video.py` 包含 MOCK 占位实现，`workflow.py` 包含真实 AI 服务调用

**修复方案**：
1. 移除 `video.py` 中重复的 Step1-Step4 MOCK 路由
2. 恢复 `video.py` 的原始前缀 `/api/v1/video`（仅处理视频生成/状态查询）
3. 移除 `video.py` schemas 中的重复 Schema 定义

**修复文件**：
- `backend/app/api/routes/video.py` - 移除 Step1-Step4 路由，恢复 `/api/v1/video` 前缀
- `backend/app/schemas/video.py` - 仅保留 `VideoGenerateRequest`

---

## 契约一致性验证

### 后端实现（Codex - workflow.py）

| 检查项 | 契约要求 | 实现情况 | 状态 |
|--------|----------|----------|------|
| Step1 路由 | `POST /api/v1/concept` | `@router.post("/concept")` with prefix `/api/v1` | ✅ |
| Step1 响应 | `concept_prompt`, `concept_image_url` | Line 105 返回一致 | ✅ |
| Step2 路由 | `POST /api/v1/storyboard/plan` | `@router.post("/storyboard/plan")` | ✅ |
| Step2 响应 | `storyboard_prompt` | Line 154 返回一致 | ✅ |
| Step2 `output_language` 默认值 | `"zh-CN"` | Line 122 默认 `"zh-CN"` | ✅ |
| Step3 路由 | `POST /api/v1/storyboard/generate` | `@router.post("/storyboard/generate")` | ✅ |
| Step3 响应 | `grid_image_url` (单张拼图) | Line 201 返回 `grid_image_url` | ✅ |
| Step4 路由 | `POST /api/v1/video/prompt` | `@router.post("/video/prompt")` | ✅ |
| Step4 响应 | `video_prompt` | Line 249 返回一致 | ✅ |
| Step4 `output_language` 默认值 | `"zh-CN"` | Line 224 默认 `"zh-CN"` | ✅ |
| Step4 `duration` 默认值 | `10` | Schema 默认 `10` | ✅ |
| Step4 `fps` 默认值 | `60` | Schema 默认 `60` | ✅ |

### 默认值验证

| 字段 | 契约默认值 | Schema 定义 | 状态 |
|------|------------|-------------|------|
| `output_language` | `"zh-CN"` | `StoryboardPlanRequest.output_language = "zh-CN"` | ✅ |
| `output_language` | `"zh-CN"` | `VideoPromptRequest.output_language = "zh-CN"` | ✅ |
| `image_size` | `"1K"` | `ConceptRequest.image_size = "1K"` | ✅ |
| `image_size` | `"1K"` | `StoryboardGenerateRequest.image_size = "1K"` | ✅ |
| `duration` | `10` | `VideoPromptRequest.duration = 10` | ✅ |
| `fps` | `60` | `VideoPromptRequest.fps = 60` | ✅ |

### 错误码验证

| 错误码 | 契约 HTTP | 实现 HTTP | 状态 |
|--------|-----------|-----------|------|
| `BAD_REQUEST` | 400 | 400 | ✅ |
| `UPSTREAM_ERROR` | 502 | 502 | ✅ |

### 响应结构验证

```python
# workflow.py 使用统一响应函数
from app.schemas.response import error_response, success_response
```

**验证**：所有接口使用 `success_response()` 和 `error_response()`，符合契约的 `{ ok, data, error }` 结构。

---

### 前端实现（Gemini - GridWorkflow.tsx）

| 检查项 | 契约要求 | 实现情况 | 状态 |
|--------|----------|----------|------|
| Step1 调用 | `/concept` | `videoService.generateConcept()` → `/concept` | ✅ |
| Step2 调用 | `/storyboard/plan` | `videoService.planStoryboard()` → `/storyboard/plan` | ✅ |
| Step3 调用 | `/storyboard/generate` | `videoService.generateStoryboard()` → `/storyboard/generate` | ✅ |
| Step4 调用 | `/video/prompt` | `videoService.generateVideoPrompt()` → `/video/prompt` | ✅ |
| Step5 调用 | `/video/generate` | `videoService.generateVideo()` → `/video/generate` | ✅ |
| 响应字段解析 | 与契约一致 | TypeScript 接口定义一致 | ✅ |

### Reroll 实现验证

**契约约束**："Reroll 不触发 LLM，仅重绘图像"

**实现验证**：

```typescript:140:156:frontend/src/components/video/GridWorkflow.tsx
// Reroll (Step 3) - Only regenerates image, keeps prompt
const handleRerollStoryboard = async () => {
  updateState({ isLoading: true, error: null });
  try {
    const res = await videoService.generateStoryboard(
      state.storyboardPrompt!, // Use existing confirmed prompt
      state.conceptImageUrl,
      state.aspectRatio
    );
    // ...
  }
};
```

**验证结论**：
- ✅ Reroll 仅调用 Step3 `generateStoryboard`（生图接口）
- ✅ 复用已确认的 `storyboardPrompt`，不触发 Step2 LLM
- ✅ 符合"仅重绘图像"约束

### 九宫格产物形态验证

**契约冻结**：`grid_image_url: string`（单张拼图）

**后端实现**：
```python
# workflow.py Line 201
return JSONResponse(
    status_code=200, content=success_response({"grid_image_url": image_url})
)
```

**前端解析**：
```typescript
// videoService.ts
export interface StoryboardGenerateResponse {
  grid_image_url: string;
}
```

**验证结论**：✅ 前后端均使用 `grid_image_url` 单字段

---

## Prompt 模板集中管理验证

**契约约束**："Prompt 模板与拼接逻辑仅在后端（前端只展示与编辑可见 Prompt）"

**验证**：

| 检查项 | 证据 | 状态 |
|--------|------|------|
| Prompt 模板集中管理 | `backend/app/core/prompts.py` | ✅ |
| `output_language` 规则注入 | `output_language_rule()` 函数 | ✅ |
| 前端不拼接 Prompt | 前端仅传递/展示/编辑，无模板逻辑 | ✅ |

---

## 验收 Checklist 复核

| 检查项 | 状态 | 证据 |
|--------|------|------|
| 四步流程可走通 | ✅ | workflow.py 实现完整链路，调用真实 AI 服务 |
| 每步都有失败路径提示 | ✅ | `_error_response()` 统一处理，返回脱敏错误 |
| Reroll 仅重绘图像 | ✅ | `handleRerollStoryboard` 仅调用 Step3 |
| Prompt 可复制/展示 | ✅ | GridWorkflow.tsx 支持 Prompt 展示和编辑 |
| 契约一致性 | ✅ | 字段、默认值、错误码均与 WP-GW-06A 一致 |

---

## 修复清单

| 问题 | 修复状态 | 文件 |
|------|----------|------|
| video.py 与 workflow.py 路由冲突 | ✅ 已修复 | `backend/app/api/routes/video.py` |
| video.py Schema 重复定义 | ✅ 已修复 | `backend/app/schemas/video.py` |

---

## 遗留建议

1. **Mock 模式开关**：建议后续添加环境变量控制 Mock/真实服务切换，便于本地开发
2. **日志增强**：workflow.py 已有基础日志，可考虑增加 latency_ms 指标

---

## 复核结论

**✅ 通过复核**

- 后端实现（Codex）符合 WP-GW-06A 冻结契约
- 前端实现（Gemini）符合契约字段和状态机要求
- Reroll 实现正确，仅重绘图像不触发 LLM
- 九宫格产物形态正确使用 `grid_image_url` 单字段
- 路由冲突问题已修复

---

## 签署

- **复核人**：Claude Agent
- **复核日期**：2026-01-07
- **复核版本**：v1.0


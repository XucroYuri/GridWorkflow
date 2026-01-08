# WP-GW-06 验收证据记录

**工作包**：WP-GW-06_GRIDWORKFLOW_FLOW（四步闭环）

**负责人**：Joint（后端：Codex，前端：Gemini）

**证据类型**：代码实现 + 接口形态说明

---

## 验收 Checklist 对应证据

### 1) 四步流程可走通（Step1 → Step4）

**后端接口已按契约落地**：

| 步骤 | 接口 | 证据 |
|------|------|------|
| Step1 概念图生成 | `POST /api/v1/concept` | `backend/app/api/routes/workflow.py` |
| Step2 九宫格 Prompt | `POST /api/v1/storyboard/plan` | `backend/app/api/routes/workflow.py` |
| Step3 九宫格生成 | `POST /api/v1/storyboard/generate` | `backend/app/api/routes/workflow.py` |
| Step4 视频 Prompt | `POST /api/v1/video/prompt` | `backend/app/api/routes/workflow.py` |

**响应中包含可复制的 Prompt 文本**：

| 接口 | 返回字段 |
|------|----------|
| `/concept` | `concept_prompt` |
| `/storyboard/plan` | `storyboard_prompt` |
| `/video/prompt` | `video_prompt` |

> 证据位置：`backend/app/api/routes/workflow.py`

---

### 2) 失败路径提示（字段缺失 / 上游错误 / 超时）

**字段缺失提示**：
- 必填字段校验返回 `BAD_REQUEST` + 明确字段提示
- 证据位置：`backend/app/api/routes/workflow.py`（`_field_required_message` 与各步骤校验）

**上游错误/超时**：
- LLM 与图像代理统一由 `APIError` 映射返回 `UPSTREAM_ERROR` / `TIMEOUT`
- 证据位置：`backend/app/services/ai_service.py`
- 接口落地：`backend/app/api/routes/workflow.py` 捕获并返回统一错误结构

---

### 3) Reroll 仅重绘（不触发 LLM）

**实现说明**：
- Step1（概念图）与 Step3（九宫格图）均只调用图像生成 `generate_image`
- Step2 / Step4 才调用文本 LLM `analyze_text`

**证据位置**：
- `backend/app/api/routes/workflow.py`：`concept` 与 `storyboard_generate` 使用 `generate_image`
- `backend/app/api/routes/workflow.py`：`storyboard_plan` 与 `video_prompt` 使用 `analyze_text`

---

### 4) Prompt 模板仅在后端拼接 + output_language 规则

**模板集中管理**：
- Prompt 拼接在 `backend/app/core/prompts.py` 完成
- 前端仅接收与编辑可见 Prompt

**output_language 生效**：
- Step2/Step4 注入 `output_language` 规则到系统提示词
- 证据位置：`backend/app/core/prompts.py`（`output_language_rule` 与系统提示构建）

---

## 备注

- 仅后端实现与接口契约一致性说明；前端 UI 状态机由 Gemini 交付。

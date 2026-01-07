# 重构落地方案：GridWorkflow (AI自动化九宫格分镜与视频流工作台)

**版本**：2.0
**日期**：2026-01-07
**目标**：基于《产品需求文档：AI自动化九宫格分镜与视频流工作台》构建全新的轻量级项目 `GridWorkflow`。通过“Python后端 + React前端”的分离架构，复用现有项目中有价值的基础设施（API网关逻辑、UI基座），实现从"剧情片段"到"视频生成Prompt"的全链路闭环。

---

## 0. 架构师视角：关键不变量与方案可靠性（PDCA）

**PDCA 总则**：见 [PDCA-00_PROJECT_GOVERNANCE.md](../PDCA-00_PROJECT_GOVERNANCE.md)。

**关键不变量（冻结项）**：
*   **统一响应结构**：所有后端接口统一返回 `{ ok, data, error }`，禁止返回 raw data。
*   **Prompt 单一来源**：Prompt 模板与拼接逻辑仅在后端存在；前端只展示“可见 Prompt”与用户可编辑部分。
*   **API Client 单一入口**：前端所有请求必须走 `apiClient.ts`，禁止散落 `fetch`。
*   **外部依赖统一封装**：业务层不直接拼接外部 URL；视频供应商通过 `provider` 注册表选择。
*   **媒体统一出站**：图片/视频统一落对象存储（COS 或可替换实现），前端只持有 URL。

**需要明确化的设计边界（避免后期返工）**：
*   **任务与状态**：视频生成必须异步化，返回 `task_id`，并可查询状态与失败原因（脱敏）。
*   **成本与配额**：对生成类接口必须支持按用户/租户限流与并发控制（先最小实现，后增强）。
*   **部署约束**：Vercel Serverless 不适合长任务，必须以“异步 + 外部状态”方式运行。

---

## 1. 总体架构设计 (Architecture)

### 1.1 技术栈选择
*   **Frontend**: React 18 + TypeScript + Vite (复用现有技术栈)
*   **Backend**: Python 3.10+ (FastAPI)
    *   *选型理由*: Python 在处理复杂数据结构、LLM 逻辑编排及未来扩展 Agent 能力方面具有天然优势。FastAPI 提供高性能的异步接口支持。
*   **API Gateway**: 复用现有 `https://ai.t8star.cn/v1` 接口资源，由 Python 后端统一代理和鉴权。

### 1.2 架构图
```mermaid
graph TD
    User[用户浏览器] --> |HTTP/JSON| Frontend[React Frontend (Vite)]
    Frontend --> |REST API| Backend[Python Backend (FastAPI)]
    
    subgraph Backend Services
        API_Proxy[API Proxy Service]
        Workflow_Engine[Workflow Orchestrator]
        Video_Service[Sora2 Video Service]
        Storage_Service[Media Storage (COS)]
        Data_Service[Data Layer (MySQL - Future)]
    end
    
    Backend --> API_Proxy
    Backend --> Workflow_Engine
    
    API_Proxy --> |OpenAI Protocol| External_AI[AI Gateway (t8star.cn)]
    Workflow_Engine --> |Prompt/Context| API_Proxy
    Video_Service --> |/v2/videos/generations| External_AI
    Workflow_Engine --> Storage_Service
    Storage_Service --> Data_Service
```

---

## 2. 迁移与重构策略 (Migration Strategy)

采用 **"Hybrid Migration" (混合迁移)** 策略：不直接在旧项目上修改，而是新建项目仓库，有选择性地迁移代码。

### 2.0 原仓库保留与冻结 (必做)
*   **目标**：保留 `Grid-Cine-Director` 的完整历史与可运行版本，避免“清理误删”。
*   **做法**：
    1.  **只读标记**：在原仓库新增只读标记文件（如 `ARCHIVE_README.md`）说明冻结原因与日期。
    2.  **分支保护**：主分支只保留 bugfix，不再添加新功能。
    3.  **新仓库独立**：所有新开发进入 `GridWorkflow`，禁止回写到旧仓库。

### 2.1 两种迁移路径对比
**方案A：复制旧项目再删减**  
*优点*：初始化快，依赖齐全；*风险*：垃圾依赖与历史耦合保留太多，Agent 容易误删关键基础设施。  

**方案B：新建骨架 + 按清单迁移（推荐）**  
*优点*：边界清晰，可控；*风险*：初期需要更严格的迁移清单与对照表。  

**推荐**：采用方案B，迁移时只复制“白名单文件”，其余一律不进新仓库。

### Phase 1: 项目初始化 (Initialization)
1.  **新建仓库/目录**: `GridWorkflow`。
2.  **目录结构**:
    ```
    GridWorkflow/
    ├── backend/          # Python FastAPI Project
    │   ├── app/
    │   │   ├── api/      # Routes
    │   │   ├── core/     # Config, Security
    │   │   ├── services/ # Business Logic (LLM, Image, Video, Storage)
    │   │   ├── storage/  # COS Client / Upload Helpers
    │   │   ├── data/     # Repository Layer (MySQL - Future)
    │   │   └── main.py
    │   ├── requirements.txt
    │   └── .env
    ├── frontend/         # React Vite Project
    │   ├── src/
    │   │   ├── components/
    │   │   ├── hooks/
    │   │   ├── contexts/
    │   │   └── ...
    │   ├── package.json
    │   └── ...
    └── README.md
    ```

### Phase 1.0: 本地仓库落点 (第一阶段)
*   **暂存落点目录**：已迁移到独立项目根目录
*   **目标独立目录**：`F:\Code\GridWorkflow`（剥离后）
*   **目的**：作为新 GitHub 项目的预备仓库，先完成“架构骨架 + 关键服务样板”迁移。
*   **边界**：此目录只放新项目代码与文档，不再混入旧仓库内容。

### Phase 1.5: 迁移白名单 (Source of Truth)
以下文件仅作为“参考实现”，需迁移到新仓库时**重新整理路径与依赖**：
*   **API 网关逻辑**：`Grid-Cine-Director/server/routes/ai.ts`
*   **配置基座**：`Grid-Cine-Director/server/config.ts`
*   **前端 UI 基座**：`Grid-Cine-Director/components/Layout/*`、`components/Lightbox.tsx`、`components/Toast.tsx`
*   **队列/任务模型参考**：`Grid-Cine-Director/services/queueService.ts`（仅参考，不建议直接拷贝）

**禁止直接迁移**：`hooks/controllers/*`、`components/Modules/ScriptEditor`、`Timeline`、旧 `ProjectContext` 与全部脚本分析流水线。

### Phase 2: 后端重构 (Backend Reconstruction - Python)
*   **目标**: 替代现有的 `server/` (Node.js) 逻辑。
*   **任务**:
    1.  **环境搭建**: 配置 FastAPI, Uvicorn, Pydantic, HTTPX。
    2.  **API Proxy 移植**:
        *   将 `server/routes/ai.ts` 中的 `analyze` (Chat Completion) 逻辑移植为 Python 服务。
        *   将 `server/routes/ai.ts` 中的 `generate-image` (FormData/Fetch) 逻辑移植为 Python 服务 (使用 `httpx` 处理 Multipart Upload)。
    3.  **Prompt 管理**: 以 PRD Template A/B 为准，在后端 `backend/app/core/prompts.py` 统一管理，避免前后端重复拼接。

### Phase 3: 前端迁移 (Frontend Migration - React)
*   **目标**: 提取 UI 基座，抛弃复杂业务。
*   **保留清单**:
    *   **基础设施**: `vite.config.ts`, `tailwind.config.js`, `tsconfig.json`, `package.json` (依赖列表)。
    *   **UI 组件**: `src/components/Layout` (MainLayout), `src/components/ui` (如有), `DirectorChat` (简化版), `Lightbox`, `Toast`。
    *   **Hooks**: `useTheme`, 基础的 API 请求 Hooks (需适配新后端 URL)。
*   **剔除清单**:
    *   `ScriptEditor` (剧本编辑器), `Timeline` (时间轴), `AssetManager` (旧资产管理), `ProjectContext` (旧全局状态)。

### Phase 4: 业务闭环 (Implementation)
*   **GridWorkbench 模块**: 在新的前端架构中重新实现 `GridWorkbench`，逻辑与 V1.0 方案一致，但 API 调用指向新的 Python 后端。

---

## 3. 详细落地步骤

### 3.1 后端开发 (Backend)

#### 3.1.0 API 数据契约 (强约束)
所有接口统一返回 `{ ok: boolean, data?: any, error?: { code, message } }` 结构，避免前端在不同阶段解析分叉。
*   **可选用户密钥**：前端透传 `x-user-gemini-key`，后端优先使用该 Key 调用网关。

**错误码与可恢复性（必须统一）**：
*   `BAD_REQUEST`：字段缺失/取值非法/请求体过大（提示用户修改输入）
*   `UNAUTHORIZED`：未登录或鉴权失败（提示重新登录/检查权限）
*   `FORBIDDEN`：策略拒绝（合规、配额、弱鉴权不允许的接口）
*   `UPSTREAM_ERROR`：上游网关/供应商错误（提示稍后重试）
*   `TIMEOUT`：上游超时（提示稍后重试，必要时降级）

**幂等性与去重（建议在生成类接口启用）**：
*   前端可透传 `x-idempotency-key`，后端按 `{user_id, endpoint, key}` 做短期去重，避免重复扣费。

**输入安全（必须）**：
*   禁止后端按前端提供的任意 URL 下载媒体（SSRF 风险）；外部 URL 仅作为展示或需经过严格 allowlist 与 HEAD 校验。
*   base64 输入设置大小上限与数量上限（先文档约束，后实现硬门禁）。

**Request/Response 示例**：
```json
// POST /api/v1/concept
{
  "style": "Anime artwork, OLM studio style...",
  "plot": "剧情片段",
  "anchors": {
    "character": { "text": "人物描述", "image_base64": "data:image/png;base64,..." },
    "environment": { "text": "场景描述", "image_base64": null },
    "prop": { "text": "道具描述", "image_base64": null }
  },
  "aspect_ratio": "16:9",
  "image_size": "1K"
}
```
```json
// Response
{ "ok": true, "data": { "image_url": "https://..." } }
```

#### 3.1.1 核心服务 (`backend/app/services/ai_service.py`)
```python
from fastapi import UploadFile
import httpx
from app.core.config import settings

async def chat_completion(messages: list, model: str):
    # 复用 OpenAI SDK 或 HTTPX 调用 ai.t8star.cn
    pass

async def generate_image(prompt: str, ref_image: bytes | None, model: str):
    # 实现原 server/routes/ai.ts 中的 /images/edits 逻辑
    # 构造 multipart/form-data
    pass
```

#### 3.1.1.1 `/images/edits` 兼容示例 (重点)
```python
async def generate_image(prompt: str, ref_image: bytes | None, model: str, aspect_ratio: str, image_size: str):
    api_key = settings.AI_GATEWAY_API_KEY
    base_url = settings.AI_GATEWAY_BASE_URL
    files = {
        "image": ("reference.png", ref_image or EMPTY_1X1_PNG, "image/png"),
    }
    data = {
        "model": model,
        "prompt": prompt,
        "response_format": "url",
        "aspect_ratio": aspect_ratio,
        "image_size": image_size,
    }
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(f"{base_url}/images/edits", headers={"Authorization": f"Bearer {api_key}"}, data=data, files=files)
        r.raise_for_status()
        return r.json()
```
*注意*: 无 reference 也必须传 `image` 字段（1x1 PNG 兜底），否则网关可能报错。

#### 3.1.1.2 视频服务 (`backend/app/services/video_service.py`)
*   **双 API 来源**：
    1.  **Primary**：`https://ai.t8star.cn/v1`（Sora2 模型）
    2.  **Secondary**：预留其他视频供应商（仅接口封装，不上生产）
*   **统一入口**：`VideoProviderRegistry` 根据 `provider` 选择实现，避免业务层直接拼接 URL。
*   **参考文档**：`docs/api/ai.t8star.cn/sora2`
*   **任务查询**：`Sora2查询任务.md` 已提供 `/v2/videos/generations/{task_id}` 规范。

```python
class VideoProviderRegistry:
    def __init__(self, providers: dict):
        self.providers = providers

    def get(self, provider: str):
        return self.providers.get(provider, self.providers["t8star"])

# t8star Sora2
async def sora2_generate(payload: dict):
    # POST /v2/videos/generations
    pass

async def sora2_query(task_id: str):
    # TODO: 对应查询任务接口（文档待补齐）
    pass
```

#### 3.1.2 路由定义 (`backend/app/api/endpoints/workflow.py`)
*   `POST /api/v1/concept`: 生成概念图 (Step 1)。
*   `POST /api/v1/storyboard/plan`: 生成九宫格 Prompt (Step 2)。
*   `POST /api/v1/storyboard/generate`: 生成九宫格图片 (Step 3)。
*   `POST /api/v1/video/prompt`: 生成视频 Prompt (Step 4)。
*   `POST /api/v1/video/generate`: 触发 Sora2 视频生成。
*   `GET /api/v1/video/status/{task_id}`: 查询视频任务状态（如接口可用）。
*   `POST /api/v1/media/upload`: 上传任意图片/视频到 COS（兜底）。

#### 3.1.2.1 接口字段最小规范 (避免歧义)
*   **/concept**：`style`, `plot`, `anchors`, `aspect_ratio`, `image_size`
*   **/storyboard/plan**：`style`, `plot`, `anchors`, `concept_prompt`(可选), `concept_image_url`(可选), `output_language`(可选，默认 `zh-CN`)
*   **/storyboard/generate**：`storyboard_prompt`, `reference_image_base64`(可选), `aspect_ratio`, `image_size`
*   **/video/prompt**：`storyboard_prompt`, `original_plot`, `duration`(默认10), `fps`(默认60), `output_language`(可选，默认 `zh-CN`)
*   **/video/generate**：`prompt`, `model`, `images`(可选), `aspect_ratio`, `hd`, `duration`, `provider`(默认 t8star)
*   **/video/status**：`task_id`, `provider`
*   **/media/upload**：`file`, `purpose`(image|video), `content_type`

#### 3.1.2.2 Sora2 参数对齐 (来自 API 参考)
*   **模型**：`sora-2` / `sora-2-pro`
*   **时长**：`10` / `15` / `25`（`25` 仅 `sora-2-pro`）
*   **比例**：`16:9` / `9:16`
*   **图生视频**：`images` 必填（url 或 base64）
*   **故事板视频**：Prompt 需按 `Shot N` 格式拼接（见文档示例）

#### 3.1.3 Prompt 管理 (`backend/app/core/prompts.py`)
*   **模板隔离**：Template A/B 独立函数，不要混入业务逻辑。
*   **输出类型**：Template A/B 输出纯文本，不用 JSON 结构。

#### 3.1.3.1 媒体存储 (Tencent COS)
*   **目的**：所有图片/视频通过 COS 存储并返回可访问 URL，前端不保存大文件。
*   **核心组件**：`backend/app/storage/cos_client.py`
*   **策略**：
    *   生成后立即上传 COS。
    *   前端仅保存 URL + metadata（大小、时长、模型等）。
    *   支持短期签名 URL（如 1-24 小时）。

#### 3.1.3.2 数据层预留 (MySQL - Future)
*   **接口先行**：定义 Repository 接口（保存任务/Prompt/媒体 URL），实现先返回 `NotImplementedError`。
*   **迁移路径**：未来将临时文件或内存数据迁移到 MySQL 与对象存储索引表。

#### 3.1.4 可观测性与重试
*   **日志字段**：`request_id`、`model`、`step`、`latency_ms`。
*   **重试策略**：LLM 文本 1 次重试；图像生成 0 次重试（避免重复扣费）。

**建议补充指标（用于 Check/回归）**：
*   `endpoint`、`status_code`、`provider`（视频）、`task_id`（视频）
*   `user_id`（仅存 hash/截断标识，不记录原值）、`payload_size_bytes`
*   `cost_hint`（如上游返回可用，允许仅记录聚合值）

**脱敏规则（必须）**：
*   禁止在日志中输出：密钥、完整 Prompt、签名 URL 查询参数、用户上传的 base64 原文。

#### 3.1.5 环境配置基线
*   `AI_GATEWAY_BASE_URL`：默认 `https://ai.t8star.cn/v1`
*   `AI_GATEWAY_API_KEY`：网关 Key（可被 `x-user-gemini-key` 覆盖）
*   `DEFAULT_TEXT_MODEL`：例如 `gemini-3-pro-preview`
*   `DEFAULT_IMAGE_MODEL`：例如 `gemini-3-pro-image-preview`
*   `CORS_ORIGINS`：允许前端访问的域名列表

### 3.2 前端开发 (Frontend)

#### 3.2.1 状态管理 (`GridContext`)
使用 React Context API 管理简单的线性工作流状态，不再引入复杂的 Redux 或 Zustand (除非必要)。

#### 3.2.2 组件开发
在 `frontend/src/features/GridWorkflow` 下开发：
*   `InputForm.tsx`: 接收剧情和资产描述。
*   `ConceptStage.tsx`: 展示和确认概念图。
*   `StoryboardStage.tsx`: 展示 Prompt 编辑器和九宫格结果。
*   `ExportStage.tsx`: 展示最终视频 Prompt。

#### 3.2.2.1 视频独立页面 (仿 Sora UI)
*   **路由**：`/video`
*   **目标**：仿 `https://sora.chatgpt.com/` 的输入/预览体验，用于手动视频生成与自动流程最终执行。
*   **布局建议**：
    *   左侧：Prompt 编辑器 + 参数（model, duration, aspect_ratio, hd, images）
    *   右侧：任务列表 + 进度条 + 视频预览（来自 COS URL）
*   **模式**：
    1.  手动模式：用户直接输入 Prompt 生成。
    2.  自动模式：来自 GridWorkflow 最终视频 Prompt 的一键生成。

#### 3.2.3 前端 API Client (最小封装)
*   **必须统一**：所有请求通过 `apiClient.ts`，防止 Agent 私自写 `fetch` 导致风格不一致。
*   **API Base**：使用 `VITE_API_BASE_URL` (如 `http://localhost:8000/api/v1`) 统一拼接路径。
```typescript
// frontend/src/services/apiClient.ts
export const post = async <T>(url: string, body: unknown): Promise<T> => {
  const res = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  const json = await res.json();
  if (!json.ok) throw new Error(json.error?.message || 'Request failed');
  return json.data as T;
};
```

---

## 4. 开发计划表

1.  **Day 1 (Setup)**:
    *   初始化 Git 仓库 `GridWorkflow`。
    *   搭建 Python FastAPI 骨架，跑通 `/health` 接口。
    *   搭建 React Vite 骨架，配置 Tailwind CSS。
2.  **Day 2 (Backend Core)**:
    *   实现 Python 版 AI Proxy (Chat & Image)。
    *   测试与 `ai.t8star.cn` 的连通性。
3.  **Day 3 (Frontend Migration)**:
    *   迁移 Layout, Toast, Lightbox 等基础 UI。
    *   搭建 GridWorkflow 的基础页面路由。
4.  **Day 4 (Workflow Logic)**:
    *   联调 Step 1 & Step 2 (概念图 + 分镜规划)。
    *   联调 Step 3 & Step 4 (分镜生图 + 视频转化)。
5.  **Day 5 (Polish)**:
    *   UI 美化。
    *   异常处理 (重试机制)。

---

## 5. 风险与注意点

*   **API 签名差异**: 确保 Python 版 `httpx` 发送的 `FormData` 格式与原 Node.js 版完全一致（特别是 `boundary` 和文件字段名 `image` vs `file`），否则可能导致网关报错。
*   **跨域问题 (CORS)**: FastAPI 需配置 `CORSMiddleware` 允许前端 `localhost:xxxx` 访问。
*   **环境变量**: 确保 `.env` 文件在前后端都正确配置，特别是 `API_KEY` 和 `BASE_URL`。
*   **模型参数不一致**: `image_size` 与 `aspect_ratio` 字段值需与网关约定一致（`1K/2K/4K`、`16:9`），否则返回 400。
*   **图像引用丢失**: 若前端未传 base64，后端会使用 1x1 PNG 兜底，容易导致风格漂移。
*   **COS 权限与跨域**: COS Bucket 需允许后端写入，必要时开启 CDN 或签名 URL。
*   **大文件上传**: 视频尺寸大，需预留分片上传或异步上传策略，避免超时。

---

## 6. 迁移执行清单 (推荐落地流程)

1.  **新仓库初始化**：建立 `GridWorkflow` 空仓库，提交初始 README（记录“迁移白名单”）。
2.  **后端优先**：先完成 FastAPI 代理层，确保 `/images/edits` 能稳定返回。
3.  **前端骨架**：创建 React 基座 + Layout/Toast/Lightbox，保证 UI 先能跑。
4.  **单步闭环**：先打通 “概念图” 单接口（前后端联调）再进入九宫格与视频 Prompt。
5.  **分步验收**：每一步生成结果都落盘并可复制，避免“全流程才发现失败”。

---

## 7. Agent 参与风险与防护 (高危区域提示)

### 7.1 高危区域清单
*   **API 代理实现**：`backend/app/services/ai_service.py` 的 multipart 结构极易被误改。
*   **Prompt 模板**：Template A/B 不允许被“自动美化”或“结构化”，必须是纯文本。
*   **统一响应结构**：`{ ok, data, error }` 不允许被 Agent 改成直接返回 raw data。
*   **前端 API Client**：禁止散落 `fetch`，否则错误处理不可控。

### 7.2 防护策略
*   **关键文件只读提示**：在文件头部写明确注释 “DO NOT AUTO-REFACTOR”。
*   **引导式任务拆分**：Agent 每次只完成单个步骤（例如仅概念图生成）。
*   **验收脚手架**：每个接口提供 `curl` 示例，Agent 改动后先自检再提交。

---

## 8. 数据与状态策略 (简化版)

*   **无持久化优先**：先以 in-memory 或临时文件保存图片（避免数据库复杂度）。
*   **显式 Reroll**：Reroll 仅重复生图，不修改 Prompt 文本。
*   **输出可追溯**：每个阶段的 Prompt 与图片 URL 需保存在前端状态中，便于回溯。
*   **Base64 限制**：前端在上传时进行压缩/裁剪（建议 < 2MB），避免 JSON 过大导致 413。

---

## 9. 验收标准 (Acceptance Criteria)

*   **功能闭环**：输入 → 概念图 → 九宫格 Prompt → 九宫格图 → 视频 Prompt 全流程可跑通。
*   **稳定性**：概念图和九宫格图支持“只重绘图像”。
*   **一致性**：九宫格图与概念图风格一致（人工验收）。
*   **合规性**：视频 Prompt 不含 emoji，具备 10s/60fps/运镜描述。

---

## 10. 安全性与密钥管理 (Security)

*   **密钥管理**：只允许后端读取 `AI_GATEWAY_API_KEY`、`COS_SECRET_KEY` 等关键密钥；前端不接触任何密钥。
*   **脱敏日志**：日志中禁止输出完整 Prompt、密钥、COS URL 的签名参数。
*   **签名访问**：媒体 URL 优先使用 COS 签名或短期可用链接。
*   **提示词保护**：系统 Prompt/模板仅在后端拼接；前端仅展示必要的可见 Prompt 或摘要。
*   **防滥用**：对 `/video/generate`、`/storyboard/generate` 设置速率限制与配额。

---

## 11. 前端暴露控制 (Frontend Exposure)

*   **不可见 Prompt**：隐式运行 Prompt（系统提示词、拼接逻辑、负面提示词）仅在后端执行。
*   **响应最小化**：前端返回 `task_id`、状态与结果 URL，不直接返回完整内部推理细节。
*   **加密与传输**：统一使用 HTTPS；对敏感字段加密传输与存储。
*   **权限校验**：媒体 URL 访问需经过后端校验或使用签名 URL。

---

## 12. 高并发与多用户支持 (Concurrency & Multi-User)

*   **任务队列**：后端使用队列管理（按用户并发上限）。
*   **限流策略**：按用户、IP、接口维度限流（避免刷接口）。
*   **任务隔离**：任务与产物必须绑定 `user_id` 或 `tenant_id`。
*   **资源回收**：过期任务与临时文件自动清理。
*   **多租户预留**：接口层统一接受 `user_id`/`tenant_id`，后续可接入数据库。

---

## 13. IP 白名单与弱鉴权 (Enterprise Access)

*   **用途**：企业内网访问时减少登录干扰，但不可绕过关键操作。
*   **规则**：仅允许白名单 IP 触发“弱鉴权模式”，仍需最小权限校验。
*   **可信代理**：只信任 Vercel/负载均衡器注入的 `X-Forwarded-For`，否则以 `req.client` 为准。
*   **策略**：对生成类接口保留强校验，对只读接口可减弱校验。
*   **配置**：`IP_ALLOWLIST`（支持 CIDR）。
*   **默认预设**：`97.64.29.114`（可在部署时替换）。

---

## 14. Vercel 部署适配 (Deployment)

*   **适配策略**：前端静态托管 + 后端 Serverless Functions。
*   **长任务规避**：视频生成必须异步化，立即返回 `task_id`，前端轮询状态。
*   **外部存储**：媒体文件统一上传 COS，避免本地文件系统依赖。
*   **请求体限制**：base64 上传限制 < 2MB；大文件先传 COS，再传 URL。
*   **环境变量**：密钥仅通过 Vercel Env 注入，禁止写入仓库。

---

## 15. Supabase 认证与云端数据 (Auth & Cloud Data)

*   **认证**：使用 Supabase Auth 作为唯一身份入口（Email/OTP/OAuth 任选）。
*   **鉴权**：后端校验 Supabase JWT，拒绝匿名访问核心接口。
*   **数据存储**：将用户元数据、任务记录、媒体索引存入 Supabase Postgres（避免本地持久化）。
*   **权限隔离**：按 `user_id`/`tenant_id` 进行 Row Level Security (RLS)。
*   **前后端分工**：前端只持有 Supabase 公钥，服务端使用 Service Role Key 进行管理操作。

---

## 16. 计划文档拆分 (Agent Friendly)

计划文档位于 `docs/`，一个文档对应一个可独立实现的模块：
*   `PRECHECK-SEC_ARCH_AGENT.md`
*   `PLAN-00_BOOTSTRAP.md`
*   `PLAN-01_BACKEND_PROXY.md`
*   `PLAN-02_VIDEO_SORA2.md`
*   `PLAN-03_STORAGE_COS.md`
*   `PLAN-04_FRONTEND_SHELL.md`
*   `PLAN-05_GRIDWORKFLOW_FLOW.md`
*   `PLAN-06_VIDEO_STUDIO_UI.md`
*   `PLAN-07_DATA_FUTURE_MYSQL.md`
*   `PLAN-08_VERCEL_DEPLOY.md`
*   `PLAN-09_SUPABASE.md`
*   `PLAN-10_IP_ALLOWLIST.md`
*   `PLAN-11_MIGRATION_ACTIONS.md`

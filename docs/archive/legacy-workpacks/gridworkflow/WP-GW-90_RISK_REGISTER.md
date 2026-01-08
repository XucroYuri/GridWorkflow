# WP-GW-90_RISK_REGISTER（风险清单与兜底策略）

**负责人团队**：Joint

**目标**：集中整理 GridWorkflow 的高风险场景与兜底策略，为 PRECHECK 与各 WP 提供统一风险基线。

---

## 输入

- [PRECHECK-SEC_ARCH_AGENT.md](../../PRECHECK-SEC_ARCH_AGENT.md)
- 审计类文档：`../../AUDIT_REPORT.md`、`../../FULL_PROJECT_CODE_AUDIT_REPORT.md`

---

## 输出（交付物）

- 风险清单：按安全/稳定/成本/体验分类
- 兜底策略：针对每类风险给出最小防御与回滚方案
- 对 PRECHECK 与各 WP 的反向链接（注明"本风险已覆盖于哪些文档"）

---

## 冻结约束（必须）

> **全局冻结项**：统一遵守 [FROZEN_INVARIANTS.md](../FROZEN_INVARIANTS.md)

**本工作包特定约束**：
- 风险评估必须覆盖全局冻结项相关的安全门禁
- 高成本操作（视频/图像生成）必须有成本与并发风险防护

---

## 1. 安全类风险

### 1.1 密钥与敏感信息泄露
- **描述**：API Key、COS 密钥、Service Role Key、JWT、完整 Prompt、签名 URL 查询参数等被写入日志、前端或错误返回体。
- **来源与覆盖**：
  - PRECHECK：1.安全性“必须排除/必须确认/建议”条款、3.1 脱敏规则。
  - WP：WP-GW-02_BACKEND_PROXY、WP-GW-04_STORAGE_COS、WP-GW-09_AUTH_SUPABASE。
- **兜底策略**：
  - 统一使用 `{ ok, data, error }`，`error` 只暴露 code 与安全 message。
  - 日志字段限制为 `request_id`、`model`、`step`、`latency_ms`。
  - 在实现中集中封装脱敏逻辑（例如日志/错误封装 helper），并在 PRECHECK 中作为门禁。

### 1.2 上传与解析炸弹
- **描述**：用户上传超大文件或畸形文件，导致内存/CPU 被打爆。
- **来源与覆盖**：
  - PRECHECK：上传类与 base64 输入的硬门禁；“禁止仅凭扩展名/Content-Type 信任”。
  - WP：WP-GW-02_BACKEND_PROXY、WP-GW-04_STORAGE_COS。
- **兜底策略**：
  - 为图片/视频/base64 设置尺寸和数量上限，超限返回 `BAD_REQUEST`。
  - 解析前做基础校验，避免直接把未校验输入交给上游或本地解析。

### 1.3 SSRF 与 URL 信任问题
- **描述**：后端直接使用前端传入 URL 发起请求，引发 SSRF 或访问内部资源。
- **来源与覆盖**：
  - PRECHECK：禁止后端直接信任前端传入 URL 并下载。
  - WP：WP-GW-02_BACKEND_PROXY、WP-GW-04_STORAGE_COS。
- **兜底策略**：
  - 对外部 URL 统一走网关/代理，并做域名/协议白名单。
  - 禁止后端直接 download 任意 URL；若必须支持，需专门 WP 与 PRECHECK 条目。

### 1.4 弱鉴权与 IP 白名单滥用
- **描述**：将 IP 白名单当作管理员或完全免鉴权，导致敏感操作被绕过。
- **来源与覆盖**：
  - PRECHECK：IP 白名单仅用于弱化鉴权，不能绕过关键操作。
  - WP：WP-GW-10_IP_ALLOWLIST、WP-GW-09_AUTH_SUPABASE。
- **兜底策略**：
  - IP 白名单仅覆盖只读接口，生成类接口仍需 JWT。
  - 默认不开启弱鉴权，必须显式配置。
  - 对可疑访问做审计日志。

### 1.5 多租户与数据泄露
- **描述**：多用户之间任务/媒体记录可互相访问。
- **来源与覆盖**：
  - PRECHECK：Supabase JWT 校验、RLS 绑定 `user_id`。
  - WP：WP-GW-09_AUTH_SUPABASE、PLAN-09_SUPABASE。
- **兜底策略**：
  - 所有核心接口必须校验 JWT。
  - 表结构按 `user_id`/`tenant_id` 做 RLS。
  - 审计数据访问错误（越权访问立即阻断并记录）。

### 1.6 CORS 配置不当
- **描述**：CORS 配置为 `*` 或过于宽松，导致跨站请求伪造或 API 滥用。
- **来源与覆盖**：
  - PRECHECK：必须确认"CORS 白名单可配置（非 `*`）"。
  - WP：WP-GW-02_BACKEND_PROXY、WP-GW-08_DEPLOY_VERCEL。
- **兜底策略**：
  - 后端 CORS 白名单通过环境变量 `ALLOWED_ORIGINS` 配置。
  - 生产环境禁止使用 `*`，仅允许明确的前端域名。
  - 审计 CORS 配置变更。

### 1.7 task_id 枚举与日志注入
- **描述**：task_id 格式无校验，攻击者可通过枚举获取他人任务状态，或注入恶意字符污染日志。
- **来源与覆盖**：
  - PRECHECK：必须确认"任务查询接口对 `task_id` 做格式与长度校验，避免枚举与日志注入"。
  - WP：WP-GW-03_VIDEO_SORA2。
- **兜底策略**：
  - `task_id` 必须为 UUID 格式，非法格式返回 `BAD_REQUEST`。
  - 长度限制 36 字符，超限直接拒绝。
  - 日志打印前对 `task_id` 做字符白名单校验（仅允许 `[a-zA-Z0-9-]`）。

### 1.8 BYOK（用户自有密钥）安全
- **描述**：用户通过 `x-user-gemini-key` 等方式使用自有 API Key，存在前端存储泄露与传输安全风险。
- **来源与覆盖**：
  - PRECHECK：必须确认"`x-user-gemini-key` 为可选头，优先使用但不记录"。
  - 审计报告：`localStorage.getItem('GCD_USER_KEY')` 风险、XOR 混淆不安全。
  - WP：WP-GW-02_BACKEND_PROXY、WP-GW-09_AUTH_SUPABASE。
- **兜底策略**：
  - 用户 Key 仅存储于客户端（localStorage + 可选加密），绝不上传服务端存储。
  - 用户 Key 在请求头传输时，后端仅使用不记录（禁止落日志）。
  - 前端提供"退出/清除密钥"机制，用户可随时撤销本地缓存。
  - 优先提示用户在安全网络环境下使用 BYOK。

### 1.9 Prompt 注入攻击
- **描述**：用户输入恶意内容覆盖或干扰系统 Prompt，导致 LLM 输出不可控或泄露内部规则。
- **来源与覆盖**：
  - PRECHECK：建议"对 Prompt 注入风险做最小防护：系统模板与用户输入分区拼接，用户输入不允许覆盖系统规则"。
  - WP：WP-GW-06_GRIDWORKFLOW_FLOW、WP-GW-06A_FLOW_CONTRACT。
- **兜底策略**：
  - 系统 Prompt 与用户输入分区拼接，使用 `{{USER_INPUT}}` 占位符。
  - 禁止用户输入包含 `{{` 或 `}}` 等模板标记（过滤或转义）。
  - 对用户输入长度做上限控制（如 2000 字符）。
  - 后端日志不记录完整 Prompt 内容。

---

## 2. 稳定性与架构类风险

### 2.1 前端直连上游 / 业务层直连上游
- **描述**：前端直接请求 `ai.t8star.cn` 或业务层代码直接访问外部 API，绕开代理与限流。
- **来源与覆盖**：
  - PRECHECK：架构稳定性“必须排除”；前端禁止直连 `ai.t8star.cn`。
  - WP：WP-GW-02_BACKEND_PROXY、WP-GW-05_FRONTEND_SHELL。
- **兜底策略**：
  - 统一 API Client（前端 `apiClient.ts`）、统一后端代理。
  - 审计代码中禁止出现硬编码外部 URL 调用。

### 2.2 长任务与 Serverless 超时
- **描述**：在 Vercel 等 Serverless 环境直接等待视频生成，导致超时和不稳定。
- **来源与覆盖**：
  - PRECHECK：建议异步任务、统一超时策略。
  - WP：WP-GW-03_VIDEO_SORA2、WP-GW-08_DEPLOY_VERCEL。
- **兜底策略**：
  - 视频生成必须异步，立即返回 `task_id` 并通过 `/video/status` 轮询。
  - 超时设定与 Provider 限制一致，不在 Serverless 内等待长任务完成。

### 2.3 Prompt 模板与多层拼接
- **描述**：前后端分别拼 Prompt，导致不可控和不稳定。
- **来源与覆盖**：
  - PRECHECK：Prompt 仅在后端拼接，前端只接收可展示摘要。
  - WP：WP-GW-02_BACKEND_PROXY、WP-GW-06_GRIDWORKFLOW_FLOW、PLAN-05_GRIDWORKFLOW_FLOW。
- **兜底策略**：
  - 模板集中在 `core/prompts.py`；前端仅编辑可见 Prompt 文本。
  - 文档明确 `{{Output_Language_Rule}}` 由后端控制语种。

### 2.4 任务状态丢失与不可追踪
- **描述**：任务仅存在于前端或内存，刷新/重启后状态丢失。
- **来源与覆盖**：
  - PRECHECK：异步任务持久化与轮询建议。
  - WP：WP-GW-03_VIDEO_SORA2、WP-GW-07_VIDEO_STUDIO_UI。
- **兜底策略**：
  - 后端维护最小任务索引（可先内存，后续 MySQL/Supabase）。
  - 前端刷新后通过 `task_id` 从服务端恢复状态。

### 2.5 Video Provider 注册表风险
- **描述**：视频生成 Provider 未统一管理，业务层直接硬编码 Provider 选择，导致难以扩展和切换。
- **来源与覆盖**：
  - PRECHECK：必须确认"Video Provider 通过注册表选择，默认仅允许 `t8star`"。
  - WP：WP-GW-03_VIDEO_SORA2、SPEC-ARCH-01_MODULAR_VIDEO_ARCH。
- **兜底策略**：
  - 后端维护 Provider 注册表，通过配置选择激活的 Provider。
  - 默认仅启用 `t8star`，扩展新 Provider 需显式注册。
  - 前端不感知 Provider 细节，仅调用统一接口。

### 2.6 跨 Tab 并发控制失效
- **描述**：用户在多个浏览器 Tab 中同时操作，各 Tab 独立的内存队列导致实际并发量突破限制。
- **来源与覆盖**：
  - 审计报告：queueService 基于单 Tab 内存，多 Tab 实际并发 = N * Limit。
  - WP：WP-GW-03_VIDEO_SORA2、WP-GW-07_VIDEO_STUDIO_UI。
- **兜底策略**：
  - 短期：后端做全局并发限制（按 user_id），不依赖前端队列。
  - 中期：前端使用 `SharedWorker` 或 `localStorage` 互斥锁管理跨 Tab 并发。
  - 生成接口返回 `RATE_LIMITED` 时，前端明确提示用户。

---

## 3. 成本与配额类风险

### 3.1 生成接口被刷爆
- **描述**：暴露生成接口无速率限制，导致成本和上游配额被耗尽。
- **来源与覆盖**：
  - PRECHECK：禁止无速率限制暴露生成接口；建议 Rate Limit。
  - WP：WP-GW-02_BACKEND_PROXY、WP-GW-03_VIDEO_SORA2、WP-GW-07_VIDEO_STUDIO_UI。
- **兜底策略**：
  - 按用户/租户限制并发数与速率。
  - 对批量调用/脚本调用做最小防护（如验证码、节流）。

### 3.2 重试策略导致重复计费
- **描述**：生成类接口重试策略不当，导致一次操作多次计费。
- **来源与覆盖**：
  - PRECHECK：建议文本 1 次重试、图像 0 次、视频 0 次。
  - WP：WP-GW-02_BACKEND_PROXY、WP-GW-03_VIDEO_SORA2。
- **兜底策略**：
  - 生成类接口默认不重试，高层逻辑由用户手动再试。
  - 日志中为每次调用打上 `request_id` 便于对账。

---

## 4. 体验与交互类风险

### 4.1 长任务无进度/状态反馈不足
- **描述**：前端等待视频/九宫格生成时缺少明确状态或进度提示，导致用户误以为卡死并重复提交。
- **来源与覆盖**：
  - PRECHECK：异步任务持久化、轮询间隔建议（>= 3s）、超时策略
  - WP：WP-GW-03_VIDEO_SORA2、WP-GW-06_GRIDWORKFLOW_FLOW、WP-GW-07_VIDEO_STUDIO_UI
- **兜底策略**：
  - 统一 `task_id` + `status` 枚举并在前端映射文案（queued/running/succeeded/failed）
  - 轮询间隔 >= 3s，失败时明确提示并允许用户手动重试（不自动重试）

### 4.2 输出语言/文案不一致
- **描述**：未统一 `output_language` 与提示文案规则，导致界面中英混杂或内容不可读。
- **来源与覆盖**：
  - PRECHECK：Prompt 仅后端拼接、前端只接收可展示摘要
  - WP：WP-GW-06A_FLOW_CONTRACT、WP-GW-06_GRIDWORKFLOW_FLOW、WP-GW-05_FRONTEND_SHELL
- **兜底策略**：
  - 后端默认 `output_language=zh-CN` 并注入 `{{Output_Language_Rule}}` 控制输出语言
  - 前端仅展示后端返回文本，不在前端重写 prompt

### 4.3 九宫格产物形式不一致
- **描述**：九宫格产物返回形式不明确（9 张 URL 或单张拼图），导致前端渲染错乱或无法展示。
- **来源与覆盖**：
  - WP：WP-GW-06A_FLOW_CONTRACT、WP-GW-06_GRIDWORKFLOW_FLOW、WP-GW-07_VIDEO_STUDIO_UI
- **兜底策略**：
  - 契约冻结返回形式（9 张 URL 或单张拼图二选一），并在后端统一转换
  - 前端仅按契约分支渲染，契约外返回按 `BAD_REQUEST` 处理

---

## 5. Agent 行为与协作类风险

### 5.1 Agent 自动重构破坏契约/结构
- **描述**：Agent 修改目录结构、服务注册、统一响应结构或 Prompt 模板形态。
- **来源与覆盖**：
  - PRECHECK：Agent 友好检查、Vibe Coding 协作规范。
  - WP：WP-GW-00_GOVERNANCE、AGENT-00_WORKSTREAMS。
- **兜底策略**：
  - 明确冻结项（响应结构、Prompt 单一来源、API Client 单一入口）。
  - 每个 WP/PLAN 有“Agent 上下文注入包”限制可变范围。

### 5.2 Agent 将 Prompt 强制结构化为 JSON
- **描述**：为了“好解析”，Agent 把 Prompt 改成 JSON 输出，破坏兼容性。
- **来源与覆盖**：
  - PRECHECK：必须排除“批量修改 Prompt 模板为 JSON/结构化输出”。
  - WP：WP-GW-06_GRIDWORKFLOW_FLOW、PLAN-05_GRIDWORKFLOW_FLOW。
- **兜底策略**：
  - Prompt 模板输出定义为纯文本；在文档中明确禁止 JSON 化。
  - 若需要结构化结果，另建专门接口与模板，不改现有链路。

### 5.3 跨模块混改与文档不同步
- **描述**：一次改动涉及多个 PLAN/WP，但文档不更新或更新不一致。
- **来源与覆盖**：
  - PRECHECK：Vibe Coding 规范（单模块聚焦、文档与实现同步）。
  - WP：所有 WP 的验收与回滚小节。
- **兜底策略**：
  - 每次变更限定在单个 WP/PLAN 范围内。
  - 修改实现时必须同时更新对应 PLAN/WP 的输入输出/验收/风险。


---

## Agent 启动上下文（复制即用）

```text
你是 Joint Agent（风险与兜底负责人）。
目标：集中整理 GridWorkflow 的高风险场景与兜底策略，使 PRECHECK、PLAN-* 与 WP-* 在风险维度保持一致。
验收：关键风险（密钥泄露、成本爆炸、长任务超时、枚举攻击、Prompt 注入、体验类风险等）在 PRECHECK 与 WP-GW-90 中都有清晰记录与兜底策略。
```

---

## 验收 Checklist

- PRECHECK 中的“必须排除/必须确认”与本风险清单对应
- 视频/图像等高成本接口的成本与并发风险有明确防护
- 体验类风险（状态反馈、输出语言一致性）有兜底方案
- Agent 相关的风险（自动重构、结构化 Prompt、目录改动）有清晰边界

---

## 回滚策略

- 若风险清单组织方式不合适，可回退为简单列表形式，再逐步结构化

---

## 验收证据（Checklist 对照表）

### ✅ 证据 1：PRECHECK "必须排除/必须确认" 与本风险清单对应

| PRECHECK 条目 | 类型 | 风险清单覆盖 |
|--------------|------|-------------|
| 禁止将密钥输出到日志 | 必须排除 | 1.1 密钥与敏感信息泄露 |
| 禁止在前端保存任何后端密钥或 COS 凭证 | 必须排除 | 1.1 密钥与敏感信息泄露 |
| 禁止后端直接信任前端传入的 URL（SSRF） | 必须排除 | 1.3 SSRF 与 URL 信任问题 |
| 禁止在前端暴露完整 Prompt 模板 | 必须排除 | 1.1 + 2.3 Prompt 模板单一来源 |
| 禁止在前端保存 Supabase Service Role Key | 必须排除 | 1.1 密钥与敏感信息泄露 |
| 禁止用 X-Forwarded-For 直接做 IP 放行 | 必须排除 | 1.4 弱鉴权与 IP 白名单滥用 |
| 禁止将上游完整错误体透传给前端 | 必须排除 | 1.1 + FROZEN_INVARIANTS 错误脱敏 |
| 禁止对上传文件仅凭扩展名信任 | 必须排除 | 1.2 上传与解析炸弹 |
| 禁止无速率限制暴露生成接口 | 必须排除 | 3.1 生成接口被刷爆 |
| 后端日志脱敏 | 必须确认 | 1.1 日志字段限制 |
| x-user-gemini-key 为可选头 | 必须确认 | 1.8 BYOK 安全（新增） |
| CORS 白名单可配置 | 必须确认 | 1.6 CORS 配置不当（新增） |
| 媒体 URL 使用签名或限时访问 | 必须确认 | 1.1 签名 URL 保护 |
| Supabase JWT 必须在后端校验 | 必须确认 | 1.5 多租户与数据泄露 |
| IP 白名单仅用于弱化鉴权 | 必须确认 | 1.4 弱鉴权与 IP 白名单滥用 |
| 上传类与 base64 输入有硬门禁 | 必须确认 | 1.2 上传与解析炸弹 |
| task_id 做格式与长度校验 | 必须确认 | 1.7 task_id 枚举与日志注入（新增） |
| 业务层禁止直接调用外部 API URL | 必须排除 | 2.1 前端直连上游 |
| 前端禁止直连 ai.t8star.cn | 必须排除 | 2.1 前端直连上游 |
| 多层重复拼接 Prompt | 必须排除 | 2.3 Prompt 模板与多层拼接 |
| Video Provider 通过注册表选择 | 必须确认 | 2.5 Video Provider 注册表风险（新增） |
| 统一 API Client（apiClient.ts） | 必须确认 | 2.1 + FROZEN_INVARIANTS |
| 异步任务持久化 | 必须确认 | 2.4 任务状态丢失与不可追踪 |
| Agent 禁止修改 multipart 结构 | 必须排除 | 5.1 Agent 自动重构破坏契约 |
| Agent 禁止批量修改 Prompt 为 JSON | 必须排除 | 5.2 Agent 将 Prompt 强制结构化 |
| Agent 禁止绕过统一响应结构 | 必须排除 | 5.1 + FROZEN_INVARIANTS |

---

### ✅ 证据 2：视频/图像等高成本接口的成本与并发风险有明确防护

| 接口类型 | 风险条目 | 防护策略 |
|---------|---------|---------|
| 视频生成 `/video/generate` | 3.1 生成接口被刷爆 | 按用户/租户限制并发数与速率 |
| 视频生成 | 3.2 重试策略导致重复计费 | 生成类接口默认不重试，视频 0 次 |
| 视频生成 | 2.2 长任务与 Serverless 超时 | 异步返回 task_id，不在 Serverless 内等待 |
| 图像生成 | 3.1 生成接口被刷爆 | 按用户/租户限制并发数与速率 |
| 图像生成 | 3.2 重试策略导致重复计费 | 图像 0 次重试 |
| 九宫格生成 | 3.1 + 4.3 | 并发限制 + 产物形式契约冻结 |
| 跨 Tab 场景 | 2.6 跨 Tab 并发控制失效（新增） | 后端全局并发限制 + 前端互斥锁 |

---

### ✅ 证据 3：体验类风险有兜底方案

| 体验风险 | 风险条目 | 兜底方案 |
|---------|---------|---------|
| 长任务无进度反馈 | 4.1 | 统一 task_id + status 枚举 (queued/running/succeeded/failed)，轮询间隔 ≥ 3s |
| 用户误以为卡死重复提交 | 4.1 | 失败时明确提示，禁止自动重试，由用户手动再试 |
| 输出语言/文案不一致 | 4.2 | 后端默认 output_language=zh-CN，注入 {{Output_Language_Rule}} |
| 界面中英混杂 | 4.2 | 前端仅展示后端返回文本，不在前端重写 prompt |
| 九宫格产物形式不一致 | 4.3 | 契约冻结返回形式（9 张 URL 或单张拼图二选一），契约外返回按 BAD_REQUEST 处理 |

---

### ✅ 证据 4：Agent 相关风险有清晰边界

| Agent 风险 | 风险条目 | 边界定义 |
|-----------|---------|---------|
| 修改目录结构/服务注册 | 5.1 | 明确冻结项（响应结构、Prompt 单一来源、API Client 单入口） |
| 批量修改 Prompt 为 JSON | 5.2 | Prompt 模板输出定义为纯文本，文档中明确禁止 JSON 化 |
| 绕过统一响应结构 | 5.1 | FROZEN_INVARIANTS 冻结 `{ ok, data, error }` |
| 跨模块混改 | 5.3 | 每次变更限定在单个 WP/PLAN 范围内 |
| 文档与实现不同步 | 5.3 | 修改实现时必须同时更新对应文档的验收/风险 |

---

## 反向链接汇总（风险覆盖文档映射）

| 风险分类 | 覆盖的 WP/PLAN/Spec |
|---------|---------------------|
| 1.x 安全类 | WP-GW-02, WP-GW-04, WP-GW-09, WP-GW-10, PRECHECK, FROZEN_INVARIANTS |
| 2.x 稳定性类 | WP-GW-02, WP-GW-03, WP-GW-05, WP-GW-06, WP-GW-07, WP-GW-08, SPEC-ARCH-01 |
| 3.x 成本类 | WP-GW-02, WP-GW-03, WP-GW-07, PRECHECK |
| 4.x 体验类 | WP-GW-03, WP-GW-05, WP-GW-06, WP-GW-06A, WP-GW-07, FROZEN_INVARIANTS |
| 5.x Agent 类 | WP-GW-00, WP-GW-06, PRECHECK, FROZEN_INVARIANTS, AGENT-00_WORKSTREAMS |

---

## 变更记录

| 日期 | 版本 | 变更说明 |
|------|------|----------|
| 2026-01-07 | v1.0 | 初始版本，从 PRECHECK 与 AUDIT_REPORT 汇总 |
| 2026-01-07 | v1.1 | 补充 1.6~1.9、2.5~2.6 风险条目；添加验收证据章节 |

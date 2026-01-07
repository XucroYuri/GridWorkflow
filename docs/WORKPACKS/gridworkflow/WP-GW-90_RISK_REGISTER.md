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
- 对 PRECHECK 与各 WP 的反向链接（注明“本风险已覆盖于哪些文档”）

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

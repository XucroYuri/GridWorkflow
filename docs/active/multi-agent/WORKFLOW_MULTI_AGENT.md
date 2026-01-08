# 多 Agent 工作流推进方案（指挥用作战单）

## 0. 使用方式（给 Agent 下指令）
- 指定角色：`Codex` / `Gemini` / `Joint`。
- 把对应的 **WP 文档**整份发送给该 Agent。
- 要求“只改工作包范围内文件，并按验收 Checklist 交付证据”。
- 若需跨包改动：先更新相关 WP/PLAN 的“依赖/输入输出/验收”，再改实现。

## 1. 阶段与顺序
### 1.1 启动与门禁（串行）
1) `Joint` → `WP-GW-00_GOVERNANCE`（冻结不变量：响应结构 `{ok,data,error}`、Prompt 单一来源、apiClient 单入口、中文 UI、output_language 可控）
2) `Joint` → `WP-GW-90_RISK_REGISTER`（风险条目作为后续验收门禁，交付时需对照给出证据）

### 1.2 骨架可启动（串行内含并行）
3) `Codex` → `WP-GW-01_BOOTSTRAP`（后端 `/health` 先行）
4) `Gemini` → 同一工作包（前端首页 + 启动基线）
连接点：端口、API Base、`.env.example`、README。自此后续包均可本地跑通。

### 1.3 并行主干
**后端（Codex Team）**
- `WP-GW-02_BACKEND_PROXY`
- `WP-GW-03_VIDEO_SORA2`
- `WP-GW-04_STORAGE_COS`
连接点：统一错误结构与脱敏、视频返回 `task_id`、媒体统一 URL 出站（COS）。

**前端（Gemini Team）**
- `WP-GW-05_FRONTEND_SHELL`
- `WP-GW-07_VIDEO_STUDIO_UI`
连接点：先完成 `apiClient.ts` 与 Light Theme 基座；Video Studio 只对接后端接口，不直连上游。

### 1.4 关键串行点（契约先于实现）
5) `Claude` → `WP-GW-06A_FLOW_CONTRACT`（冻结 Step1~Step4 字段/默认值/错误码/状态枚举；九宫格产物形态二选一并冻结：9 个 URL 或单张拼图）
6) 完成后再进入 `WP-GW-06_GRIDWORKFLOW_FLOW`（`Gemini` 状态机 + `Codex` 接口实现，按冻结契约逐步替换 mock，Reroll 只重绘不触发 LLM）

### 1.5 收敛与上线（串行）
7) 鉴权：`Joint` 或 `Codex+Claude+Gemini` → `WP-GW-09_AUTH_SUPABASE`
8) 弱鉴权：`Codex`（Claude 复核安全） → `WP-GW-10_IP_ALLOWLIST`
9) 部署收敛：`Joint` → `WP-GW-08_DEPLOY_VERCEL`
备注：已在最终仓库路径，无需再执行剥离（WP-GW-11_DETACH_REPO 暂停）。

## 2. 验收与门禁执行
- 每个工作包交付时，对照 `WP-GW-90_RISK_REGISTER` 相关风险条目提供证据（成本/并发、脱敏、长任务异步、输出语言一致性等）。
- 违反不变量（响应结构、Prompt 单一来源、apiClient 单入口、中文 UI、output_language 可控）视为直接退回。

## 3. 物料与参考
- 环境占位：`.env.example`（后端端口、`AI_GATEWAY_BASE_URL`/`API_KEY`、前端 `VITE_API_BASE_URL`）。
- 参考代码（只作对照，不直接耦合）：`docs/reference/mother/`
  - `server/routes/ai.ts`、`server/config.ts`
  - `components/Layout/MainLayout.tsx`、`components/Lightbox.tsx`、`components/Toast.tsx`
  - `services/queueService.ts`

## 4. 指挥口径（一句话规则）
“指定角色 + 发送对应 WP 全文 + 限定改动范围 + 要求按验收 Checklist 出证据；跨包先改契约/门禁文档，再动实现。”

## 5. 窗口策略与编号（新建/继承 & 串并行）
- 串行步骤：新开“上下文窗口”编号递增（S1, S2, ...），避免历史上下文干扰；仅在同角色且同工作包的连续细化时复用。
- 并行步骤：为每个并行 Agent 分配独立窗口编号（P1, P2, ...），互不共享上下文；完成后将结果汇总到后续串行窗口。
- 建议编号映射（可直接使用，含 Agent 角色）：
  - S1: Claude（Joint）→ `WP-GW-00_GOVERNANCE`（新建）
  - S2: Claude（Joint）→ `WP-GW-90_RISK_REGISTER`（新建）
  - S3: Codex → `WP-GW-01_BOOTSTRAP` 后端（新建）
  - S4: Gemini → `WP-GW-01_BOOTSTRAP` 前端（新建）
  - P1: Codex → `WP-GW-02_BACKEND_PROXY`（并行）
  - P2: Codex → `WP-GW-03_VIDEO_SORA2`（并行）
  - P3: Codex → `WP-GW-04_STORAGE_COS`（并行）
  - P4: Gemini → `WP-GW-05_FRONTEND_SHELL`（并行）
  - P5: Gemini → `WP-GW-07_VIDEO_STUDIO_UI`（并行）
  - S5: Claude → `WP-GW-06A_FLOW_CONTRACT`（新建，关键契约冻结）
  - S6: Joint（Codex+Gemini，Claude 复核契约）→ `WP-GW-06_GRIDWORKFLOW_FLOW`（继承 S5）
  - S7: Joint（Codex+Gemini+Claude 安全审阅）→ `WP-GW-09_AUTH_SUPABASE`（新建）
  - S8: Codex（Claude 复核安全）→ `WP-GW-10_IP_ALLOWLIST`（新建）
  - S9: Joint（Codex+Gemini，Claude 复核安全）→ `WP-GW-08_DEPLOY_VERCEL`（新建，收敛上线）

## 6. Agent 启动指令（可直接复制）
> 使用方式：在对应窗口发送整段指令；附上对应 WP 文档全文。

```text
【S1 Claude (Joint) / WP-GW-00_GOVERNANCE】
角色：Claude（Joint，治理与门禁）
任务：执行 WP-GW-00_GOVERNANCE，冻结不变量；只改 docs/**；按验收清单出证据。
文档：docs/archive/legacy-workpacks/gridworkflow/WP-GW-00_GOVERNANCE.md
```

```text
【S2 Claude (Joint) / WP-GW-90_RISK_REGISTER】
角色：Claude（Joint，风险兜底）
任务：执行 WP-GW-90_RISK_REGISTER，完善风险条目与兜底策略；按验收清单出证据。
文档：docs/archive/legacy-workpacks/gridworkflow/WP-GW-90_RISK_REGISTER.md
```

```text
【S3 Codex / WP-GW-01_BOOTSTRAP】
角色：Codex（后端）
任务：完成后端骨架与 /health；统一 `{ok,data,error}`；只改 backend/** 与 docs/**；按验收清单出证据。
文档：docs/archive/legacy-workpacks/gridworkflow/WP-GW-01_BOOTSTRAP.md
```

```text
【S4 Gemini / WP-GW-01_BOOTSTRAP】
角色：Gemini Agent（前端）
任务：完成前端首页与启动基线；Light Theme；只改 frontend/** 与 docs/**；按验收清单出证据。
文档：docs/archive/legacy-workpacks/gridworkflow/WP-GW-01_BOOTSTRAP.md
```

```text
【P1 Codex / WP-GW-02_BACKEND_PROXY】
角色：Codex
任务：AI 网关代理（文本/图像）；脱敏与统一错误结构；按验收清单出证据。
文档：docs/archive/legacy-workpacks/gridworkflow/WP-GW-02_BACKEND_PROXY.md
```

```text
【P2 Codex / WP-GW-03_VIDEO_SORA2】
角色：Codex
任务：视频生成与状态查询，返回 task_id，标准错误结构；按验收清单出证据。
文档：docs/archive/legacy-workpacks/gridworkflow/WP-GW-03_VIDEO_SORA2.md
```

```text
【P3 Codex / WP-GW-04_STORAGE_COS】
角色：Codex
任务：媒体统一出站到 COS；签名/脱敏；按验收清单出证据。
文档：docs/archive/legacy-workpacks/gridworkflow/WP-GW-04_STORAGE_COS.md
```

```text
【P4 Gemini / WP-GW-05_FRONTEND_SHELL】
角色：Gemini Agent
任务：前端基座 + apiClient 单入口 + Light Theme；按验收清单出证据。
文档：docs/archive/legacy-workpacks/gridworkflow/WP-GW-05_FRONTEND_SHELL.md
```

```text
【P5 Gemini / WP-GW-07_VIDEO_STUDIO_UI】
角色：Gemini Agent
任务：/video 工作台 UI，任务列表/预览，后端接口对接（不直连上游）；按验收清单出证据。
文档：docs/archive/legacy-workpacks/gridworkflow/WP-GW-07_VIDEO_STUDIO_UI.md
```

```text
【S5 Claude / WP-GW-06A_FLOW_CONTRACT】
角色：Claude（契约负责人）
任务：冻结 Step1~Step4 契约（字段/默认值/错误码/状态枚举；九宫格产物形态二选一并冻结）；按验收清单出证据。
文档：docs/archive/legacy-workpacks/gridworkflow/WP-GW-06A_FLOW_CONTRACT.md
```

```text
【S6 Joint (Codex+Gemini，Claude 复核) / WP-GW-06_GRIDWORKFLOW_FLOW】
角色：Joint 协同（前端状态机 + 后端实现）
任务：按已冻结契约完成四步闭环；前端状态机、后端替换 mock；Reroll 仅重绘；按验收清单出证据。
文档：docs/archive/legacy-workpacks/gridworkflow/WP-GW-06_GRIDWORKFLOW_FLOW.md
```

```text
【S7 Joint (Codex+Gemini，Claude 安全审阅) / WP-GW-09_AUTH_SUPABASE】
角色：联合
任务：Supabase 鉴权与基础数据隔离（JWT/RLS）；按验收清单出证据。
文档：docs/archive/legacy-workpacks/gridworkflow/WP-GW-09_AUTH_SUPABASE.md
```

```text
【S8 Codex（Claude 复核） / WP-GW-10_IP_ALLOWLIST】
角色：Codex（Claude 复核）
任务：IP 白名单弱鉴权（只读接口），生成接口仍需 JWT；按验收清单出证据。
文档：docs/archive/legacy-workpacks/gridworkflow/WP-GW-10_IP_ALLOWLIST.md
```

```text
【S9 Joint (Codex+Gemini，Claude 复核) / WP-GW-08_DEPLOY_VERCEL】
角色：Joint（Codex+Gemini，Claude 复核）
任务：Vercel 部署收敛，异步任务不超时，媒体外置；按验收清单出证据。
文档：docs/archive/legacy-workpacks/gridworkflow/WP-GW-08_DEPLOY_VERCEL.md
```

## 7. GitHub 提交流程（默认习惯）
- 每个 Agent 在对应窗口任务通过验收后，默认执行一次提交与推送，保持可审计历史。
- 推荐分支/提交规范：
  - 分支：`feature/<WP>-<window>`（如 `feature/WP-GW-02-P1`），合并到 `main` 时走 PR。
  - 提交信息：`<window> <WP> <summary>`（如 `P1 WP-GW-02 proxy error handling`）。
- 安全与清单：
  - `.env`、密钥、私有证书严禁入库；先确认 `.gitignore` 覆盖。
  - 提交前附验收要点：成功/失败用例、风险条目对应的证据。
- 仓库初始化与推送（如尚未创建远程）：
  - 本地：`git init`（如未初始化），`git add . && git commit -m "init docs/workflow"`。
  - 远程：创建 GitHub 仓库后 `git remote add origin <repo-url>`，`git push -u origin main`。
  - 完成后为后续窗口保持“验收→提交→推送”的固定节奏。

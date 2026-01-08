# 多 Agent 分步开发组织路线图（并行/串行）

> **状态**: 📋 **规划中**  
> **完成度**: 0%  
> **最后更新**: 2026-01-08  
> **适用范围**: 通用路线图模板

**目标**：把 GridWorkflow 的研发拆成可由 Agent 独立执行的工作包，并明确哪些必须串行（契约/安全/鉴权），哪些可并行（UI 与后端实现分离、页面与服务并行）。

---

## ⚠️ 重要说明

**当前活跃阶段**: Phase 1 (稳定加固) + Phase 2 (生产就绪)

- **v1.0 MVP 阶段工作包**（WP-GW-00 到 WP-GW-11）: 已完成，已归档至 `docs/archive/legacy-workpacks/`，仅作历史参考
- **当前执行任务**: 参见 [WORKFLOW_MULTI_AGENT.md](./WORKFLOW_MULTI_AGENT.md) 和 [MULTI_AGENT_EXECUTION_PLAN.md](./MULTI_AGENT_EXECUTION_PLAN.md)
- **本文档**: 作为通用路线图模板，展示多 Agent 协作的组织方式，当前阶段请参考上述文档

---

## 1. 团队与角色

| 角色 | LLM | 核心特点 | 职责范围 |
|------|-----|----------|----------|
| **Expert (Claude)** | Claude | 🔍 **严谨严厉的代码专家** | 代码审核、方案评审、安全审阅、CI配置、最终验收、架构决策 |
| **Backend (Codex)** | Codex | ⚡ **后端架构专业高效** | 实现 `backend/**`，数据契约、安全、代理、存储、鉴权、任务系统 |
| **Frontend (Gemini)** | Gemini | 🎨 **前端审美且熟练** | 实现 `frontend/**`，Light Theme UI、交互、状态机、apiClient |
| **Joint Agent** | Codex + Gemini | 🔗 联调集成 | 只做联调与验收类变更，禁止引入新需求；修复必须回写到对应 PLAN 的验收条目 |

---

## 2. 串行门禁（必须先完成）

这些工作包一旦未完成，后续并行会产生反复返工：

- **WP-GW-00_GOVERNANCE**：冻结不变量与协作规范、统一响应结构、Agent 分工与上下文注入机制。
- **WP-GW-90_RISK_REGISTER**：高风险场景清单与兜底策略作为后续门禁依据。
- **WP-GW-01_BOOTSTRAP**：前后端骨架与端口、环境变量基线，确保后续工作可启动。

---

## 3. 并行开发主干（推荐并行窗口）

### 并行窗口 A（后端主干：Codex）

- WP-GW-02_BACKEND_PROXY（文本/图像代理，统一错误映射与脱敏）
- WP-GW-03_VIDEO_SORA2（视频生成/状态查询，任务可追踪）
- WP-GW-04_STORAGE_COS（统一媒体出站，URL 规范与签名策略）

### 并行窗口 B（前端主干：Gemini）

- WP-GW-05_FRONTEND_SHELL（UI 基座 + Light Theme 统一风格 + apiClient）
- WP-GW-07_VIDEO_STUDIO_UI（/video 页面：输入/任务列表/预览）

### 并行窗口 C（工作流：Joint 或拆分）

可拆为前端与后端两条线，但契约必须先冻结（WP-GW-06A）：

- WP-GW-06A_FLOW_CONTRACT（四步工作流与视频接口契约冻结）
- WP-GW-06_GRIDWORKFLOW_FLOW（四步状态机：概念图 → 分镜规划 → 九宫格图 → 视频 Prompt）

---

## 4. 依赖关系（关键串行点）

- WP-GW-05_FRONTEND_SHELL 必须先于 WP-GW-06/WP-GW-07（否则 UI 风格与 apiClient 不统一）。
- WP-GW-02_BACKEND_PROXY 必须先于 WP-GW-06（否则工作流文本/图像链路无法联调）。
- WP-GW-03_VIDEO_SORA2 与 WP-GW-04_STORAGE_COS 共同影响 WP-GW-07（任务列表与预览 URL）。
- 鉴权类（WP-GW-09_AUTH_SUPABASE / WP-GW-10_IP_ALLOWLIST）建议在“主干跑通后”串行补齐，避免早期引入复杂度。

---

## 5. 收敛与部署（串行）

- WP-GW-09_AUTH_SUPABASE（后端 JWT 校验 + 前端登录态接入）
- WP-GW-10_IP_ALLOWLIST（弱鉴权边界明确，仅覆盖只读接口）
- WP-GW-08_DEPLOY_VERCEL（Serverless 约束下的异步任务与外部状态验证）
- WP-GW-11_DETACH_REPO（从母体仓库剥离到 `F:\Code\GridWorkflow`）

---

## 6. 每个工作包的 Agent 启动与交付标准

- 每个 WP 都包含：
  - 负责人团队（Claude/Codex/Gemini/Joint）
  - 输入/输出、冻结约束、禁止事项
  - 验收 Checklist（至少 1 成功 + 1 失败路径）
  - 回滚策略
- 每个 Agent 交付后必须更新：
  - 对应 WP 的验收证据与风险点（PDCA 的 Check/Act）

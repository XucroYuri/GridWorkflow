# PLAN-00_BOOTSTRAP (GridWorkflow 项目骨架)

**目标**: 在 `GRIDWORKFLOW_ROOT` 搭建新仓库骨架，形成可运行的前后端最小结构（剥离前暂存于母体仓库内，剥离后迁移为独立根目录）。

## 范围
**包含**:
- `backend/` FastAPI 骨架 + `/health`
- `frontend/` Vite + React + Tailwind 骨架
- 统一 `.env.example` 与 README

**不包含**:
- 任何业务逻辑
- 真实模型调用

## 依赖
- Python 3.10+
- Node 18+

## 交付物
- 目录结构可跑通（前后端各自启动）
- README 中记录启动方式与端口

## 步骤
0.  先完成 `PRECHECK-SEC_ARCH_AGENT.md` 的门禁检查
1. 创建 `backend/` 与 `frontend/`
2. FastAPI 初始化与 `/health`
3. Vite 初始化与根页面
4. `.env.example` 只包含必要键

## Agent 风险点
- 不要把旧仓库的业务代码直接复制过来
- 不要引入不必要的依赖

## 验收
- `GET /health` 返回 200
- 前端可访问首页

## PDCA 钩子
- **Plan**: 明确后端端口、前端端口与基础目录结构，确保 `.env.example` 仅包含必需键。
- **Do**: 按步骤完成骨架搭建，不引入任何业务代码或额外依赖。
- **Check**: 通过 `/health` 接口与首页访问验证；确认目录结构与 PRECHECK 要求一致。
- **Act**: 若发现端口/目录或环境变量混乱，先更新本文档与 `PDCA-00_PROJECT_GOVERNANCE`，再调整实际代码与配置。

## Agent 上下文注入包
- **负责人团队**: Joint（Codex + Gemini 串行）
- **本阶段目标**: 建立前后端最小可运行骨架与环境变量基线，支撑后续并行开发。
- **输入**: 本文档、`PRECHECK-SEC_ARCH_AGENT.md`、`AGENT-00_WORKSTREAMS.md`。
- **输出**: `backend/` FastAPI + `/health`、`frontend/` Vite/React/Tailwind、`.env.example`、README。
- **冻结约束**:
  - `.env.example` 不含任何真实密钥
  - 后端响应结构 `{ ok, data, error }`
  - 前端 UI 文案仅简体中文
- **禁止事项（高风险）**:
  - 将旧项目业务代码直接复制进来
  - 引入与当前阶段无关的大依赖
- **验收 Checklist**:
  - `GET /health` 返回 200
  - 前端可访问首页
  - 启动与路径不依赖母体仓库脚本
- **回滚策略**:
  - 若骨架不稳定，回退到“最小 FastAPI + 最小 Vite”再逐步扩展。

# 多 Agent 工作流推进方案（指挥用作战单）

> **状态**: 🚀 **L0 验证通过，准备启动 Stage 1.1**  
> **完成度**: L0 ✅ (首次本地运行验证完成)  
> **最后更新**: 2026-01-08  
> **适用范围**: Phase 1 (稳定加固) + Phase 2 (生产就绪)

---

## ⚠️ 重要说明

本文档针对**当前活跃阶段**（Phase 1 和 Phase 2）的任务，而非已完成的 v1.0 MVP 阶段。

- **v1.0 已完成工作包**: 已归档至 `docs/archive/legacy-workpacks/`，仅作历史参考
- **当前活跃任务**: Phase 1 (工作流持久化、测试体系、Sentry) + Phase 2 (安全改进)
- **详细执行方案**: 参见 [MULTI_AGENT_EXECUTION_PLAN.md](./MULTI_AGENT_EXECUTION_PLAN.md)

---

## 0. 使用方式（给 Agent 下指令）

### 0.1 Agent 角色说明

| 角色 | LLM | 核心特点 | 适合任务 |
|------|-----|----------|----------|
| `Expert` | **Claude** | 🔍 严谨严厉的代码专家 | 代码审核、方案评审、安全审阅、CI配置、最终验收 |
| `Backend` | **Codex** | ⚡ 后端架构专业高效 | 数据表设计、API实现、后端测试、性能优化 |
| `Frontend` | **Gemini** | 🎨 前端审美且熟练 | 组件开发、Hook实现、UI优化、前端测试 |

### 0.2 指令发送方式

- 指定角色：`Expert (Claude)` / `Backend (Codex)` / `Frontend (Gemini)`
- 把对应的 **PLAN 文档**或 **Stage 详细方案**整份发送给该 Agent
- 要求"只改工作包范围内文件，并按验收 Checklist 交付证据"
- 若需跨包改动：先更新相关 PLAN 的"依赖/输入输出/验收"，再改实现

---

## 1. 详细执行计划与时序分析

### 1.1 总体执行时序图

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                           GridWorkflow 多 Agent 协作执行时序                              │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  Week 1                    Week 2                    Week 3                    Week 4    │
│  ──────                    ──────                    ──────                    ──────    │
│                                                                                          │
│  ┌─────────────────────────────────────────────────┐                                     │
│  │ P0-紧急: SEC-01 CORS 修复 (Codex)               │ ← 【人类开发者】需验证生产环境       │
│  └─────────────────────────────────────────────────┘                                     │
│                                                                                          │
│  ┌───────────────────────────────────────────────────────────────────────┐               │
│  │ Stage 1.1-1.3: 工作流持久化                                           │               │
│  │ ┌───────────┐   ┌───────────────────────┐   ┌────────────────┐        │               │
│  │ │ 1.1 数据表 │ → │ 1.2 API+Hook (并行)   │ → │ 1.3 组件改造   │        │               │
│  │ │ Claude→   │   │ Codex ─┐              │   │ Gemini→Claude  │        │               │
│  │ │ Codex→    │   │        ├→ Claude审核  │   │                │        │               │
│  │ │ Claude    │   │ Gemini─┘              │   │                │        │               │
│  │ └───────────┘   └───────────────────────┘   └────────────────┘        │               │
│  └───────────────────────────────────────────────────────────────────────┘               │
│            ↓                                                                             │
│            │ 【人类开发者】需在 Supabase 中执行 SQL 脚本                                   │
│            │                                                                             │
│            ├─────────────────────────────────────────────────────────────────────────┐   │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │   │
│  │ Stage 2.1: 测试体系 (与 Stage 1.2 并行启动)                                     │ │   │
│  │ ┌─────────────────────────────────────┐   ┌────────────────────────┐            │ │   │
│  │ │ 后端测试 (Codex) + 前端测试 (Gemini)│ → │ CI 配置 (Claude)       │            │ │   │
│  │ │           (并行)                    │   │                        │            │ │   │
│  │ └─────────────────────────────────────┘   └────────────────────────┘            │ │   │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │   │
│                                                                                      │   │
│                        【人类开发者】需配置 GitHub Secrets                            │   │
│                                                                                      │   │
│  ┌───────────────────────────────────────────────────────────────────────────────────┤   │
│  │ Stage 3.1: Sentry 监控                                                            │   │
│  │ ┌─────────────────────────────────────┐   ┌────────────────────────┐              │   │
│  │ │ 后端 Sentry (Codex)                 │   │ 告警规则 (Claude)      │              │   │
│  │ │ 前端 Sentry (Gemini)                │ → │                        │              │   │
│  │ │           (并行)                    │   │                        │              │   │
│  │ └─────────────────────────────────────┘   └────────────────────────┘              │   │
│  └───────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                          │
│                        【人类开发者】需创建 Sentry 项目并获取 DSN                         │
│                                                                                          │
│  ════════════════════════════════ Phase 1 完成线 ════════════════════════════════════    │
│                                                                                          │
│  ┌───────────────────────────────────────────────────────────────────────────────────┐   │
│  │ Phase 2: 安全改进 (Phase 1 完成后启动主体)                                        │   │
│  │                                                                                   │   │
│  │ P0 任务 (Week 1 可提前):                                                          │   │
│  │ ├── SEC-01 CORS (Codex) ← 【紧急，Week 1 并行】                                   │   │
│  │ └── SEC-02 BYOK (Codex)                                                           │   │
│  │                                                                                   │   │
│  │ P1 任务 (串行依赖):                                                               │   │
│  │ ├── SEC-03 Sentry 过滤 (Codex+Gemini) ← 依赖 Stage 3.1                            │   │
│  │ ├── SEC-04 JWT 验证 (Codex)                                                       │   │
│  │ ├── SEC-05 Rate Limiting (Codex)                                                  │   │
│  │ └── SEC-06 日志过滤 (Codex)                                                       │   │
│  │                                                                                   │   │
│  │ P2 任务 (后续迭代):                                                               │   │
│  │ ├── SEC-07 RLS 测试 (Codex)                                                       │   │
│  │ └── SEC-08 依赖安全扫描 (Claude)                                                  │   │
│  └───────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                          │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 并行/串行任务分析

#### 🔀 可并行执行的任务组

| 并行组 | 任务 A | 任务 B | Agent A | Agent B | 条件 |
|--------|--------|--------|---------|---------|------|
| **P1** | Stage 1.2 API 实现 | Stage 1.2 Hook 实现 | Codex | Gemini | Stage 1.1 完成后 |
| **P2** | Stage 2.1 后端测试 | Stage 2.1 前端测试 | Codex | Gemini | 无依赖，可与 Stage 1.2 同时启动 |
| **P3** | Stage 3.1 后端 Sentry | Stage 3.1 前端 Sentry | Codex | Gemini | Stage 2.1 完成后（推荐） |
| **P4** | SEC-01 CORS | Stage 1.1 数据表 | Codex | Codex | **紧急任务可优先并行** |
| **P5** | SEC-04 JWT | SEC-05 Rate Limiting | Codex | Codex | Phase 1 完成后，可并行 |
| **P6** | SEC-06 日志过滤 | SEC-07 RLS 测试 | Codex | Codex | P1 任务完成后 |

#### 🔗 必须串行执行的任务链

| 串行链 | 上游任务 | 下游任务 | 原因 |
|--------|----------|----------|------|
| **S1** | Stage 1.1 数据表 | Stage 1.2 API + Hook | 数据表是 API 和 Hook 的基础 |
| **S2** | Stage 1.2 联调审核 | Stage 1.3 组件改造 | 需确认 API/Hook 契约一致 |
| **S3** | Stage 3.1 Sentry 集成 | SEC-03 敏感信息过滤 | 需先有 Sentry 才能配置过滤 |
| **S4** | SEC-01 CORS | 生产环境部署 | 安全基线必须修复 |
| **S5** | Phase 1 完成 | SEC-02 BYOK | BYOK 依赖基础架构稳定 |

### 1.3 人类参与节点完整规范

> ⚠️ **重要**：本节定义了所有需要人类参与的节点，包括必须等待的阻塞点和反馈收集机制。
> Agent 在遇到这些节点时必须**暂停并等待**人类确认后才能继续。

#### 1.3.1 参与角色定义

| 角色 | 代号 | 职责 | 参与时机 |
|------|------|------|----------|
| **人类开发者** | 👨‍💻 `@Dev` | 执行 Agent 无权限的操作、代码审查、环境配置 | 全程参与 |
| **产品经理** | 📋 `@PM` | 功能验收、用户体验评审、需求确认 | 功能完成后 |
| **测试用户** | 👤 `@User` | 真实使用场景测试、反馈收集 | 集成测试阶段 |

#### 1.3.2 人类介入节点详细清单

##### 🔴 阻塞型节点（Agent 必须等待）

| 节点 | 时机 | 角色 | 操作 | 原因 | 阻塞任务 | 预计耗时 |
|------|------|------|------|------|----------|----------|
| **H1** | Stage 1.1 后 | 👨‍💻 Dev | 在 Supabase Dashboard 执行 SQL DDL | Agent 无 Supabase 管理员权限 | Stage 1.2 | 15-30 min |
| **H2** | Stage 1.3 后 | 👨‍💻 Dev | 验证 RLS 策略（用不同账号测试） | 安全验证需人工确认 | Phase 1 验收 | 30 min |
| **H3** | Stage 2.1 后 | 👨‍💻 Dev | 配置 GitHub Secrets | CI 密钥需人工设置 | CI 运行 | 15 min |
| **H4** | Stage 3.1 前 | 👨‍💻 Dev | 创建 Sentry 项目、获取 DSN | 账号管理需人工操作 | Stage 3.1 | 20 min |
| **H5** | SEC-01 后 | 👨‍💻 Dev | 验证生产环境 CORS 配置生效 | 安全验证需人工确认 | 生产部署 | 15 min |
| **H6** | SEC-02 后 | 👨‍💻 Dev | 生成并安全存储 ENCRYPTION_MASTER_KEY | 密钥管理需人工操作 | BYOK 上线 | 30 min |
| **H7** | 每个任务完成后 | 👨‍💻 Dev | 执行 `git push gitee main` | 代码提交需人工审批 | 下一任务 | 5 min |

##### 🟡 本地运行验证节点（首次运行 + 功能验证）

| 节点 | 时机 | 角色 | 操作 | 目的 | 阻塞任务 | 预计耗时 |
|------|------|------|------|------|----------|----------|
| **L0** | Phase 1 开始前 | 👨‍💻 Dev | **首次本地环境搭建与运行验证** | 确认项目可运行 | Stage 1.1 | 1-2 hours |
| **L1** | Stage 1.1 后 | 👨‍💻 Dev | 本地运行后端，验证数据库连接 | 确认 Supabase 配置正确 | Stage 1.2 | 30 min |
| **L2** | Stage 1.2 后 | 👨‍💻 Dev | 本地运行前后端，验证 API 调通 | 确认前后端联调 | Stage 1.3 | 30 min |
| **L3** | Stage 1.3 后 | 👨‍💻 Dev + 📋 PM | 本地完整功能验证 | 确认持久化功能正常 | Phase 1 验收 | 1 hour |
| **L4** | Stage 3.1 后 | 👨‍💻 Dev | 本地触发错误，验证 Sentry 上报 | 确认监控正常 | Phase 1 验收 | 30 min |
| **L5** | Phase 1 完成后 | 👤 User | 真实用户场景测试 | 收集用户反馈 | Phase 2 规划 | 2-4 hours |

##### 🟢 反馈收集节点（非阻塞但重要）

| 节点 | 时机 | 角色 | 操作 | 目的 | 影响 |
|------|------|------|------|------|------|
| **F1** | Stage 1.3 后 | 📋 PM | UI/UX 评审反馈 | 确认用户体验达标 | 后续迭代优化 |
| **F2** | Phase 1 完成后 | 👤 User | 用户体验反馈收集 | 收集真实使用痛点 | Phase 2 优先级 |
| **F3** | Phase 2 完成后 | 📋 PM + 👤 User | 整体功能评审 | 确认安全改进对用户透明 | 上线决策 |

#### 1.3.3 Agent 等待机制

当 Agent 遇到人类介入节点时，**必须执行以下等待协议**：

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Agent 等待协议 (Wait Protocol)                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. 【输出等待声明】                                                         │
│     ════════════════════════════════════════════════════════════════════   │
│     🔴 【等待人类介入】节点 H1 - Supabase SQL 执行                            │
│                                                                             │
│     ⏳ 当前状态：Stage 1.1 数据表设计已完成                                   │
│     📋 待执行操作：在 Supabase Dashboard 执行以下 SQL DDL                     │
│     📄 SQL 脚本位置：backend/sql/SCHEMA_WORKFLOW_PERSISTENCE.sql             │
│                                                                             │
│     👨‍💻 请【人类开发者】完成以下步骤：                                         │
│     1. 登录 Supabase Dashboard                                               │
│     2. 进入 SQL Editor                                                       │
│     3. 执行 SQL DDL 脚本                                                     │
│     4. 验证表创建成功                                                        │
│                                                                             │
│     ✅ 完成后请回复：                                                        │
│     - "H1 完成" / "H1 done" - 继续下一步                                     │
│     - "H1 问题: <描述>" - 有问题需要处理                                      │
│     ════════════════════════════════════════════════════════════════════   │
│                                                                             │
│  2. 【等待确认】                                                             │
│     - Agent 停止执行，等待人类回复                                           │
│     - 不要自动假设完成并继续                                                 │
│                                                                             │
│  3. 【处理反馈】                                                             │
│     - 收到 "完成" → 继续执行下一步                                           │
│     - 收到 "问题" → 分析问题并提供解决方案                                   │
│     - 收到 "取消" → 记录状态，暂停当前任务线                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 1.3.4 反馈收集模板

##### 本地运行验证反馈模板 (L0-L5)

```markdown
## 本地运行验证反馈 - [节点编号]

### 基本信息
- **验证人**: 
- **验证时间**: 
- **操作系统**: Windows / macOS / Linux
- **Node 版本**: 
- **Python 版本**: 

### 验证结果
- [ ] 后端启动成功
- [ ] 前端启动成功
- [ ] 前后端联调成功
- [ ] 功能测试通过

### 发现的问题
| 问题编号 | 问题描述 | 严重程度 | 建议 |
|----------|----------|----------|------|
| P1 | | 🔴高/🟡中/🟢低 | |

### 截图/日志（如有）
[附加截图或日志片段]

### 下一步建议
- [ ] 可以继续下一阶段
- [ ] 需要修复问题后再继续
```

##### 用户体验反馈模板 (F1-F3)

```markdown
## 用户体验反馈 - [节点编号]

### 反馈人信息
- **角色**: 产品经理 / 测试用户
- **反馈时间**: 

### 功能体验评分 (1-5分)
| 功能 | 易用性 | 响应速度 | 视觉设计 | 综合评分 |
|------|--------|----------|----------|----------|
| 工作流创建 | | | | |
| 状态恢复 | | | | |
| 视频生成 | | | | |

### 正面反馈
1. 
2. 

### 改进建议
| 优先级 | 建议内容 | 影响范围 |
|--------|----------|----------|
| P0 | | |
| P1 | | |

### 其他备注
```

---

## 1.4 本地运行验证计划

> ⚠️ **重要**：项目目前尚未在本地完整运行过，必须在 Phase 1 正式开始前完成首次本地验证。

### 1.4.1 首次本地运行验证 (L0) - **Phase 1 前置条件**

```text
【L0 首次本地运行验证 - 必须在 Stage 1.1 前完成】
═══════════════════════════════════════════════════════════════════════════════

📋 目的：确认项目基础设施可正常运行，建立本地开发环境基线

👨‍💻 执行人：人类开发者

⏱️ 预计耗时：1-2 小时

📝 执行步骤：

1. 环境准备
   ├─ [ ] 安装 Python 3.11+
   ├─ [ ] 安装 Node.js 20+
   ├─ [ ] 安装 pnpm 或 npm
   └─ [ ] 配置 Git 仓库

2. 后端启动验证
   ├─ [ ] cd backend
   ├─ [ ] python -m venv venv
   ├─ [ ] source venv/bin/activate (Windows: venv\Scripts\activate)
   ├─ [ ] pip install -r requirements.txt
   ├─ [ ] 创建 .env 文件（参考 .env.example）
   ├─ [ ] uvicorn app.main:app --reload --port 8000
   ├─ [ ] 访问 http://localhost:8000/health 验证
   └─ [ ] 访问 http://localhost:8000/docs 查看 API 文档

3. 前端启动验证
   ├─ [ ] cd frontend
   ├─ [ ] npm install
   ├─ [ ] 创建 .env.local 文件
   ├─ [ ] npm run dev
   ├─ [ ] 访问 http://localhost:5173 验证
   └─ [ ] 检查控制台无严重错误

4. 前后端联调验证
   ├─ [ ] 确认 CORS 配置允许本地开发
   ├─ [ ] 尝试登录/注册流程
   ├─ [ ] 确认 Supabase Auth 正常
   └─ [ ] 尝试一个 API 调用（如 /health）

5. 记录基线状态
   ├─ [ ] 记录所有依赖版本
   ├─ [ ] 记录环境变量配置
   └─ [ ] 提交 L0 验证报告

🚨 阻塞条件：
   - 如果 L0 验证失败，Stage 1.1 不能开始
   - 必须先解决所有阻塞问题

✅ 完成标志：
   - 前后端都能本地启动
   - 基本功能可访问
   - 验证报告已提交
```

### 1.4.2 阶段性验证时序图

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                              本地运行验证时序 (必须执行)                                   │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  Phase 1 开始前                                                                          │
│  ════════════════                                                                        │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐ │
│  │ 🔴 【L0】首次本地运行验证                                                            │ │
│  │     执行人：👨‍💻 Dev                                                                   │ │
│  │     内容：环境搭建、后端启动、前端启动、基本联调                                      │ │
│  │     阻塞：Stage 1.1 开始                                                             │ │
│  └─────────────────────────────────────────────────────────────────────────────────────┘ │
│                           ↓                                                              │
│  Stage 1.1 后                                                                            │
│  ════════════════                                                                        │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐ │
│  │ 🟡 【L1】数据库连接验证                                                              │ │
│  │     执行人：👨‍💻 Dev                                                                   │ │
│  │     内容：验证 Supabase 表创建成功、RLS 策略生效                                      │ │
│  │     阻塞：Stage 1.2 开始                                                             │ │
│  └─────────────────────────────────────────────────────────────────────────────────────┘ │
│                           ↓                                                              │
│  Stage 1.2 后                                                                            │
│  ════════════════                                                                        │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐ │
│  │ 🟡 【L2】API 联调验证                                                                │ │
│  │     执行人：👨‍💻 Dev                                                                   │ │
│  │     内容：验证 Sessions API 可调用、Hook 可获取数据                                   │ │
│  │     阻塞：Stage 1.3 开始                                                             │ │
│  └─────────────────────────────────────────────────────────────────────────────────────┘ │
│                           ↓                                                              │
│  Stage 1.3 后                                                                            │
│  ════════════════                                                                        │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐ │
│  │ 🟡 【L3】完整功能验证 + UI/UX 评审                                                   │ │
│  │     执行人：👨‍💻 Dev + 📋 PM                                                           │ │
│  │     内容：                                                                           │ │
│  │     - 刷新页面后状态恢复                                                             │ │
│  │     - 新用户创建会话                                                                 │ │
│  │     - 步骤结果正确保存                                                               │ │
│  │     - UI 文案检查（简体中文）                                                        │ │
│  │     - 交互体验评估                                                                   │ │
│  │     阻塞：Phase 1 验收                                                               │ │
│  │                                                                                      │ │
│  │     📋 PM 评审要点：                                                                 │ │
│  │     - [ ] 功能符合需求                                                               │ │
│  │     - [ ] 用户体验流畅                                                               │ │
│  │     - [ ] 错误提示友好                                                               │ │
│  │     - [ ] 加载状态清晰                                                               │ │
│  └─────────────────────────────────────────────────────────────────────────────────────┘ │
│                           ↓                                                              │
│  Stage 3.1 后                                                                            │
│  ════════════════                                                                        │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐ │
│  │ 🟡 【L4】Sentry 监控验证                                                             │ │
│  │     执行人：👨‍💻 Dev                                                                   │ │
│  │     内容：                                                                           │ │
│  │     - 手动触发前端错误，验证 Sentry 收到                                              │ │
│  │     - 手动触发后端错误，验证 Sentry 收到                                              │ │
│  │     - 验证敏感信息已过滤                                                             │ │
│  │     阻塞：Phase 1 最终验收                                                           │ │
│  └─────────────────────────────────────────────────────────────────────────────────────┘ │
│                           ↓                                                              │
│  Phase 1 完成后                                                                          │
│  ════════════════                                                                        │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐ │
│  │ 🟢 【L5】用户场景测试                                                                │ │
│  │     执行人：👤 User (非开发人员)                                                      │ │
│  │     内容：                                                                           │ │
│  │     - 模拟真实用户完整工作流                                                         │ │
│  │     - 收集用户反馈                                                                   │ │
│  │     - 识别易用性问题                                                                 │ │
│  │     影响：Phase 2 优先级调整                                                         │ │
│  │                                                                                      │ │
│  │     👤 用户测试场景：                                                                │ │
│  │     1. 新用户注册并创建第一个工作流                                                  │ │
│  │     2. 中途刷新页面，验证恢复                                                        │ │
│  │     3. 完成完整工作流（概念→分镜→视频）                                              │ │
│  │     4. 查看历史记录                                                                  │ │
│  │     5. 遇到错误时的体验                                                              │ │
│  └─────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                          │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

### 1.4.3 验证检查清单

#### L0 首次运行检查清单

```markdown
## L0 首次本地运行验证检查清单

### 环境信息
- 操作系统: Windows 10 (10.0.26200)
- Python 版本: Python 3.12
- Node 版本: (使用 Vite 7.3.1)
- 验证日期: 2026-01-08

### 后端验证
- [x] `pip install -r requirements.txt` 无错误
- [x] `.env` 文件已正确配置 (使用默认配置)
- [x] `uvicorn app.main:app --reload` 启动成功
- [x] `http://localhost:8000/health` 返回 `{"ok": true, ...}`
- [x] `http://localhost:8000/docs` 可访问 (状态码 200)

### 前端验证
- [x] `npm install` 无错误
- [x] `.env.local` 文件已正确配置 (使用默认代理配置)
- [x] `npm run dev` 启动成功 (Vite v7.3.1, 836ms)
- [x] `http://localhost:5173` 可访问 (状态码 200)
- [x] 控制台无严重错误（红色错误）

### 联调验证
- [x] 前端可连接后端 API (通过 Vite 代理 `/api` → `localhost:8000`)
- [x] CORS 配置正确 (开发环境默认 `*`)
- [ ] Supabase Auth 可用 (需配置 SUPABASE_URL 和 SUPABASE_ANON_KEY)

### 问题记录
| 问题 | 解决方案 | 状态 |
|------|----------|------|
| FastAPI 返回类型错误 | 修复 `ai.py` 中 `JSONResponse \| dict` 联合类型，改用 `response_model=None` | ✅ 已修复 |
| 后端启动失败 | 上述类型注解问题导致，修复后成功启动 | ✅ 已修复 |

### 验证结论
- [x] ✅ 验证通过，可以开始 Stage 1.1
- [ ] ❌ 验证失败，需要解决以下问题：
```

#### L3 完整功能验证检查清单

```markdown
## L3 完整功能验证检查清单

### 验证人员
- 开发者: 
- 产品经理: 
- 验证日期: 

### 功能验证 (👨‍💻 Dev)
- [ ] 刷新页面后状态可恢复
- [ ] 新用户访问时创建新会话
- [ ] 步骤结果正确保存到数据库
- [ ] 视频任务正确关联会话
- [ ] 错误处理显示中文提示
- [ ] 网络断开时有友好提示

### UI/UX 评审 (📋 PM)
- [ ] 界面文案均为简体中文
- [ ] 加载状态清晰可见
- [ ] 步骤导航清晰
- [ ] 错误提示用户友好
- [ ] 视觉设计符合预期
- [ ] 交互流程顺畅

### 性能初步评估
- [ ] 页面加载时间 < 3s
- [ ] API 响应时间 < 2s（非 AI 调用）
- [ ] 无明显卡顿

### 反馈汇总
| 类型 | 反馈内容 | 优先级 | 处理建议 |
|------|----------|--------|----------|
| Bug | | | |
| 改进 | | | |
| 需求 | | | |

### 验证结论
- [ ] ✅ 验证通过，可以进行 Phase 1 验收
- [ ] ⚠️ 有问题但不阻塞，记录到后续迭代
- [ ] ❌ 验证失败，需要修复后重新验证
```

---

## 2. 当前阶段任务总览（快速参考）

### Phase 1: 稳定加固 (P0 - 必须完成)

| 任务 | 工时 | 负责 | 详细方案 |
|------|------|------|----------|
| 1.1 工作流持久化 | 5-7天 | Backend + Frontend | [PHASE_1_IMPLEMENTATION.md](../phase-1/PHASE_1_IMPLEMENTATION.md#11-工作流持久化) |
| 1.2 测试体系基础 | 10-15天 | Backend + Frontend | [PHASE_1_IMPLEMENTATION.md](../phase-1/PHASE_1_IMPLEMENTATION.md#12-测试体系基础) |
| 1.3 Sentry 监控 | 2-3天 | Joint | [PHASE_1_IMPLEMENTATION.md](../phase-1/PHASE_1_IMPLEMENTATION.md#13-sentry-监控) |

### Phase 2: 生产就绪 (P1 - 安全加固)

| 任务 | 优先级 | 负责 | 详细方案 |
|------|--------|------|----------|
| SEC-01 CORS 配置 | P0 | Backend | [SECURITY_IMPROVEMENT_PLAN.md](../phase-2/SECURITY_IMPROVEMENT_PLAN.md#-sec-01-cors-配置过于宽松) |
| SEC-02 BYOK 密钥存储 | P0 | Backend | [SECURITY_IMPROVEMENT_PLAN.md](../phase-2/SECURITY_IMPROVEMENT_PLAN.md#-sec-02-byok-密钥存储安全) |
| SEC-03 Sentry 敏感信息 | P1 | Joint | [SECURITY_IMPROVEMENT_PLAN.md](../phase-2/SECURITY_IMPROVEMENT_PLAN.md#-sec-03-sentry-敏感信息泄露) |
| SEC-04 JWT 验证 | P1 | Backend | [SECURITY_IMPROVEMENT_PLAN.md](../phase-2/SECURITY_IMPROVEMENT_PLAN.md#-sec-04-jwt-验证配置) |
| SEC-05 API 速率限制 | P1 | Backend | [SECURITY_IMPROVEMENT_PLAN.md](../phase-2/SECURITY_IMPROVEMENT_PLAN.md#-sec-05-api-速率限制缺失) |
| SEC-06 日志敏感信息 | P1 | Backend | [SECURITY_IMPROVEMENT_PLAN.md](../phase-2/SECURITY_IMPROVEMENT_PLAN.md#-sec-06-日志敏感信息) |
| SEC-07 RLS 策略验证 | P2 | Backend | [SECURITY_IMPROVEMENT_PLAN.md](../phase-2/SECURITY_IMPROVEMENT_PLAN.md#-sec-07-rls-策略验证) |
| SEC-08 依赖包安全 | P2 | Joint | [SECURITY_IMPROVEMENT_PLAN.md](../phase-2/SECURITY_IMPROVEMENT_PLAN.md#-sec-08-依赖包安全) |

---

## 3. Phase 1 执行顺序与窗口分配

### 2.1 执行时序

```
Week 1-2: 工作流持久化
├── Stage 1.1: Supabase 数据表设计 (Expert审核 → Backend实现 → Expert验收)
├── Stage 1.2: 后端API + 前端Hook (并行: Backend + Frontend)
└── Stage 1.3: 组件改造 (Frontend实现 → Expert审核)

Week 2-3: 测试体系 (与Stage 1.2并行启动)
├── Stage 2.1: 后端测试 + 前端测试 (并行: Backend + Frontend)
└── Stage 2.2: CI配置 (Expert配置 → Expert审核)

Week 3-4: Sentry 监控
├── Stage 3.1: Sentry集成 (并行: Backend + Frontend)
└── Stage 3.2: 告警规则配置 (Expert配置)
```

### 2.2 窗口编号与Agent分配

| 窗口ID | Agent | Stage | 任务 | 状态 |
|--------|-------|-------|------|------|
| #E1 | Expert (Claude) | 1.1-1.3 | 数据表审核、联调审核、最终验收 | 待启动 |
| #B1 | Backend (Codex) | 1.1 | Supabase 数据表实现 | 待启动 |
| #B2 | Backend (Codex) | 1.2 | 后端 API 实现 | 待启动 |
| #F1 | Frontend (Gemini) | 1.2-1.3 | Hook实现、组件改造 | 待启动 |
| #B3 | Backend (Codex) | 2.1 | 后端测试 (pytest) | 待启动 |
| #F2 | Frontend (Gemini) | 2.1 | 前端测试 (vitest) | 待启动 |
| #E2 | Expert (Claude) | 2.2, 3.2 | CI配置、告警规则配置 | 待启动 |
| #B4 | Backend (Codex) | 3.1 | 后端 Sentry 集成 | 待启动 |
| #F3 | Frontend (Gemini) | 3.1 | 前端 Sentry 集成 | 待启动 |

---

## 4. Phase 2 执行顺序（Phase 1 完成后启动）

### 3.1 优先级排序

**P0 优先级（立即执行）**:
1. SEC-01: CORS 配置修复 (Backend)
2. SEC-02: BYOK 密钥存储安全 (Backend，依赖 v1.2-02)

**P1 优先级（Phase 1 完成后）**:
3. SEC-03: Sentry 敏感信息过滤 (Joint，依赖 Phase 1.3)
4. SEC-04: JWT 验证增强 (Backend)
5. SEC-05: API 速率限制 (Backend)
6. SEC-06: 日志敏感信息过滤 (Backend)

**P2 优先级（后续迭代）**:
7. SEC-07: RLS 策略验证 (Backend，依赖 v1.2-01)
8. SEC-08: 依赖包安全扫描 (Joint)

### 3.2 窗口分配建议

| 窗口ID | Agent | 任务 | 状态 |
|--------|-------|------|------|
| #B5 | Backend (Codex) | SEC-01 CORS 修复 | 待启动 |
| #B6 | Backend (Codex) | SEC-02 BYOK 密钥存储 | 待启动 |
| #J1 | Joint (Codex+Gemini) | SEC-03 Sentry 过滤 | 待启动 |
| #B7 | Backend (Codex) | SEC-04 JWT 验证 | 待启动 |
| #B8 | Backend (Codex) | SEC-05 Rate Limiting | 待启动 |
| #B9 | Backend (Codex) | SEC-06 日志过滤 | 待启动 |

---

## 5. Agent 启动指令（Phase 1）

> **使用方式**：在对应 Agent 窗口发送整段指令；附上对应的 PLAN 文档或 Stage 详细方案。
> 
> **Agent 窗口对应关系**：
> - **Claude 窗口** → 发送 `@Expert` 指令
> - **Codex 窗口** → 发送 `@Backend` 指令  
> - **Gemini 窗口** → 发送 `@Frontend` 指令

---

### Stage 1.1: 工作流持久化 - 数据表设计

#### 🔍 Claude (Expert) - #E1 窗口

```text
【#E1 Claude (Expert) / Stage 1.1 数据表审核】
═══════════════════════════════════════════════
Agent：Claude (🔍 严谨严厉的代码专家)
窗口：#E1 Expert
任务：审核工作流持久化数据表设计方案，检查 RLS 策略、索引设计、性能考虑
文档：docs/active/phase-1/PHASE_1_IMPLEMENTATION.md (Section 1.1, Step 1)
输出：审核结论、优化建议、最终确认的 SQL DDL
约束：docs/active/multi-agent/FROZEN_INVARIANTS.md
```

#### ⚡ Codex (Backend) - #B1 窗口

```text
【#B1 Codex (Backend) / Stage 1.1 数据表实现】
═══════════════════════════════════════════════
Agent：Codex (⚡ 后端架构专业高效)
窗口：#B1 Backend
任务：输出完整可执行的 SQL DDL 脚本（workflow_sessions + video_tasks 表 + RLS 策略）
文档：docs/active/phase-1/PHASE_1_IMPLEMENTATION.md (Section 1.1, Step 1)
输出：SQL DDL 脚本、RLS 策略、索引定义
约束：docs/active/multi-agent/FROZEN_INVARIANTS.md
⚠️ 注意：Agent 无 Supabase 执行权限，需由【人类开发者】手动执行 SQL
```

---

### Stage 1.2: 工作流持久化 - API + Hook (🔀 并行执行)

> **并行策略**：Codex 和 Gemini 可同时启动，完成后由 Claude 联调审核

#### ⚡ Codex (Backend) - #B2 窗口 (并行 A)

```text
【#B2 Codex (Backend) / Stage 1.2 后端 API 实现】
═══════════════════════════════════════════════
Agent：Codex (⚡ 后端架构专业高效)
窗口：#B2 Backend
并行：与 #F1 Gemini 并行执行
任务：实现 /api/v1/sessions 和 /api/v1/video/tasks 后端接口
文档：docs/active/phase-1/PHASE_1_IMPLEMENTATION.md (Section 1.1, Step 2)
输出：API 实现代码、Pydantic Schema、curl 测试命令
约束：docs/active/multi-agent/FROZEN_INVARIANTS.md (统一响应格式 {ok, data, error})
```

#### 🎨 Gemini (Frontend) - #F1 窗口 (并行 B)

```text
【#F1 Gemini (Frontend) / Stage 1.2 Hook 实现】
═══════════════════════════════════════════════
Agent：Gemini (🎨 前端审美且熟练)
窗口：#F1 Frontend
并行：与 #B2 Codex 并行执行
任务：实现 useWorkflowPersistence Hook，支持会话保存和恢复
文档：docs/active/phase-1/PHASE_1_IMPLEMENTATION.md (Section 1.1, Step 3)
输出：Hook 实现、TypeScript 类型定义、使用示例
约束：docs/active/multi-agent/FROZEN_INVARIANTS.md (API Client 单入口)
```

---

### Stage 1.3: 工作流持久化 - 组件改造

> **前置条件**：Stage 1.2 联调审核通过

#### 🎨 Gemini (Frontend) - #F1 窗口 (继承)

```text
【#F1 Gemini (Frontend) / Stage 1.3 组件改造】
═══════════════════════════════════════════════
Agent：Gemini (🎨 前端审美且熟练)
窗口：#F1 Frontend (继承自 Stage 1.2)
前置：Stage 1.2 联调审核通过
任务：改造 GridWorkflow 组件，集成 useWorkflowPersistence Hook
文档：docs/active/phase-1/PHASE_1_IMPLEMENTATION.md (Section 1.1, Step 4)
输出：改造后的组件、状态恢复验证、刷新测试截图
约束：docs/active/multi-agent/FROZEN_INVARIANTS.md
```

#### 🔍 Claude (Expert) - #E1 窗口 (继承) - 最终验收

```text
【#E1 Claude (Expert) / Stage 1.1-1.3 工作流持久化最终验收】
═══════════════════════════════════════════════
Agent：Claude (🔍 严谨严厉的代码专家)
窗口：#E1 Expert (继承)
任务：验收工作流持久化全部功能
验收清单：
  □ 刷新页面后状态可恢复
  □ 新用户访问时创建新会话
  □ 步骤结果正确保存到数据库
  □ 视频任务正确关联会话
  □ 错误处理友好（中文提示）
  □ 代码符合冻结项规范
输出：验收结论、问题列表、Stage 2.1 启动许可
```

---

### Stage 2.1: 测试体系 (🔀 可与 Stage 1.2 并行启动)

> **并行策略**：后端测试和前端测试可同时进行；此 Stage 可与 Stage 1.2 并行启动
> **人类开发者介入**：CI 配置完成后需手动配置 GitHub Secrets

#### ⚡ Codex (Backend) - #B3 窗口 (并行 A)

```text
【#B3 Codex (Backend) / Stage 2.1 后端测试】
═══════════════════════════════════════════════
Agent：Codex (⚡ 后端架构专业高效)
窗口：#B3 Backend (新开)
并行：与 #F2 Gemini 并行执行；可与 Stage 1.2 同时启动
任务：配置 pytest，编写 Services 和 API 单元测试，目标覆盖率 > 50%
文档：docs/active/phase-1/PHASE_1_IMPLEMENTATION.md (Section 1.2)
输出：
  - backend/pytest.ini
  - backend/tests/conftest.py
  - backend/tests/test_*.py 测试用例
  - 覆盖率报告
约束：docs/active/multi-agent/FROZEN_INVARIANTS.md
```

#### 🎨 Gemini (Frontend) - #F2 窗口 (并行 B)

```text
【#F2 Gemini (Frontend) / Stage 2.1 前端测试】
═══════════════════════════════════════════════
Agent：Gemini (🎨 前端审美且熟练)
窗口：#F2 Frontend (新开)
并行：与 #B3 Codex 并行执行；可与 Stage 1.2 同时启动
任务：配置 Vitest，编写组件和 Hook 测试，目标覆盖率 > 50%
文档：docs/active/phase-1/PHASE_1_IMPLEMENTATION.md (Section 1.2)
输出：
  - frontend/vitest.config.ts
  - frontend/src/test/setup.ts
  - frontend/src/**/*.test.tsx 测试用例
  - 覆盖率报告
约束：docs/active/multi-agent/FROZEN_INVARIANTS.md
```

#### 🔍 Claude (Expert) - #E2 窗口 - CI 配置

```text
【#E2 Claude (Expert) / Stage 2.2 CI 配置】
═══════════════════════════════════════════════
Agent：Claude (🔍 严谨严厉的代码专家)
窗口：#E2 Expert (新开)
前置：#B3 + #F2 测试用例完成
任务：配置 GitHub Actions CI，集成测试和覆盖率检查
文档：docs/active/phase-1/PHASE_1_IMPLEMENTATION.md (Section 1.2, Step 4)
输出：
  - .github/workflows/test.yml
  - CI 测试通过验证
  - 覆盖率报告配置
约束：docs/active/multi-agent/FROZEN_INVARIANTS.md
⚠️ 注意：需【人类开发者】配置 GitHub Secrets (CODECOV_TOKEN 等)
```

---

### Stage 3.1: Sentry 监控 (🔀 并行执行)

> **并行策略**：后端和前端 Sentry 集成可同时进行
> **人类开发者介入**：需先创建 Sentry 项目并获取 DSN

#### ⚠️ 人类开发者前置操作

```text
【人类开发者 / Stage 3.1 前置】
═══════════════════════════════════════════════
操作：创建 Sentry 项目并获取 DSN
步骤：
  1. 访问 https://sentry.io
  2. 创建后端项目：Python + FastAPI → 获取 SENTRY_DSN_BACKEND
  3. 创建前端项目：JavaScript + React → 获取 VITE_SENTRY_DSN
  4. 将 DSN 配置到环境变量
输出：两个 Sentry DSN 值
```

#### ⚡ Codex (Backend) - #B4 窗口 (并行 A)

```text
【#B4 Codex (Backend) / Stage 3.1 后端 Sentry 集成】
═══════════════════════════════════════════════
Agent：Codex (⚡ 后端架构专业高效)
窗口：#B4 Backend (新开)
并行：与 #F3 Gemini 并行执行
前置：【人类开发者】已提供 SENTRY_DSN
任务：集成 sentry-sdk，配置错误追踪和性能监控
文档：docs/active/phase-1/PHASE_1_IMPLEMENTATION.md (Section 1.3, Step 2)
输出：
  - backend/app/core/sentry.py
  - backend/app/main.py 集成代码
  - 错误上报验证截图
约束：docs/active/multi-agent/FROZEN_INVARIANTS.md (密钥脱敏、错误脱敏)
```

#### 🎨 Gemini (Frontend) - #F3 窗口 (并行 B)

```text
【#F3 Gemini (Frontend) / Stage 3.1 前端 Sentry 集成】
═══════════════════════════════════════════════
Agent：Gemini (🎨 前端审美且熟练)
窗口：#F3 Frontend (新开)
并行：与 #B4 Codex 并行执行
前置：【人类开发者】已提供 VITE_SENTRY_DSN
任务：集成 @sentry/react，配置错误边界和性能监控
文档：docs/active/phase-1/PHASE_1_IMPLEMENTATION.md (Section 1.3, Step 3)
输出：
  - frontend/src/lib/sentry.ts
  - frontend/src/components/ErrorBoundary.tsx
  - 错误上报验证截图
约束：docs/active/multi-agent/FROZEN_INVARIANTS.md (敏感信息过滤)
```

#### 🔍 Claude (Expert) - #E2 窗口 (继承) - 告警配置

```text
【#E2 Claude (Expert) / Stage 3.2 告警规则配置】
═══════════════════════════════════════════════
Agent：Claude (🔍 严谨严厉的代码专家)
窗口：#E2 Expert (继承)
前置：#B4 + #F3 Sentry 集成完成
任务：输出 Sentry Dashboard 告警配置指南
文档：docs/active/phase-1/PHASE_1_IMPLEMENTATION.md (Section 1.3, Step 4)
输出：
  - 告警规则配置文档（含截图指引）
  - 错误告警：新错误通知
  - 性能告警：p95 > 3s 通知
  - 错误激增告警：10分钟 > 10次
⚠️ 注意：实际配置需【人类开发者】在 Sentry Dashboard 操作
```

---

## 6. Agent 启动指令（Phase 2 - 安全改进）

> **执行策略**：
> - **SEC-01 (CORS)** 为 P0 紧急任务，可与 Phase 1 Stage 1.1 并行启动
> - 其他 P0/P1 任务在 Phase 1 完成后依次执行
> - P2 任务根据优先级在后续迭代中安排

---

### P0 优先级任务（紧急）

#### ⚡ Codex (Backend) - #B5 窗口 - SEC-01 CORS（🚨 紧急，Week 1 并行）

```text
【#B5 Codex (Backend) / SEC-01 CORS 修复】
═══════════════════════════════════════════════
Agent：Codex (⚡ 后端架构专业高效)
窗口：#B5 Backend (新开)
优先级：🚨 P0 紧急 - 可与 Stage 1.1 并行启动
任务：修复 CORS 配置，生产环境强制配置，禁止默认 "*"
文档：docs/active/phase-2/SECURITY_IMPROVEMENT_PLAN.md (Section SEC-01)
输出：
  - backend/app/main.py CORS 修复代码
  - 开发环境默认值配置
  - 生产环境强制配置验证逻辑
约束：生产环境必须显式配置 CORS_ALLOW_ORIGINS
⚠️ 注意：需【人类开发者】验证生产环境 CORS 配置生效
```

#### ⚡ Codex (Backend) - #B6 窗口 - SEC-02 BYOK

```text
【#B6 Codex (Backend) / SEC-02 BYOK 密钥存储】
═══════════════════════════════════════════════
Agent：Codex (⚡ 后端架构专业高效)
窗口：#B6 Backend (新开)
优先级：P0
前置：Phase 1 完成、基础架构稳定
任务：实现 BYOK 密钥加密存储，每用户独立 Salt，支持密钥轮换
文档：docs/active/phase-2/SECURITY_IMPROVEMENT_PLAN.md (Section SEC-02)
输出：
  - backend/app/core/encryption.py
  - 独立 ENCRYPTION_MASTER_KEY 配置
  - 密钥轮换功能
  - 审计日志表 SQL
约束：
  - 加密主密钥必须与 JWT Secret 独立
  - 每用户使用独立派生密钥
⚠️ 注意：需【人类开发者】生成并安全存储 ENCRYPTION_MASTER_KEY
```

---

### P1 优先级任务

#### 🔗 Joint (Codex + Gemini) - #J1 窗口 - SEC-03 Sentry 过滤

```text
【#J1 Joint (Codex + Gemini) / SEC-03 Sentry 敏感信息过滤】
═══════════════════════════════════════════════
Agent：Joint (Codex + Gemini 协作)
窗口：#J1 Joint (新开，或分为 #B7 + #F4)
优先级：P1
前置：Stage 3.1 Sentry 集成完成
任务：在 Sentry 集成中添加白名单敏感信息过滤
文档：docs/active/phase-2/SECURITY_IMPROVEMENT_PLAN.md (Section SEC-03)
输出：
  - 后端 (Codex): backend/app/core/sentry.py beforeSend 过滤
  - 前端 (Gemini): frontend/src/lib/sentry.ts beforeSend 过滤
  - 敏感信息验证截图
约束：使用白名单而非黑名单过滤策略
```

#### ⚡ Codex (Backend) - #B7 窗口 - SEC-04 JWT 验证

```text
【#B7 Codex (Backend) / SEC-04 JWT 验证增强】
═══════════════════════════════════════════════
Agent：Codex (⚡ 后端架构专业高效)
窗口：#B7 Backend (新开)
优先级：P1
并行：可与 SEC-05 并行执行
任务：增强 JWT 验证，添加 issuer 验证、audience 验证
文档：docs/active/phase-2/SECURITY_IMPROVEMENT_PLAN.md (Section SEC-04)
输出：
  - backend/app/core/auth.py JWT 验证增强
  - SUPABASE_JWT_AUDIENCE, SUPABASE_JWT_ISSUER 配置
  - 安全测试用例
约束：算法限制为 HS256
```

#### ⚡ Codex (Backend) - #B8 窗口 - SEC-05 Rate Limiting

```text
【#B8 Codex (Backend) / SEC-05 Rate Limiting】
═══════════════════════════════════════════════
Agent：Codex (⚡ 后端架构专业高效)
窗口：#B8 Backend (新开)
优先级：P1
并行：可与 SEC-04 并行执行
任务：实现 API 速率限制，使用 slowapi
文档：docs/active/phase-2/SECURITY_IMPROVEMENT_PLAN.md (Section SEC-05)
输出：
  - backend/app/core/rate_limit.py
  - 各端点限流配置（/concept 10/min, /video/generate 3/min）
  - 限流测试、429 响应格式
约束：符合冻结项 RATE_LIMITED 错误码
```

#### ⚡ Codex (Backend) - #B9 窗口 - SEC-06 日志过滤

```text
【#B9 Codex (Backend) / SEC-06 日志敏感信息过滤】
═══════════════════════════════════════════════
Agent：Codex (⚡ 后端架构专业高效)
窗口：#B9 Backend (新开)
优先级：P1
任务：增强日志过滤，移除敏感信息（API Key、Token、完整 Prompt）
文档：docs/active/phase-2/SECURITY_IMPROVEMENT_PLAN.md (Section SEC-06)
输出：
  - backend/app/core/logger.py SensitiveFilter
  - 敏感字段正则匹配
  - 日志脱敏验证
约束：白名单字段策略
```

---

### P2 优先级任务（后续迭代）

#### ⚡ Codex (Backend) - SEC-07 RLS 测试

```text
【Codex (Backend) / SEC-07 RLS 策略验证】
═══════════════════════════════════════════════
Agent：Codex (⚡ 后端架构专业高效)
优先级：P2（后续迭代）
前置：多租户功能实现 (v1.2-01)
任务：验证 RLS 策略，编写 RLS 测试套件
文档：docs/active/phase-2/SECURITY_IMPROVEMENT_PLAN.md (Section SEC-07)
```

#### 🔍 Claude (Expert) - SEC-08 依赖安全扫描

```text
【Claude (Expert) / SEC-08 依赖包安全扫描】
═══════════════════════════════════════════════
Agent：Claude (🔍 严谨严厉的代码专家)
优先级：P2（后续迭代）
任务：配置 GitHub Actions 安全扫描 CI
文档：docs/active/phase-2/SECURITY_IMPROVEMENT_PLAN.md (Section SEC-08)
输出：
  - .github/workflows/security.yml
  - .github/dependabot.yml
```

---

## 7. 详细执行日程表（含人类验证节点）

### 7.1 Day-by-Day 执行计划

> ⚠️ **注意**：所有 `👨‍💻` 标记的节点需要人类开发者介入，`📋` 标记需要产品经理参与，`👤` 标记需要测试用户参与。
> Agent 必须在这些节点**暂停等待**人类确认后才能继续。

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                          Week 0 (预备周): 首次本地运行验证                                │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  Day 0 (启动前)                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐ │
│  │ 🔴【L0】首次本地运行验证 - 阻塞型，必须完成                                          │ │
│  │                                                                                     │ │
│  │ 👨‍💻 人类开发者执行：                                                                 │ │
│  │ ├─ 后端环境搭建 + 启动验证                                                          │ │
│  │ ├─ 前端环境搭建 + 启动验证                                                          │ │
│  │ ├─ 前后端联调验证                                                                   │ │
│  │ └─ 提交 L0 验证报告                                                                 │ │
│  │                                                                                     │ │
│  │ ⏱️ 预计耗时：1-2 小时                                                               │ │
│  │ ❌ 如果失败：不能开始 Stage 1.1                                                     │ │
│  └─────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                          │
└──────────────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                              Week 1: 基础设施 + 紧急安全修复                              │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  Day 1 (周一) - 前置条件：L0 验证通过                                                    │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐ │
│  │ 🚨 紧急并行启动:                                                                    │ │
│  │ ├─ #B5 Codex: SEC-01 CORS 修复 ──────────────────────────────────────────┐         │ │
│  │ │                                                                         │         │ │
│  │ 📋 主流程串行启动:                                                        │ (并行)  │ │
│  │ └─ #E1 Claude: Stage 1.1 数据表审核 ────────────────────────────────────┘          │ │
│  │                                                                                     │ │
│  │ 🔀 可选并行启动 (无依赖):                                                           │ │
│  │ ├─ #B3 Codex: Stage 2.1 后端测试配置                                               │ │
│  │ └─ #F2 Gemini: Stage 2.1 前端测试配置                                              │ │
│  └─────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                          │
│  Day 2 (周二)                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐ │
│  │ 🔗 串行依赖:                                                                        │ │
│  │ └─ #B1 Codex: Stage 1.1 数据表实现 (依赖 #E1 审核结果)                             │ │
│  │                                                                                     │ │
│  │ 🔴👨‍💻【H1】人类开发者介入 - 阻塞型:                                                  │ │
│  │ └─ 在 Supabase Dashboard 执行 SQL DDL 脚本                                         │ │
│  │ └─ Agent 输出等待声明，暂停执行                                                    │ │
│  │ └─ 等待人类回复 "H1 完成" 后继续                                                   │ │
│  │                                                                                     │ │
│  │ 🟡👨‍💻【L1】本地验证 - 数据库连接:                                                    │ │
│  │ └─ 验证 Supabase 表创建成功、RLS 策略生效                                          │ │
│  │ └─ 提交 L1 验证报告                                                                │ │
│  │                                                                                     │ │
│  │ 🔗 串行依赖:                                                                        │ │
│  │ └─ #E1 Claude: Stage 1.1 数据表验收                                                │ │
│  │                                                                                     │ │
│  │ 🔀 继续并行:                                                                        │ │
│  │ ├─ #B3 Codex: 后端测试用例编写                                                     │ │
│  │ └─ #F2 Gemini: 前端测试用例编写                                                    │ │
│  │                                                                                     │ │
│  │ 🔴👨‍💻【H5】人类开发者介入 - 阻塞型:                                                  │ │
│  │ └─ 验证生产环境 CORS 配置 (SEC-01 完成后)                                          │ │
│  └─────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                          │
│  Day 3-4 (周三-周四)                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐ │
│  │ 🔀 并行组 P1:                                                                       │ │
│  │ ├─ #B2 Codex: Stage 1.2 后端 API 实现 ─────────────────────┐                       │ │
│  │ │                                                          │ → #E1 联调审核        │ │
│  │ └─ #F1 Gemini: Stage 1.2 前端 Hook 实现 ───────────────────┘                       │ │
│  │                                                                                     │ │
│  │ 🔀 继续并行:                                                                        │ │
│  │ ├─ #B3 Codex: 后端测试用例编写                                                     │ │
│  │ └─ #F2 Gemini: 前端测试用例编写                                                    │ │
│  │                                                                                     │ │
│  │ 🟡👨‍💻【L2】本地验证 - API 联调 (Stage 1.2 完成后):                                   │ │
│  │ └─ 本地运行前后端，验证 API 可调用                                                 │ │
│  │ └─ 验证 Hook 可正确获取和保存数据                                                  │ │
│  │ └─ 提交 L2 验证报告                                                                │ │
│  └─────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                          │
│  Day 5 (周五)                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐ │
│  │ 🔗 串行:                                                                            │ │
│  │ ├─ #E1 Claude: Stage 1.2 联调审核                                                  │ │
│  │ ├─ #F1 Gemini: Stage 1.3 组件改造                                                  │ │
│  │ └─ #E1 Claude: Stage 1.3 最终验收                                                  │ │
│  │                                                                                     │ │
│  │ 🟡👨‍💻📋【L3】本地验证 - 完整功能 + UI/UX 评审:                                       │ │
│  │ └─ 👨‍💻 Dev: 刷新页面恢复、新会话创建、数据保存                                      │ │
│  │ └─ 📋 PM: UI 文案检查、交互体验评估                                                │ │
│  │ └─ 提交 L3 验证报告（含 PM 反馈）                                                  │ │
│  │                                                                                     │ │
│  │ 🔴👨‍💻【H2】人类开发者介入 - 阻塞型:                                                  │ │
│  │ └─ 验证 RLS 策略（用不同账号测试）                                                 │ │
│  │                                                                                     │ │
│  │ 🔗 串行:                                                                            │ │
│  │ └─ #E2 Claude: Stage 2.2 CI 配置                                                   │ │
│  │                                                                                     │ │
│  │ 🔴👨‍💻【H3】人类开发者介入 - 阻塞型:                                                  │ │
│  │ └─ 配置 GitHub Secrets (CODECOV_TOKEN 等)                                          │ │
│  └─────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                          │
└──────────────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                                 Week 2: Sentry + Phase 1 收尾                            │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  Day 6 (周一)                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐ │
│  │ 🔴👨‍💻【H4】人类开发者介入 - 阻塞型:                                                  │ │
│  │ └─ 创建 Sentry 项目，获取 DSN                                                       │ │
│  │ └─ 配置环境变量 SENTRY_DSN_BACKEND, VITE_SENTRY_DSN                                │ │
│  │                                                                                     │ │
│  │ 🔀 并行组 P3:                                                                       │ │
│  │ ├─ #B4 Codex: Stage 3.1 后端 Sentry 集成                                           │ │
│  │ └─ #F3 Gemini: Stage 3.1 前端 Sentry 集成                                          │ │
│  └─────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                          │
│  Day 7 (周二)                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐ │
│  │ 🔗 串行:                                                                            │ │
│  │ └─ #E2 Claude: Stage 3.2 告警规则配置指南                                          │ │
│  │                                                                                     │ │
│  │ 🟡👨‍💻【L4】本地验证 - Sentry 监控:                                                   │ │
│  │ └─ 手动触发前端错误，验证 Sentry 收到                                              │ │
│  │ └─ 手动触发后端错误，验证 Sentry 收到                                              │ │
│  │ └─ 验证敏感信息已过滤（无 API Key、Token 等）                                      │ │
│  │ └─ 提交 L4 验证报告                                                                │ │
│  │                                                                                     │ │
│  │ 🔴👨‍💻【人类开发者介入 - Sentry 告警配置】:                                           │ │
│  │ └─ 在 Sentry Dashboard 配置告警规则                                                │ │
│  │ └─ 错误告警：新错误出现时通知                                                      │ │
│  │ └─ 性能告警：p95 > 3s 时通知                                                       │ │
│  │                                                                                     │ │
│  │ ✅ Phase 1 技术验收完成                                                             │ │
│  └─────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                          │
│  Day 8 (周三) - 用户验收                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐ │
│  │ 🟢👤【L5】用户场景测试 - 非阻塞但重要:                                               │ │
│  │                                                                                     │ │
│  │ 👤 测试用户执行（非开发人员）:                                                      │ │
│  │ ├─ 测试场景 1: 新用户注册并创建第一个工作流                                        │ │
│  │ ├─ 测试场景 2: 中途刷新页面，验证状态恢复                                          │ │
│  │ ├─ 测试场景 3: 完成完整工作流（概念→分镜→视频）                                    │ │
│  │ ├─ 测试场景 4: 查看历史记录和已完成的工作流                                        │ │
│  │ └─ 测试场景 5: 遇到网络错误/API 错误时的体验                                       │ │
│  │                                                                                     │ │
│  │ 📋 产品经理收集反馈:                                                               │ │
│  │ ├─ 整理用户反馈汇总                                                                │ │
│  │ ├─ 评估是否需要紧急修复                                                            │ │
│  │ └─ 输出 Phase 2 优先级建议                                                         │ │
│  │                                                                                     │ │
│  │ ✅ Phase 1 完整验收完成（含用户反馈）                                               │ │
│  └─────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                          │
└──────────────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                                 Week 3-4: Phase 2 安全改进                               │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  Day 8-9 (周三-周四)                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐ │
│  │ 🔗 串行:                                                                            │ │
│  │ └─ #J1 Joint: SEC-03 Sentry 敏感信息过滤 (依赖 Stage 3.1)                          │ │
│  │                                                                                     │ │
│  │ 🔀 并行组 P5:                                                                       │ │
│  │ ├─ #B7 Codex: SEC-04 JWT 验证增强                                                  │ │
│  │ └─ #B8 Codex: SEC-05 Rate Limiting                                                 │ │
│  └─────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                          │
│  Day 10-11 (周五-下周一)                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐ │
│  │ 🔗 串行:                                                                            │ │
│  │ └─ #B9 Codex: SEC-06 日志过滤                                                      │ │
│  │                                                                                     │ │
│  │ 🔗 串行:                                                                            │ │
│  │ └─ #B6 Codex: SEC-02 BYOK 密钥存储                                                 │ │
│  │                                                                                     │ │
│  │ 👤 【人类开发者介入点 H6】:                                                         │ │
│  │ └─ 生成并安全存储 ENCRYPTION_MASTER_KEY                                            │ │
│  └─────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                          │
│  Day 12-14 (后续)                                                                        │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐ │
│  │ 📋 P2 优先级 (后续迭代):                                                            │ │
│  │ ├─ SEC-07 RLS 策略验证                                                             │ │
│  │ └─ SEC-08 依赖安全扫描 CI                                                          │ │
│  │                                                                                     │ │
│  │ ✅ Phase 2 验收完成                                                                 │ │
│  └─────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                          │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 窗口占用时间线

| 窗口 | Agent | Day 1 | Day 2 | Day 3-4 | Day 5 | Day 6 | Day 7 | Day 8+ |
|------|-------|-------|-------|---------|-------|-------|-------|--------|
| #E1 | Claude | 1.1审核 | 1.1验收 | - | 1.2审核→1.3验收 | - | - | - |
| #E2 | Claude | - | - | - | 2.2 CI | - | 3.2告警 | - |
| #B1 | Codex | - | 1.1实现 | - | - | - | - | - |
| #B2 | Codex | - | - | 1.2 API | - | - | - | - |
| #B3 | Codex | 2.1测试 | 2.1测试 | 2.1测试 | 2.1测试 | - | - | - |
| #B4 | Codex | - | - | - | - | 3.1 Sentry | - | - |
| #B5 | Codex | SEC-01 | SEC-01 | - | - | - | - | - |
| #B6-9 | Codex | - | - | - | - | - | - | SEC-02~06 |
| #F1 | Gemini | - | - | 1.2 Hook | 1.3组件 | - | - | - |
| #F2 | Gemini | 2.1测试 | 2.1测试 | 2.1测试 | 2.1测试 | - | - | - |
| #F3 | Gemini | - | - | - | - | 3.1 Sentry | - | - |

### 6.3 关键里程碑

| 里程碑 | 预计完成日 | 验收标准 | 负责人 |
|--------|------------|----------|--------|
| **M1** SEC-01 CORS 修复 | Day 2 | 生产环境 CORS 配置验证通过 | Codex → 人类验证 |
| **M2** Stage 1.1 数据表 | Day 2 | SQL DDL 执行成功，RLS 验证通过 | Codex → 人类执行 |
| **M3** Stage 1.2 API+Hook | Day 4 | 联调审核通过，契约一致 | Claude 验收 |
| **M4** Stage 1.3 组件改造 | Day 5 | 刷新页面状态可恢复 | Claude 验收 |
| **M5** Stage 2.1 测试体系 | Day 5 | CI 运行通过，覆盖率 > 50% | Claude 验收 |
| **M6** Stage 3.1 Sentry | Day 7 | 错误可追踪，告警规则生效 | Claude 验收 |
| **M7** Phase 1 完成 | Day 7 | 全部验收清单通过 | Claude 最终验收 |
| **M8** Phase 2 P0/P1 完成 | Day 11 | 安全改进全部实施 | Claude 安全审阅 |

---

## 8. 验收与门禁执行

### 6.1 全局冻结项（必须遵守）

所有 Agent 必须遵守 [FROZEN_INVARIANTS.md](./FROZEN_INVARIANTS.md) 定义的约束：

- ✅ 统一响应结构 `{ok, data, error}`
- ✅ Prompt 单一来源（后端）
- ✅ API Client 单入口（前端）
- ✅ UI 文案仅简体中文
- ✅ 安全门禁（密钥脱敏、外部调用隔离、错误脱敏）
- ✅ 错误码规范
- ✅ 任务状态枚举

**违反冻结项视为直接退回**

### 6.2 验收 Checklist

每个 Stage 完成后，Agent 需要提供：

- [ ] 代码实现符合工作包范围
- [ ] 通过单元测试（如有）
- [ ] 符合全局冻结项
- [ ] 文档已更新（如有需要）
- [ ] 验收要点已满足（见各 PLAN 文档）

---

## 9. Git 提交流程

> **仓库性质**:
> - **Gitee**: 内部开发主仓库，所有日常开发在此进行
> - **GitHub**: 快速部署临时仓库，仅用于 Vercel 等平台部署

- 每个 Agent 在对应窗口任务通过验收后，默认执行一次提交与推送，保持可审计历史
- 推荐分支/提交规范：
  - 分支：`feature/<Stage>-<window>`（如 `feature/stage-1.1-B1`），合并到 `main` 时走 PR
  - 提交信息：`<window> <Stage> <summary>`（如 `#B1 Stage-1.1 implement workflow tables`）
- 安全与清单：
  - `.env`、密钥、私有证书严禁入库；先确认 `.gitignore` 覆盖
  - 提交前附验收要点：成功/失败用例、风险条目对应的证据
- 推送命令：
  - **日常开发**: `git push gitee main`（推送到 Gitee 主仓库）
  - **需要部署时**: `git push github main`（同步到 GitHub 部署仓库）

---

## 10. Agent-Human 协作协议

> 本章节定义 Agent 与人类参与者之间的协作规范，确保信息传递清晰、等待机制有效。

### 10.1 Agent 输出规范（等待人类介入时）

当 Agent 遇到需要人类介入的节点时，必须输出以下格式的等待声明：

```text
════════════════════════════════════════════════════════════════════════════════
🔴 【等待人类介入】节点 [节点编号] - [节点名称]
════════════════════════════════════════════════════════════════════════════════

📋 当前状态：[已完成的工作描述]

👨‍💻/📋/👤 请 [角色] 完成以下操作：

1. [具体操作步骤 1]
2. [具体操作步骤 2]
3. ...

📁 相关文件/资源：
- [文件路径或链接]

⏱️ 预计耗时：[X 分钟/小时]

✅ 完成后请回复以下之一：
- "[节点编号] 完成" → Agent 继续执行下一步
- "[节点编号] 问题: <问题描述>" → Agent 分析问题并提供解决方案
- "[节点编号] 取消" → Agent 暂停当前任务线

❌ 阻塞任务：[下游任务名称]

════════════════════════════════════════════════════════════════════════════════
```

### 10.2 人类回复规范

人类参与者在完成操作后，应回复以下格式之一：

| 回复格式 | 含义 | Agent 行为 |
|----------|------|------------|
| `H1 完成` 或 `H1 done` | 操作成功完成 | 继续执行下一步 |
| `H1 问题: <描述>` | 遇到问题 | 分析问题，提供解决方案 |
| `H1 取消` 或 `H1 cancel` | 取消当前操作 | 暂停任务线，记录状态 |
| `H1 跳过` 或 `H1 skip` | 跳过此步骤 | 记录跳过原因，继续下一步（需谨慎） |

### 10.3 反馈收集流程

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            反馈收集完整流程                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  1. Agent 完成任务                                                              │
│     │                                                                           │
│     ▼                                                                           │
│  2. Agent 输出等待声明 + 验证检查清单                                            │
│     │                                                                           │
│     ▼                                                                           │
│  3. 人类执行验证操作                                                            │
│     ├─ 👨‍💻 Dev: 技术验证（环境、功能、安全）                                    │
│     ├─ 📋 PM: 产品验证（UI/UX、功能完整性）                                     │
│     └─ 👤 User: 用户验证（真实使用场景）                                        │
│     │                                                                           │
│     ▼                                                                           │
│  4. 人类填写验证报告                                                            │
│     ├─ 使用提供的模板                                                           │
│     ├─ 记录发现的问题                                                           │
│     └─ 给出验证结论                                                             │
│     │                                                                           │
│     ▼                                                                           │
│  5. 人类回复 Agent                                                              │
│     ├─ "完成" → 继续                                                            │
│     ├─ "问题" → Agent 处理                                                      │
│     └─ "取消" → 暂停                                                            │
│     │                                                                           │
│     ▼                                                                           │
│  6. Agent 记录反馈并继续/处理问题                                                │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 10.4 异常处理协议

| 异常场景 | Agent 行为 | 人类应对 |
|----------|------------|----------|
| 人类长时间未回复（>24h） | 发送提醒消息 | 尽快回复或说明延迟原因 |
| 人类报告问题 | 分析问题，提供解决方案，等待确认 | 确认方案或提供更多信息 |
| 人类取消操作 | 记录状态，暂停任务线，不影响其他并行任务 | 说明取消原因，决定后续 |
| 验证不通过 | 记录问题，回退到上一步，重新执行 | 明确不通过原因 |

### 10.5 进度同步机制

为保持人类和 Agent 对项目进度的同步，采用以下机制：

#### 每日同步（推荐）

```markdown
## 每日进度同步 - [日期]

### Agent 完成情况
- [x] [任务1]
- [x] [任务2]
- [ ] [任务3] - 等待人类介入 H1

### 等待人类操作
| 节点 | 操作 | 等待时长 | 状态 |
|------|------|----------|------|
| H1 | Supabase SQL 执行 | 2h | 等待中 |

### 今日计划
- Agent: [计划任务]
- 人类: [需要执行的操作]

### 阻塞问题
- [如有阻塞问题列出]
```

#### 阶段总结

```markdown
## Stage X.X 完成报告

### 完成任务
1. [任务列表]

### 人类参与记录
| 节点 | 操作 | 执行人 | 耗时 | 结果 |
|------|------|--------|------|------|
| H1 | SQL 执行 | @Dev | 30min | ✅ |

### 发现的问题
| 问题 | 解决方案 | 状态 |
|------|----------|------|
| | | |

### 下阶段前置条件
- [x] [条件1]
- [ ] [条件2]

### 建议
- [后续建议]
```

---

## 11. 参考文档

### Phase 1 详细方案
- [PHASE_1_IMPLEMENTATION.md](../phase-1/PHASE_1_IMPLEMENTATION.md) - Phase 1 完整实施方案
- [PLAN-v1.1-02_WORKFLOW_PERSISTENCE.md](../../plan/PLAN-v1.1-02_WORKFLOW_PERSISTENCE.md) - 工作流持久化详细计划
- [PLAN-DEBT-01_TESTING.md](../../plan/PLAN-DEBT-01_TESTING.md) - 测试体系建设详细计划
- [PLAN-v1.1-03_SENTRY_MONITORING.md](../../plan/PLAN-v1.1-03_SENTRY_MONITORING.md) - Sentry 监控详细计划

### Phase 2 详细方案
- [SECURITY_IMPROVEMENT_PLAN.md](../phase-2/SECURITY_IMPROVEMENT_PLAN.md) - 安全改进完整方案

### 多 Agent 执行方案
- [MULTI_AGENT_EXECUTION_PLAN.md](./MULTI_AGENT_EXECUTION_PLAN.md) - 详细执行方案和 Agent Prompt
- [FROZEN_INVARIANTS.md](./FROZEN_INVARIANTS.md) - 全局冻结项
- [ROADMAP_MULTI_AGENT.md](./ROADMAP_MULTI_AGENT.md) - 多 Agent 路线图

### 本地开发指南
- [DEBUG_GUIDE.md](../../guides/DEBUG_GUIDE.md) - 调试指导手册（含本地环境配置）

### 主计划
- [MASTER_PLAN_2026.md](../../MASTER_PLAN_2026.md) - 项目主计划

---

## 变更记录

| 日期 | 版本 | 变更说明 |
|------|------|----------|
| 2026-01-08 | v1.0 | 初始版本 |
| 2026-01-08 | v2.0 | 新增人类参与节点详细规范、本地运行验证计划、Agent-Human 协作协议 |

---

**文档维护者**: AI Architect  
**最后更新**: 2026-01-08  
**版本**: v2.0

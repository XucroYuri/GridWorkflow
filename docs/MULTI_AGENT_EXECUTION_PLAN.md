# GridWorkflow 多Agent协作执行方案

> **版本**: 2026-01-08  
> **基于**: [MASTER_PLAN_2026.md](./MASTER_PLAN_2026.md)  
> **目标**: 通过多Agent并行/串行协作，高效推进Phase 1-2任务

---

## 📋 Agent 角色定义

| Agent | 代号 | 特长 | 负责领域 |
|-------|------|------|----------|
| **Claude** | `@Expert` | 代码审查、架构设计、质量把控 | 代码审核、方案评审、疑难问题 |
| **Codex** | `@Backend` | 后端开发、API设计、数据库 | Python/FastAPI、Supabase、测试 |
| **Gemini** | `@Frontend` | 前端开发、UI/UX、交互设计 | React/TypeScript、组件、样式 |

---

## 🗺️ Phase 1 执行路线图

### 整体时序图

```
Week 1-2: 工作流持久化
┌─────────────────────────────────────────────────────────────────────────┐
│ Stage 1.1: Supabase 数据表设计                                           │
│ [Expert 审核] ──▶ [Backend 实现] ──▶ [Expert 验收]                        │
└─────────────────────────────────────────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Stage 1.2: 后端API + 前端Hook (并行)                                     │
│ [Backend: API实现] ─────────────┬─────────────▶ [Expert 联调审核]         │
│ [Frontend: Hook实现] ───────────┘                                        │
└─────────────────────────────────────────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Stage 1.3: 组件改造                                                      │
│ [Frontend 实现] ──▶ [Expert 审核]                                        │
└─────────────────────────────────────────────────────────────────────────┘

Week 2-3: 测试体系 (与Stage 1.2并行启动)
┌─────────────────────────────────────────────────────────────────────────┐
│ Stage 2.1: 后端测试 + 前端测试 (并行)                                    │
│ [Backend: pytest] ────────────┬─────────────▶ [Expert CI配置+审核]       │
│ [Frontend: vitest] ───────────┘                                          │
└─────────────────────────────────────────────────────────────────────────┘

Week 3-4: Sentry 监控
┌─────────────────────────────────────────────────────────────────────────┐
│ Stage 3.1: Sentry 集成 (并行)                                            │
│ [Backend: sentry-sdk] ────────┬─────────────▶ [Expert 告警规则配置]       │
│ [Frontend: @sentry/react] ────┘                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📝 Stage 1.1: Supabase 数据表设计

### 执行信息

| 项目 | 值 |
|------|-----|
| **负责Agent** | `@Expert` (Claude) → `@Backend` (Codex) → `@Expert` (Claude) |
| **上下文策略** | Expert 新开窗口 → Backend 新开窗口 (带入Expert产出) → Expert 继承原窗口 |
| **预估时间** | 0.5 天 |
| **输入依赖** | 无 |
| **输出产出** | SQL DDL脚本、RLS策略 |

### Step 1: Expert 方案审核 (新窗口 #E1)

```markdown
# Agent 启动 Prompt: @Expert #E1 - 数据表设计审核

## 你的角色
你是 Claude，一位严谨的代码架构专家。你的任务是审核并优化 GridWorkflow 项目的 Supabase 数据表设计方案。

## 项目背景
GridWorkflow 是一个 AI 驱动的视频创作工作流平台，需要实现工作流状态持久化功能。
- 技术栈：FastAPI + React + Supabase + Vercel
- 当前问题：刷新页面后工作流进度丢失
- 目标：用户可以恢复中断的工作流

## 你的任务
1. 审核以下数据表设计方案的合理性
2. 检查 RLS（行级安全）策略是否正确
3. 评估是否有潜在的性能问题
4. 输出优化建议和最终确认的 SQL DDL

## 待审核的表设计

### workflow_sessions 表
```sql
CREATE TABLE workflow_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id),
  status TEXT NOT NULL DEFAULT 'draft',
  current_step INTEGER NOT NULL DEFAULT 1,
  input_data JSONB DEFAULT '{}',
  concept_result JSONB,
  storyboard_result JSONB,
  video_prompt_result JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### video_tasks 表
```sql
CREATE TABLE video_tasks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID REFERENCES workflow_sessions(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id),
  task_id TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  progress INTEGER DEFAULT 0,
  result_url TEXT,
  error_message TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### RLS 策略
```sql
ALTER TABLE workflow_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE video_tasks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "用户只能访问自己的会话" ON workflow_sessions
  FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "用户只能访问自己的任务" ON video_tasks
  FOR ALL USING (auth.uid() = user_id);
```

## 输出要求
1. 逐项审核结论（通过/需修改）
2. 具体修改建议（如有）
3. 最终确认的完整 SQL DDL（可直接执行）
4. 给 @Backend Agent 的实现建议

## 重要约束
- status 字段的允许值应该明确定义
- 考虑是否需要 updated_at 的自动更新触发器
- 索引策略建议
```

### Step 2: Backend 数据表实现 (新窗口 #B1)

```markdown
# Agent 启动 Prompt: @Backend #B1 - Supabase 数据表实现

## 你的角色
你是 Codex，一位可靠的后端开发专家。你的任务是在 Supabase 中实现工作流持久化的数据表。

## 项目信息
- 仓库：https://gitee.com/chengdu-flower-food/grid-workflow
- 分支：main
- Supabase 项目需要开发者提供访问凭据

## 来自 @Expert #E1 的审核结果
[此处粘贴 Expert 的审核输出]

## 你的任务
1. 根据 Expert 审核通过的 SQL DDL，在 Supabase 中执行
2. 创建必要的索引
3. 创建 updated_at 自动更新触发器
4. 验证 RLS 策略是否生效
5. 记录实施过程和任何调整

## 输出要求
1. 执行的完整 SQL 脚本（包含所有修改）
2. 执行结果截图或日志
3. 验证测试结果（尝试用不同用户查询）
4. 遇到的问题及解决方案
5. 给 @Expert 的验收检查点清单

## 文件输出
将最终的 SQL 脚本保存到：
`docs/WORKPACKS/gridworkflow/evidence/SCHEMA_WORKFLOW_PERSISTENCE.sql`

## 注意事项
- 如果没有 Supabase 访问权限，请输出完整可执行的 SQL 脚本供开发者执行
- 不要修改任何现有表结构
- 确保所有操作可回滚
```

### Step 3: Expert 验收 (继承窗口 #E1)

```markdown
# Agent 继续 Prompt: @Expert #E1 - 数据表实现验收

## 来自 @Backend #B1 的实现结果
[此处粘贴 Backend 的实现输出]

## 验收任务
1. 检查 SQL 脚本是否与审核方案一致
2. 验证 RLS 策略是否完整
3. 确认索引和触发器是否正确
4. 输出最终验收结论

## 输出
- 验收结论：通过/需返工
- 问题列表（如有）
- Stage 1.2 启动许可
```

---

## 📝 Stage 1.2: 后端 API + 前端 Hook (并行)

### 执行信息

| 项目 | 值 |
|------|-----|
| **负责Agent** | `@Backend` + `@Frontend` 并行，`@Expert` 审核 |
| **上下文策略** | Backend 新开窗口 #B2，Frontend 新开窗口 #F1，Expert 继承 #E1 |
| **预估时间** | 2 天 |
| **输入依赖** | Stage 1.1 完成 |
| **输出产出** | 后端API代码、前端Hook代码 |

### Step 1a: Backend API 实现 (新窗口 #B2，与 #F1 并行)

```markdown
# Agent 启动 Prompt: @Backend #B2 - Sessions API 实现

## 你的角色
你是 Codex，负责实现 GridWorkflow 的工作流会话管理 API。

## 项目上下文
- 仓库：https://gitee.com/chengdu-flower-food/grid-workflow
- 后端框架：FastAPI
- 数据库：Supabase (PostgreSQL)
- 认证：Supabase Auth + JWT

## 来自 Stage 1.1 的产出
数据表已创建：
- workflow_sessions
- video_tasks
RLS 策略已配置。

## 你的任务
实现以下 API 端点：

### 1. POST /api/v1/sessions
创建新的工作流会话
- 需要 JWT 认证
- 请求体：`{ input_data?: object }`
- 返回：`{ ok: true, data: WorkflowSession, error: null }`

### 2. GET /api/v1/sessions/{session_id}
获取会话详情
- 需要 JWT 认证 + 所有权验证
- 返回：`{ ok: true, data: WorkflowSession, error: null }`

### 3. PATCH /api/v1/sessions/{session_id}
更新会话状态
- 需要 JWT 认证 + 所有权验证
- 请求体：`{ status?, current_step?, concept_result?, ... }`
- 返回：`{ ok: true, data: WorkflowSession, error: null }`

### 4. GET /api/v1/sessions/{session_id}/tasks
获取会话的视频任务列表
- 需要 JWT 认证 + 所有权验证
- 返回：`{ ok: true, data: VideoTask[], error: null }`

### 5. POST /api/v1/sessions/{session_id}/tasks
为会话添加视频任务
- 需要 JWT 认证 + 所有权验证
- 请求体：`{ task_id: string }`
- 返回：`{ ok: true, data: VideoTask, error: null }`

## 代码规范
1. 统一响应格式：`{ ok, data, error }`
2. 使用 Pydantic 定义 Schema
3. 使用依赖注入获取当前用户
4. 日志脱敏，不记录敏感数据

## 文件结构
```
backend/app/
├── api/routes/sessions.py      # 新增
├── schemas/sessions.py         # 新增
└── services/session_service.py # 新增
```

## 输出要求
1. 完整的代码实现（可直接运行）
2. 每个端点的测试 curl 命令示例
3. 给 @Frontend 的 API 契约说明（接口文档）
4. 给 @Expert 的代码审查要点

## 重要约束
- 遵循现有代码风格（参考 video.py）
- 错误处理与现有一致
- 不引入新的依赖
```

### Step 1b: Frontend Hook 实现 (新窗口 #F1，与 #B2 并行)

```markdown
# Agent 启动 Prompt: @Frontend #F1 - useWorkflowPersistence Hook 实现

## 你的角色
你是 Gemini，负责实现 GridWorkflow 的前端工作流持久化 Hook。

## 项目上下文
- 仓库：https://gitee.com/chengdu-flower-food/grid-workflow
- 前端框架：React 19 + TypeScript + Vite
- 状态管理：React Context + Hooks
- 样式：Tailwind CSS
- 认证：Supabase Auth

## 来自 Stage 1.1 的产出
数据表结构：
- workflow_sessions (id, user_id, status, current_step, input_data, concept_result, storyboard_result, video_prompt_result)
- video_tasks (id, session_id, user_id, task_id, status, progress, result_url, error_message)

## 你的任务
实现 `useWorkflowPersistence` Hook，提供以下功能：

### Hook API 设计
```typescript
interface UseWorkflowPersistence {
  // 状态
  session: WorkflowSession | null;
  tasks: VideoTask[];
  loading: boolean;
  error: string | null;
  
  // 操作
  updateSession: (updates: Partial<WorkflowSession>) => Promise<void>;
  saveStepResult: (step: number, result: object) => Promise<void>;
  addTask: (taskId: string) => Promise<void>;
  updateTask: (taskId: string, updates: Partial<VideoTask>) => Promise<void>;
  startNewSession: () => Promise<void>;
  refreshTasks: () => Promise<void>;
}
```

### 实现要求
1. 组件挂载时自动恢复或创建会话
2. 使用 localStorage 缓存 session_id
3. 缓存的会话不存在时清理并创建新会话
4. Supabase 查询结果严格校验 (error === null && data !== null)
5. 错误状态友好展示

## 代码规范
1. 使用 TypeScript 严格类型
2. 使用 useCallback 优化函数引用
3. 错误处理使用 try-catch
4. 与现有 AuthContext 集成

## 文件结构
```
frontend/src/
├── hooks/useWorkflowPersistence.ts  # 新增
├── types/workflow.ts                 # 新增
└── services/sessionService.ts        # 新增（可选，封装API调用）
```

## 输出要求
1. 完整的 Hook 代码实现
2. 类型定义文件
3. 使用示例代码
4. 给 @Expert 的代码审查要点
5. 给 @Backend 的 API 调用格式确认

## 重要约束
- 不要直接修改 GridWorkflow.tsx（Stage 1.3 再做）
- 遵循现有代码风格
- 使用 supabase.from() 而非原生 fetch
```

### Step 2: Expert 联调审核 (继承窗口 #E1)

```markdown
# Agent 继续 Prompt: @Expert #E1 - API + Hook 联调审核

## 来自 @Backend #B2 的 API 实现
[此处粘贴 Backend 的代码输出]

## 来自 @Frontend #F1 的 Hook 实现
[此处粘贴 Frontend 的代码输出]

## 审核任务
1. **契约一致性检查**
   - API 响应格式是否与 Hook 期望一致
   - 字段命名是否统一 (snake_case vs camelCase)
   - 错误码是否能被前端正确处理

2. **代码质量检查**
   - 后端：安全性、性能、错误处理
   - 前端：类型安全、内存泄漏、边界情况

3. **集成测试建议**
   - 列出需要测试的关键场景
   - 指出可能的边界问题

## 输出要求
1. 审核结论：通过/需修改
2. 具体问题列表和修改建议（如有）
3. 给 @Backend 和 @Frontend 的修改指令（如需）
4. Stage 1.3 启动许可
```

---

## 📝 Stage 1.3: 组件改造

### 执行信息

| 项目 | 值 |
|------|-----|
| **负责Agent** | `@Frontend` → `@Expert` |
| **上下文策略** | Frontend 继承窗口 #F1，Expert 继承窗口 #E1 |
| **预估时间** | 1 天 |
| **输入依赖** | Stage 1.2 完成 |
| **输出产出** | 改造后的 GridWorkflow.tsx |

### Step 1: Frontend 组件改造 (继承窗口 #F1)

```markdown
# Agent 继续 Prompt: @Frontend #F1 - GridWorkflow 组件改造

## 来自 @Expert #E1 的审核结果
[此处粘贴 Expert 的审核通过确认]

## 你的任务
将 `useWorkflowPersistence` Hook 集成到 `GridWorkflow.tsx` 组件。

## 当前组件分析
`frontend/src/components/video/GridWorkflow.tsx`:
- 使用 useState 管理工作流状态
- 状态在刷新后丢失
- 需要保持现有 UI 和交互不变

## 改造要求
1. **引入持久化 Hook**
   ```tsx
   const {
     session,
     tasks,
     updateSession,
     saveStepResult,
     addTask,
     updateTask,
     startNewSession,
   } = useWorkflowPersistence();
   ```

2. **初始化时恢复状态**
   - 从 session 恢复 currentStep, inputData, results
   - 处理 loading 状态显示

3. **步骤完成时保存**
   - handleGenerateConcept 成功后调用 saveStepResult(1, result)
   - 其他步骤类似

4. **视频生成时记录任务**
   - handleGenerateVideo 成功后调用 addTask(task_id)

5. **任务状态更新**
   - 轮询结果后调用 updateTask(task_id, { status, result_url })

6. **重置功能**
   - handleReset 时调用 startNewSession()

## UI 要求
- 添加 loading 状态的骨架屏
- 添加错误提示 Toast
- 保持现有视觉风格

## 输出要求
1. 完整的改造后的 GridWorkflow.tsx
2. 变更说明（改了哪些地方）
3. 测试场景清单
4. 给 @Expert 的验收检查点
```

### Step 2: Expert 最终验收 (继承窗口 #E1)

```markdown
# Agent 继续 Prompt: @Expert #E1 - 工作流持久化最终验收

## 来自 @Frontend #F1 的组件改造结果
[此处粘贴 Frontend 的代码输出]

## 验收检查清单
1. □ 刷新页面后状态可恢复
2. □ 新用户访问时创建新会话
3. □ 步骤结果正确保存到数据库
4. □ 视频任务正确关联会话
5. □ 错误处理友好
6. □ 代码符合项目规范
7. □ 无性能问题（不必要的重渲染）

## 输出要求
1. 最终验收结论：通过/需返工
2. 问题列表和修改指令（如需返工）
3. Stage 1.2/1.3 的总结报告
4. 给开发者的部署/测试指导
5. 给下一阶段的建议
```

---

## 📝 Stage 2.1: 测试体系建设 (与 Stage 1.2 并行启动)

### 执行信息

| 项目 | 值 |
|------|-----|
| **负责Agent** | `@Backend` + `@Frontend` 并行，`@Expert` 审核 |
| **上下文策略** | Backend 新开窗口 #B3，Frontend 新开窗口 #F2，Expert 新开窗口 #E2 |
| **预估时间** | 5 天 |
| **输入依赖** | 无（可与 Stage 1.2 并行） |
| **输出产出** | pytest 配置+用例、vitest 配置+用例、GitHub Actions CI |

### Step 1a: Backend 测试实现 (新窗口 #B3，与 #F2 并行)

```markdown
# Agent 启动 Prompt: @Backend #B3 - 后端测试体系建设

## 你的角色
你是 Codex，负责为 GridWorkflow 后端建立测试体系。

## 项目上下文
- 仓库：https://gitee.com/chengdu-flower-food/grid-workflow
- 后端框架：FastAPI + Python 3.11
- 测试框架：pytest + pytest-asyncio

## 你的任务

### 1. 测试框架配置
创建 `backend/pytest.ini`:
```ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
addopts = --cov=app --cov-report=term-missing
```

创建 `backend/tests/conftest.py`:
- TestClient fixture
- Mock Supabase fixture
- Mock AI Gateway fixture

### 2. 单元测试 (优先级从高到低)

#### P0: 核心服务测试
- `tests/test_video_service.py` - 视频生成服务
- `tests/test_ai_service.py` - AI 调用服务

#### P1: API 路由测试
- `tests/test_health.py` - 健康检查
- `tests/test_video_routes.py` - 视频 API
- `tests/test_workflow_routes.py` - 工作流 API

#### P2: 工具函数测试
- `tests/test_auth.py` - 认证逻辑
- `tests/test_config.py` - 配置加载

### 3. 测试覆盖率目标
- Services: > 70%
- Routes: > 60%
- 总体: > 50%

## 输出要求
1. 完整的测试配置文件
2. 每个测试模块的代码
3. 运行测试的命令和预期输出
4. 覆盖率报告示例
5. 给 @Expert 的审查要点

## 重要约束
- 测试必须可以在无外部依赖的情况下运行
- 使用 Mock 隔离外部服务
- 测试文件命名遵循 test_*.py
```

### Step 1b: Frontend 测试实现 (新窗口 #F2，与 #B3 并行)

```markdown
# Agent 启动 Prompt: @Frontend #F2 - 前端测试体系建设

## 你的角色
你是 Gemini，负责为 GridWorkflow 前端建立测试体系。

## 项目上下文
- 仓库：https://gitee.com/chengdu-flower-food/grid-workflow
- 前端框架：React 19 + TypeScript + Vite
- 测试框架：Vitest + React Testing Library

## 你的任务

### 1. 测试框架配置
创建 `frontend/vitest.config.ts`:
```typescript
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.ts',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
    },
  },
});
```

创建 `frontend/src/test/setup.ts`:
- @testing-library/jest-dom 扩展
- Mock Supabase
- Mock apiClient

### 2. 组件测试 (优先级从高到低)

#### P0: 核心组件测试
- `GridWorkflow.test.tsx` - 工作流组件
- `VideoEditor.test.tsx` - 视频编辑器

#### P1: 功能组件测试
- `Login.test.tsx` - 登录组件
- `TaskList.test.tsx` - 任务列表

#### P2: Hook 测试
- `useWorkflowPersistence.test.ts` - 持久化 Hook
- `useAuth.test.ts` - 认证 Hook

### 3. 测试覆盖率目标
- 核心组件: > 70%
- Hooks: > 60%
- 总体: > 50%

## 输出要求
1. 完整的测试配置文件
2. 每个测试模块的代码
3. package.json 的测试脚本配置
4. 运行测试的命令和预期输出
5. 给 @Expert 的审查要点

## 重要约束
- 测试必须可以在无网络的情况下运行
- 使用 vi.mock() 隔离外部依赖
- 优先测试用户交互和关键路径
```

### Step 2: Expert CI 配置 + 审核 (新窗口 #E2)

```markdown
# Agent 启动 Prompt: @Expert #E2 - CI 配置 + 测试审核

## 你的角色
你是 Claude，负责配置 GitHub Actions CI 并审核测试质量。

## 来自 @Backend #B3 的后端测试
[此处粘贴 Backend 的测试代码]

## 来自 @Frontend #F2 的前端测试
[此处粘贴 Frontend 的测试代码]

## 你的任务

### 1. 审核测试质量
- 测试是否覆盖关键路径
- Mock 是否合理
- 断言是否充分
- 是否有边界情况遗漏

### 2. 配置 GitHub Actions CI
创建 `.github/workflows/test.yml`:
```yaml
name: Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov httpx
      - name: Run tests
        run: |
          cd backend
          pytest --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v4

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      - name: Run tests
        run: |
          cd frontend
          npm run test:coverage
```

### 3. 配置 Gitee CI (可选)
创建 `.gitee/workflows/test.yml`（如果 Gitee 支持）

## 输出要求
1. 测试质量审核报告
2. 给 @Backend 和 @Frontend 的修改建议（如需）
3. 完整的 CI 配置文件
4. Stage 2.1 完成总结
```

---

## 📝 Stage 3.1: Sentry 监控集成

### 执行信息

| 项目 | 值 |
|------|-----|
| **负责Agent** | `@Backend` + `@Frontend` 并行，`@Expert` 配置告警 |
| **上下文策略** | Backend 新开窗口 #B4，Frontend 新开窗口 #F3，Expert 继承 #E2 |
| **预估时间** | 1.5 天 |
| **输入依赖** | Stage 2.1 完成（推荐）或 Stage 1.3 完成（最低） |
| **输出产出** | Sentry 集成代码、告警规则配置 |

### Step 1a: Backend Sentry 集成 (新窗口 #B4)

```markdown
# Agent 启动 Prompt: @Backend #B4 - 后端 Sentry 集成

## 你的角色
你是 Codex，负责为 GridWorkflow 后端集成 Sentry 错误监控。

## 项目上下文
- 仓库：https://gitee.com/chengdu-flower-food/grid-workflow
- 后端框架：FastAPI
- Sentry SDK：sentry-sdk[fastapi]

## 你的任务

### 1. 安装依赖
```bash
pip install sentry-sdk[fastapi]
```
更新 `requirements.txt`

### 2. 创建 Sentry 配置模块
`backend/app/core/sentry.py`:
```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

def init_sentry():
    dsn = os.getenv("SENTRY_DSN")
    if not dsn:
        return
    
    sentry_sdk.init(
        dsn=dsn,
        environment=os.getenv("APP_ENV", "development"),
        integrations=[FastApiIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=False,
        before_send=filter_sensitive_data,
    )

def filter_sensitive_data(event, hint):
    # 过滤敏感信息
    # API Key, JWT, 用户数据等
    ...
```

### 3. 集成到 main.py
在 app 创建前调用 `init_sentry()`

### 4. 添加环境变量
更新 `.env.example` 和 `config.py`

## 输出要求
1. 完整的代码实现
2. 环境变量配置说明
3. 敏感数据过滤规则
4. 测试 Sentry 的方法（如何触发一个测试错误）
5. 给 @Expert 的告警配置建议
```

### Step 1b: Frontend Sentry 集成 (新窗口 #F3)

```markdown
# Agent 启动 Prompt: @Frontend #F3 - 前端 Sentry 集成

## 你的角色
你是 Gemini，负责为 GridWorkflow 前端集成 Sentry 错误监控。

## 项目上下文
- 仓库：https://gitee.com/chengdu-flower-food/grid-workflow
- 前端框架：React 19 + Vite
- Sentry SDK：@sentry/react

## 你的任务

### 1. 安装依赖
```bash
npm install @sentry/react
```

### 2. 创建 Sentry 配置模块
`frontend/src/lib/sentry.ts`:
```typescript
import * as Sentry from '@sentry/react';

export function initSentry() {
  const dsn = import.meta.env.VITE_SENTRY_DSN;
  if (!dsn) return;

  Sentry.init({
    dsn,
    environment: import.meta.env.MODE,
    integrations: [
      Sentry.browserTracingIntegration(),
      Sentry.replayIntegration(),
    ],
    tracesSampleRate: 0.1,
    replaysSessionSampleRate: 0.1,
    replaysOnErrorSampleRate: 1.0,
    beforeSend: filterSensitiveData,
  });
}

function filterSensitiveData(event) {
  // 过滤敏感信息
  ...
}
```

### 3. 集成到 main.tsx
在 React 渲染前调用 `initSentry()`

### 4. 添加 ErrorBoundary
包裹 App 组件

### 5. 添加环境变量
更新 `.env.example`

## 输出要求
1. 完整的代码实现
2. ErrorBoundary 组件代码
3. 环境变量配置说明
4. 测试 Sentry 的方法
5. 给 @Expert 的告警配置建议
```

### Step 2: Expert 告警配置 (继承窗口 #E2)

```markdown
# Agent 继续 Prompt: @Expert #E2 - Sentry 告警规则配置

## 来自 @Backend #B4 的后端集成
[此处粘贴 Backend 的代码]

## 来自 @Frontend #F3 的前端集成
[此处粘贴 Frontend 的代码]

## 你的任务

### 1. 审核集成代码
- 敏感数据过滤是否完整
- 采样率是否合理
- 环境区分是否正确

### 2. 设计告警规则
```
规则 1: 新错误告警
- 触发条件: 出现新的错误类型
- 通知方式: Email
- 优先级: P1

规则 2: 错误激增告警
- 触发条件: 10分钟内错误数 > 10
- 通知方式: Email + Slack
- 优先级: P0

规则 3: 性能告警
- 触发条件: API p95 延迟 > 5s
- 通知方式: Email
- 优先级: P2
```

### 3. 输出 Sentry 配置指南

## 输出要求
1. 集成代码审核结论
2. 修改建议（如需）
3. 完整的告警规则配置文档
4. Sentry Dashboard 配置步骤
5. Phase 1 完成总结报告
```

---

## 📊 上下文窗口管理总览

### 窗口分配表

| 窗口ID | Agent | 阶段 | 状态 | 继承自 |
|--------|-------|------|------|--------|
| #E1 | Expert (Claude) | Stage 1.1-1.3 | 活跃 | - |
| #B1 | Backend (Codex) | Stage 1.1 | 完成 | - |
| #B2 | Backend (Codex) | Stage 1.2 | 完成 | - |
| #F1 | Frontend (Gemini) | Stage 1.2-1.3 | 活跃 | - |
| #E2 | Expert (Claude) | Stage 2.1, 3.1 | 活跃 | - |
| #B3 | Backend (Codex) | Stage 2.1 | 完成 | - |
| #F2 | Frontend (Gemini) | Stage 2.1 | 完成 | - |
| #B4 | Backend (Codex) | Stage 3.1 | 完成 | - |
| #F3 | Frontend (Gemini) | Stage 3.1 | 完成 | - |

### 信息传递流

```
Stage 1.1:
Expert #E1 ────────▶ Backend #B1 ────────▶ Expert #E1 (验收)
   │                     │
   │  [审核方案]          │  [实现结果]
   ▼                     ▼

Stage 1.2 (并行):
Expert #E1 (许可) ────┬────▶ Backend #B2 ────────┬────▶ Expert #E1 (联调审核)
                      │                          │
                      └────▶ Frontend #F1 ───────┘
                                │
                                │  [API契约同步]
                                ▼

Stage 1.3:
Expert #E1 (许可) ────▶ Frontend #F1 ────▶ Expert #E1 (最终验收)

Stage 2.1 (并行，可与 1.2 同时启动):
                   ┌────▶ Backend #B3 ────────┬────▶ Expert #E2 (CI+审核)
                   │                          │
新窗口 ────────────┼────▶ Frontend #F2 ───────┘
                   │
                   │  [无依赖]

Stage 3.1 (并行):
Expert #E2 (许可) ────┬────▶ Backend #B4 ────────┬────▶ Expert #E2 (告警配置)
                      │                          │
                      └────▶ Frontend #F3 ───────┘
```

---

## 🚀 执行启动顺序

### Day 1
1. **启动 Expert #E1** - Stage 1.1 数据表审核
2. **启动 Backend #B3** - Stage 2.1 后端测试（并行）
3. **启动 Frontend #F2** - Stage 2.1 前端测试（并行）

### Day 2
4. **Backend #B1** - Stage 1.1 数据表实现
5. **Expert #E1 验收** - Stage 1.1 完成

### Day 3-4
6. **Backend #B2 + Frontend #F1 并行** - Stage 1.2 API + Hook
7. **Expert #E1 联调审核**

### Day 5
8. **Frontend #F1 继续** - Stage 1.3 组件改造
9. **Expert #E1 最终验收**
10. **Expert #E2** - Stage 2.1 CI 配置

### Day 6-7
11. **Backend #B4 + Frontend #F3 并行** - Stage 3.1 Sentry
12. **Expert #E2 告警配置** - Phase 1 完成

---

## 📋 检查清单

### Phase 1 完成标准
- [ ] 工作流刷新后可恢复
- [ ] 后端测试覆盖率 > 50%
- [ ] 前端测试覆盖率 > 50%
- [ ] GitHub Actions CI 通过
- [ ] Sentry 可收到错误报告
- [ ] 告警规则已配置

### 交付物清单
- [ ] SQL DDL 脚本
- [ ] 后端 API 代码
- [ ] 前端 Hook 代码
- [ ] 改造后的 GridWorkflow.tsx
- [ ] 后端测试用例
- [ ] 前端测试用例
- [ ] CI 配置文件
- [ ] Sentry 集成代码
- [ ] 告警规则文档

---

**文档维护者**: AI Architect  
**最后更新**: 2026-01-08


-- =============================================================================
-- GridWorkflow 工作流持久化数据表 DDL
-- =============================================================================
-- 文档：Stage 1.1 - Supabase 数据表设计
-- 审核：@Expert #E1 (2026-01-08)
-- 状态：✅ 审核通过
-- 约束：遵守 FROZEN_INVARIANTS.md 全局冻结项
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. 工作流会话表 (workflow_sessions)
-- -----------------------------------------------------------------------------
-- 用途：存储用户的工作流会话状态，支持刷新页面后恢复进度
-- 
-- 状态说明（会话状态，与冻结项的任务状态是不同概念）：
--   - draft: 草稿，用户正在编辑输入
--   - in_progress: 进行中，至少完成了一个步骤
--   - completed: 已完成，所有步骤都已完成
--   - abandoned: 已放弃，用户主动放弃或长期未活动
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS workflow_sessions (
  -- 主键
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- 用户关联（必需）
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  
  -- 会话状态（非冻结项的任务状态，是会话生命周期状态）
  status TEXT NOT NULL DEFAULT 'draft'
    CHECK (status IN ('draft', 'in_progress', 'completed', 'abandoned')),
  
  -- 当前步骤（1-based，对应前端的步骤索引）
  -- 步骤：1=输入, 2=概念, 3=分镜, 4=视频提示词, 5=视频生成
  current_step INTEGER NOT NULL DEFAULT 1
    CHECK (current_step >= 1 AND current_step <= 5),
  
  -- 输入数据（用户的原始输入）
  input_data JSONB DEFAULT '{}',
  
  -- 各步骤的 AI 生成结果
  concept_result JSONB,       -- 步骤2: 概念生成结果
  storyboard_result JSONB,    -- 步骤3: 分镜生成结果
  video_prompt_result JSONB,  -- 步骤4: 视频提示词生成结果
  
  -- 时间戳
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 添加表注释
COMMENT ON TABLE workflow_sessions IS '工作流会话表：存储用户的工作流进度状态，支持页面刷新后恢复';
COMMENT ON COLUMN workflow_sessions.status IS '会话状态: draft(草稿), in_progress(进行中), completed(已完成), abandoned(已放弃)';
COMMENT ON COLUMN workflow_sessions.current_step IS '当前步骤(1-5): 1=输入, 2=概念, 3=分镜, 4=视频提示词, 5=视频生成';

-- -----------------------------------------------------------------------------
-- 2. 视频任务表 (video_tasks)
-- -----------------------------------------------------------------------------
-- 用途：存储视频生成任务的状态和结果
-- 
-- 状态说明（必须符合 FROZEN_INVARIANTS.md 第4节定义的任务状态枚举）：
--   - queued: 排队中
--   - running: 执行中
--   - succeeded: 成功
--   - failed: 失败
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS video_tasks (
  -- 主键
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- 关联会话（级联删除：会话删除时自动删除关联任务）
  session_id UUID REFERENCES workflow_sessions(id) ON DELETE CASCADE,
  
  -- 用户关联（冗余字段，用于 RLS 策略优化和直接查询）
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  
  -- 外部任务 ID（来自视频生成服务的任务标识，如 Sora2 的 task_id）
  -- 用于轮询任务状态和获取结果
  task_id TEXT NOT NULL,
  
  -- 任务状态（必须符合冻结项的任务状态枚举！）
  status TEXT NOT NULL DEFAULT 'queued'
    CHECK (status IN ('queued', 'running', 'succeeded', 'failed')),
  
  -- 任务进度（0-100，仅在 running 状态时更新）
  progress INTEGER DEFAULT 0
    CHECK (progress >= 0 AND progress <= 100),
  
  -- 结果 URL（成功时的视频下载/播放地址）
  result_url TEXT,
  
  -- 错误信息（失败时的脱敏错误描述，遵守冻结项安全门禁）
  error_message TEXT,
  
  -- 时间戳
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 添加表注释
COMMENT ON TABLE video_tasks IS '视频任务表：存储视频生成任务的状态和结果';
COMMENT ON COLUMN video_tasks.task_id IS '外部任务ID：来自视频生成服务(如 Sora2)的任务标识';
COMMENT ON COLUMN video_tasks.status IS '任务状态(冻结项): queued(排队中), running(执行中), succeeded(成功), failed(失败)';
COMMENT ON COLUMN video_tasks.progress IS '任务进度: 0-100，仅在 running 状态时有意义';

-- 添加唯一约束：同一会话中的外部任务 ID 不能重复
CREATE UNIQUE INDEX idx_video_tasks_session_task ON video_tasks(session_id, task_id);

-- -----------------------------------------------------------------------------
-- 3. 索引优化
-- -----------------------------------------------------------------------------
-- 基于预期查询模式创建索引：
-- - 按用户查询会话列表
-- - 按状态过滤会话
-- - 按会话查询任务
-- - 按任务状态过滤

-- workflow_sessions 索引
CREATE INDEX idx_workflow_sessions_user_id ON workflow_sessions(user_id);
CREATE INDEX idx_workflow_sessions_user_status ON workflow_sessions(user_id, status);
CREATE INDEX idx_workflow_sessions_updated_at ON workflow_sessions(updated_at DESC);

-- video_tasks 索引
CREATE INDEX idx_video_tasks_session_id ON video_tasks(session_id);
CREATE INDEX idx_video_tasks_user_id ON video_tasks(user_id);
CREATE INDEX idx_video_tasks_status ON video_tasks(status);
CREATE INDEX idx_video_tasks_task_id ON video_tasks(task_id);

-- -----------------------------------------------------------------------------
-- 4. 自动更新 updated_at 触发器
-- -----------------------------------------------------------------------------

-- 创建通用的 updated_at 更新函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 为 workflow_sessions 添加触发器
DROP TRIGGER IF EXISTS trigger_workflow_sessions_updated_at ON workflow_sessions;
CREATE TRIGGER trigger_workflow_sessions_updated_at
  BEFORE UPDATE ON workflow_sessions
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- 为 video_tasks 添加触发器
DROP TRIGGER IF EXISTS trigger_video_tasks_updated_at ON video_tasks;
CREATE TRIGGER trigger_video_tasks_updated_at
  BEFORE UPDATE ON video_tasks
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- -----------------------------------------------------------------------------
-- 5. 行级安全策略 (RLS)
-- -----------------------------------------------------------------------------
-- 策略原则：
-- - 用户只能访问自己的数据
-- - INSERT 时必须验证 user_id 等于 auth.uid()
-- - 分离 SELECT/INSERT/UPDATE/DELETE 策略，提高可读性和安全性

-- 启用 RLS
ALTER TABLE workflow_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE video_tasks ENABLE ROW LEVEL SECURITY;

-- ===================
-- workflow_sessions RLS 策略
-- ===================

-- SELECT: 用户只能查看自己的会话
CREATE POLICY "workflow_sessions_select_own"
  ON workflow_sessions
  FOR SELECT
  USING (auth.uid() = user_id);

-- INSERT: 用户只能创建属于自己的会话
CREATE POLICY "workflow_sessions_insert_own"
  ON workflow_sessions
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- UPDATE: 用户只能更新自己的会话
CREATE POLICY "workflow_sessions_update_own"
  ON workflow_sessions
  FOR UPDATE
  USING (auth.uid() = user_id);

-- DELETE: 用户只能删除自己的会话
CREATE POLICY "workflow_sessions_delete_own"
  ON workflow_sessions
  FOR DELETE
  USING (auth.uid() = user_id);

-- ===================
-- video_tasks RLS 策略
-- ===================

-- SELECT: 用户只能查看自己的任务
CREATE POLICY "video_tasks_select_own"
  ON video_tasks
  FOR SELECT
  USING (auth.uid() = user_id);

-- INSERT: 用户只能创建属于自己的任务
CREATE POLICY "video_tasks_insert_own"
  ON video_tasks
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- UPDATE: 用户只能更新自己的任务
CREATE POLICY "video_tasks_update_own"
  ON video_tasks
  FOR UPDATE
  USING (auth.uid() = user_id);

-- DELETE: 用户只能删除自己的任务
CREATE POLICY "video_tasks_delete_own"
  ON video_tasks
  FOR DELETE
  USING (auth.uid() = user_id);

-- -----------------------------------------------------------------------------
-- 6. 验证查询（用于人工验证表结构）
-- -----------------------------------------------------------------------------
-- 执行完 DDL 后，可运行以下查询验证：

-- 验证表结构
-- SELECT column_name, data_type, is_nullable, column_default 
-- FROM information_schema.columns 
-- WHERE table_name IN ('workflow_sessions', 'video_tasks')
-- ORDER BY table_name, ordinal_position;

-- 验证索引
-- SELECT indexname, indexdef 
-- FROM pg_indexes 
-- WHERE tablename IN ('workflow_sessions', 'video_tasks');

-- 验证 RLS 策略
-- SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual, with_check
-- FROM pg_policies 
-- WHERE tablename IN ('workflow_sessions', 'video_tasks');

-- -----------------------------------------------------------------------------
-- 版本记录
-- -----------------------------------------------------------------------------
-- v1.0 (2026-01-08): 初始版本
--   - 创建 workflow_sessions 表（会话状态持久化）
--   - 创建 video_tasks 表（视频任务跟踪）
--   - 添加 RLS 策略（行级安全）
--   - 添加索引优化
--   - 添加 updated_at 自动更新触发器
-- =============================================================================


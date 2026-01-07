# PLAN-04_FRONTEND_SHELL (前端基座迁移)

**目标**: 从旧项目中迁移 UI 基座，形成 GridWorkflow 前端框架。

## 范围
**包含**:
- Layout、Lightbox、Toast
- 基础路由与主题
- `apiClient.ts`

**不包含**:
- 旧 ScriptEditor、Timeline、ProjectContext

## 关键实现点
- 所有 API 调用只能走 `apiClient.ts`
- 组件只做展示，不嵌入业务逻辑
- 前端界面与交互文案统一使用简体中文
- 默认提供浅色主题并迁移当前项目 Light Theme 的专业现代视觉风格

## Agent 风险点
- 不要引入旧全局状态
- 不要复制复杂控制器 hooks
- 不要在未明确需求前引入多语言国际化框架并造成文案分叉

## 验收
- 页面骨架可渲染
- Toast/Lightbox 可用
- 浅色主题下视觉风格统一且达到“专业、现代、克制”的标准

## PDCA 钩子
- **Plan**: 冻结前端基座范围（Layout/Lightbox/Toast/路由/主题/apiClient），明确不迁移旧业务。
- **Do**: 迁移 UI 基座与基础路由，所有请求统一走 `apiClient.ts`。
- **Check**: 验证基础页面可用、Toast/Lightbox 正常、API 调用入口唯一且错误处理一致。
- **Act**: 若发现旧业务渗透进来，立即回退相关改动并更新“剔除清单”以防复发。

## Agent 上下文注入包
- **负责人团队**: Gemini (前端)
- **本阶段目标**: 迁移 UI 基座并固化 Light Theme（Google 风格）的视觉与交互基线。
- **输入**: 本文档、`AGENT-00_WORKSTREAMS.md`、当前项目 Light Theme 的视觉参考、后端 API 契约（统一响应结构）。
- **输出**: Layout/主题/基础路由/Toast/Lightbox 与 `apiClient.ts` 的最小可用集。
- **冻结约束**:
  - 所有 API 请求只走 `apiClient.ts`
  - 所有界面文案仅简体中文
  - 不直连外部 AI API
- **禁止事项（高风险）**:
  - 引入复杂全局状态或旧业务逻辑
  - 为了快而在组件内散落 `fetch`
- **验收 Checklist**:
  - 首页与基础路由可访问
  - Toast/Lightbox 可用
  - Light Theme 下视觉风格一致
- **回滚策略**:
  - 任何迁移不稳定时，先回滚到仅保留 Layout + apiClient 的最小骨架版本。

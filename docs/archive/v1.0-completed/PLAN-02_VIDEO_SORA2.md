# PLAN-02_VIDEO_SORA2 (Sora2 视频服务)

**目标**: 接入 `https://ai.t8star.cn/v1` 的 Sora2 视频生成能力，提供生成与查询接口。

## 范围
**包含**:
- `/api/v1/video/generate`
- `/api/v1/video/status/{task_id}` (如可用)
- `provider` 选择器 (t8star 默认)

**不包含**:
- 视频渲染后期处理
- 多供应商生产切换

## 参数对齐
- `model`: `sora-2` / `sora-2-pro`
- `duration`: `10` / `15` / `25` (25 仅 pro)
- `aspect_ratio`: `16:9` / `9:16`
- `images`: 图生视频时必填 (url 或 base64)
- `prompt`: 支持故事板格式 (Shot N)

## 关键实现点
- 接口路径: `/v2/videos/generations`
- 返回 `task_id` 后需异步查询状态
- 任务查询文档待补齐时需保留占位实现

## Agent 风险点
- 不要硬编码模型参数
- 不要默认开启 `hd`
- 不要在日志中记录完整 `task_id` 与上游返回的原始错误体（保留部分前缀即可）
- 不要允许前端自定义 provider URL 或绕过后端 provider 注册表

## 验收
- 触发生成返回 `task_id`
- 日志记录模型、时长、比例

## PDCA 钩子
- **Plan**: 冻结视频生成与查询的契约（model/duration/aspect_ratio/images/prompt/task_id/status）。
- **Do**: 实现 `generate` 与 `status` 两条最短链路，所有长耗时均异步化并可追踪。
- **Check**: 校验 `task_id` 可用、状态枚举一致、失败原因可透出（脱敏）；轮询间隔不小于约束值。
- **Act**: 若供应商接口波动，优先在 provider 封装层适配，禁止在业务层或前端散落供应商细节。

## Agent 上下文注入包
- **负责人团队**: Codex (后端)
- **本阶段目标**: 稳定封装 Sora2 视频生成/查询接口并保障任务可追踪与可控。
- **输入**: 本文档、Sora2 OpenAPI 参考、`PRECHECK-SEC_ARCH_AGENT.md`、`AGENT-00_WORKSTREAMS.md`。
- **输出**: `/video/generate` 与 `/video/status/{task_id}` 后端实现、状态枚举与错误映射说明。
- **冻结约束**:
  - 所有耗时操作异步化，前端只拿 `task_id` 与轮询接口
  - 不透传上游错误体与敏感字段
  - `task_id` 校验与 provider 注册表统一管理
- **禁止事项（高风险）**:
  - 在前端暴露可被枚举的 `task_id` 规律或内部 ID
  - 在后端日志中记录完整 URL/签名参数
- **验收 Checklist**:
  - 正常生成任务返回可查询的 `task_id`
  - 异常任务返回标准化错误结构且无敏感信息
- **回滚策略**:
  - 出现不兼容或严重错误时，可通过配置切回 mock 或禁用视频生成功能。

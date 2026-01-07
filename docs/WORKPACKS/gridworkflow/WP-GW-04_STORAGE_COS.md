# WP-GW-04_STORAGE_COS（媒体统一出站：COS）

**负责人团队**：Codex

**目标**：实现图片/视频统一上传 COS 并返回 URL（可签名），前端不保存大文件。

---

## 输入

- [PLAN-03_STORAGE_COS.md](../../PLAN-03_STORAGE_COS.md)
- [PRECHECK-SEC_ARCH_AGENT.md](../../PRECHECK-SEC_ARCH_AGENT.md)

---

## 输出（交付物）

- `backend/app/storage/cos_client.py`（或等价实现）
- 上传接口或服务方法：image/video → COS URL
- `backend/app/api/routes/media.py`：`/media/upload` 上传接口
- 失败回退策略与签名 URL 策略说明

---

## 冻结约束（必须）

> **全局冻结项**：统一遵守 [FROZEN_INVARIANTS.md](../FROZEN_INVARIANTS.md)

**本工作包特定约束**：
- COS 密钥只在后端使用，禁止出现在前端与日志中
- 返回给前端的 URL 不应包含可长期有效的敏感签名参数
- 媒体 URL 统一走 COS 出站

---

## Agent 启动上下文（复制即用）

```text
你是 Codex Agent（后端负责人）。
只允许修改 backend/** 与 docs/**。
目标：实现 COS 上传与返回 URL（可选签名），并保证密钥与签名参数不泄露。
验收：图片/视频上传各 1 条成功路径；失败路径不泄露敏感信息。
```

---

## 验收 Checklist

- 图片上传返回可访问 URL
- 视频上传返回可访问 URL
- 日志不包含 COS 密钥或签名查询参数

---

## Strategy

- Signed URL：`COS_SIGNED_URL=true` 启用，TTL 使用 `COS_SIGNED_URL_TTL_SECONDS`（60-3600s 夹标）；日志不记录签名查询参数。
- Fallback：COS 未配置或上传失败且提供 `source_url` 时，返回 `fallback=true` 并使用原 URL；否则返回通用错误。

## Evidence

- Success path: `POST /media/upload`（multipart: `media_type=image|video`, `file=@...`）→ `{ ok: true, data: { url, signed, expires_in? } }`
- Failure path: 类型不符或超限 → `{ ok: false, error: { code, message } }`
- Log safety: 仅记录 `request_id` 与概要错误，不包含 COS 密钥或签名参数

## 回滚策略

- 若 COS 集成不稳定：临时返回上游 URL（仅阶段性兜底），并在文档标注风险与时限

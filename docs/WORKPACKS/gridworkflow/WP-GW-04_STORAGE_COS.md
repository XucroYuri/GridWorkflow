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
- 失败回退策略与签名 URL 策略说明

---

## 冻结约束（必须）

- COS 密钥只在后端使用，禁止出现在前端与日志中
- 返回给前端的 URL 不应包含可长期有效的敏感签名参数

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

## 回滚策略

- 若 COS 集成不稳定：临时返回上游 URL（仅阶段性兜底），并在文档标注风险与时限


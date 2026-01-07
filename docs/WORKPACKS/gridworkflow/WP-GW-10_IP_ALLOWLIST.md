# WP-GW-10_IP_ALLOWLIST（企业内网弱鉴权）

**负责人团队**：Codex

**目标**：实现 IP 白名单弱鉴权（仅覆盖非敏感只读接口），生成类接口仍需强鉴权。

---

## 输入

- [PLAN-10_IP_ALLOWLIST.md](../../PLAN-10_IP_ALLOWLIST.md)
- [PRECHECK-SEC_ARCH_AGENT.md](../../PRECHECK-SEC_ARCH_AGENT.md)

---

## 输出（交付物）

- CIDR 白名单解析与可信代理校验
- 弱鉴权策略（只读接口允许，生成接口不允许）

---

## 冻结约束（必须）

> **全局冻结项**：统一遵守 [FROZEN_INVARIANTS.md](../FROZEN_INVARIANTS.md)

**本工作包特定约束**：
- 不将 IP 白名单作为管理员权限
- 生产环境默认关闭，必须显式配置才开启
- 对生成类接口仍要求 JWT 校验
- 弱鉴权仅覆盖只读接口

---

## Agent 启动上下文（复制即用）

```text
你是 Codex Agent（后端负责人）。
目标：实现 IP 白名单弱鉴权，仅覆盖只读接口；生成接口仍需登录。
验收：白名单 IP 可访问只读接口；生成接口在白名单 IP 下仍被拒绝；可信代理校验存在。
```

---

## 配置与开关

- `IP_ALLOWLIST_ENABLED`：是否开启弱鉴权；生产环境默认关闭，需要显式开启。
- `IP_ALLOWLIST`：CIDR/IP 列表（逗号分隔）；默认 `97.64.29.114`。
- `TRUSTED_PROXY_CIDRS`：可信代理 CIDR 列表（逗号分隔）；为空则不信任 `X-Forwarded-For`。

---

## 验收 Checklist

- 白名单 IP 可访问只读接口
- 生成接口仍需登录
- 可信代理校验存在，避免滥用 X-Forwarded-For

---

## 验收证据

- 见 `docs/WORKPACKS/gridworkflow/EVIDENCE_WP-GW-10_IP_ALLOWLIST.md`。

---

## 回滚策略

- 若出现误放行：立即关闭弱鉴权开关并回退到纯 JWT 鉴权

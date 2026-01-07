# WP-GW-10 验收证据记录

**工作包**：WP-GW-10_IP_ALLOWLIST（企业内网弱鉴权）

**负责人**：Codex（后端，Claude 复核）

**冻结日期**：2026-01-07

**冻结版本**：v1.0

---

## 验收清单完成状态

### 1) 白名单 IP 可访问只读接口

**证据**

- 仅只读接口放行：`backend/app/api/routes/video.py`
- 白名单判断与开关：`backend/app/core/auth.py`
- 配置项定义：`backend/app/core/config.py` (第75-87行)

**代码要点**

```python
# backend/app/api/routes/video.py
@router.get("/status/{task_id}", dependencies=[Depends(require_user_or_allowlisted)])
async def video_status(...):
    ...
```

```python
# backend/app/core/auth.py
if _allowlist_enabled(settings) and _is_request_allowlisted(request, settings):
    return None
```

**环境变量配置**

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `IP_ALLOWLIST_ENABLED` | `false` | 是否开启弱鉴权；生产环境需显式开启 |
| `IP_ALLOWLIST` | `97.64.29.114` | CIDR/IP 列表，逗号分隔 |
| `TRUSTED_PROXY_CIDRS` | 空 | 可信代理 CIDR 列表；留空则不信任 X-Forwarded-For |

**可复现（示例）**

1. `.env` 启用白名单并设置本机地址：
   - `IP_ALLOWLIST_ENABLED=true`
   - `IP_ALLOWLIST=127.0.0.1/32`
2. 访问只读接口，不携带 `Authorization` 仍可通过鉴权门禁：

```bash
curl -X GET "http://localhost:8000/api/v1/video/status/<task_id>?provider=t8star" \
  -H "x-user-gemini-key: <your-key>"
```

期望结果：未提供 JWT 但通过弱鉴权进入业务逻辑（仍需上游 key 才能查询状态）。

---

### 2) 生成接口仍需登录

**证据**

- 生成接口强制 JWT：`backend/app/api/routes/video.py`
- 其他核心路由仍保留 `require_user`：`backend/app/api/routes/ai.py`、`backend/app/api/routes/workflow.py`、`backend/app/api/routes/media.py`

**代码要点**

```python
# backend/app/api/routes/video.py
@router.post("/generate", dependencies=[Depends(require_user)])
async def generate_video(...):
    ...
```

无 JWT 调用生成接口将触发 `AuthError` 并返回 `401 UNAUTHORIZED`。

---

### 3) 可信代理校验存在，避免滥用 X-Forwarded-For

**证据**

- 仅信任可信代理注入的 `X-Forwarded-For`：`backend/app/core/auth.py`
- 可信代理 CIDR 配置：`backend/app/core/config.py` (第85-87行 `trusted_proxy_cidrs`)

**代码要点**

```python
# backend/app/core/auth.py
trusted_proxies = _parse_networks(settings.trusted_proxy_cidrs)
if trusted_proxies and _ip_in_networks(client_ip, trusted_proxies):
    forwarded_for = request.headers.get("x-forwarded-for")
    ...
```

当请求来源不在 `TRUSTED_PROXY_CIDRS` 中时，`X-Forwarded-For` 会被忽略，避免绕过。

---

## 回滚策略

- 发现误放行：将 `IP_ALLOWLIST_ENABLED=false` 并恢复到纯 JWT 鉴权。

---

## Claude 复核记录

**复核日期**：2026-01-07

**复核结果**：✅ 通过

**验收清单核验**：

| 验收项 | 状态 | 代码位置 |
|--------|------|----------|
| 白名单 IP 可访问只读接口 | ✅ | `video.py:125` `require_user_or_allowlisted` |
| 生成接口仍需登录 | ✅ | `video.py:35` `require_user` |
| 可信代理校验存在 | ✅ | `auth.py:68-82` `_get_client_ip` |
| 生产环境默认关闭 | ✅ | `auth.py:60-65` `_allowlist_enabled` |

**代码质量评估**：

- `auth.py`：使用 `@lru_cache` 优化 CIDR 解析，正确处理 IPv4/IPv6
- `config.py`：配置项清晰，`ip_allowlist_configured` 确保生产环境显式配置
- 路由隔离正确：仅 `GET /api/v1/video/status/{task_id}` 启用弱鉴权

**修正项**：

- 证据文档中 `.env.example` 引用已修正为 `config.py` 配置项定义
- 补充了环境变量配置表格说明

**复核人**：Claude

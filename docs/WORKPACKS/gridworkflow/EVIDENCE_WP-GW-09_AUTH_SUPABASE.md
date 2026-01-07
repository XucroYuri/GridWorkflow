# WP-GW-09 验收证据记录

**工作包**：WP-GW-09_AUTH_SUPABASE（认证与云端数据：Supabase）

**负责人**：Codex（后端）+ Gemini（前端）+ Claude（安全审阅）

**冻结日期**：2026-01-07

**冻结版本**：v1.0

---

## 验收清单完成状态

### 1) 登录流程可用，前端拿到 JWT

**证据**

- Supabase 客户端初始化：`frontend/src/lib/supabase.ts`
- 登录组件触发 OTP 登录：`frontend/src/components/Auth/Login.tsx`
- AuthContext 订阅 session 并缓存：`frontend/src/contexts/AuthContext.tsx`
- API 请求自动注入 JWT：`frontend/src/services/apiClient.ts`

**说明**

前端使用 `SUPABASE_ANON_KEY` 与 `SUPABASE_URL` 建立客户端，登录后可从 `session.access_token` 获取 JWT，并在 API 请求中设置 `Authorization: Bearer <token>`。

---

### 2) 后端可校验 JWT 并提取 user_id

**证据**

- JWT 校验逻辑与 user_id 提取：`backend/app/core/auth.py`
- 鉴权失败统一返回 `UNAUTHORIZED`：`backend/app/main.py`
- 核心路由强制鉴权：`backend/app/api/routes/ai.py`、`backend/app/api/routes/workflow.py`、`backend/app/api/routes/video.py`、`backend/app/api/routes/media.py`

**代码要点**

```python
# backend/app/core/auth.py
token = _extract_bearer_token(authorization)
claims = _decode_supabase_jwt(token, settings)
user_id = claims.get("sub") or claims.get("user_id")
request.state.user_id = user_id
```

后端通过 `SUPABASE_JWT_SECRET` 校验 Supabase JWT，解析 `sub` 作为 `user_id` 存入 `request.state`。

---

### 3) 未登录访问核心接口被拒绝

**证据**

```python
# backend/app/core/auth.py
if not token:
    raise AuthError("未登录或鉴权失败。")
```

```python
# backend/app/main.py
@app.exception_handler(AuthError)
async def auth_exception_handler(_: Request, exc: AuthError):
    return JSONResponse(
        status_code=401,
        content=error_response("UNAUTHORIZED", exc.message),
    )
```

缺少或无效 JWT 时触发 `AuthError`，统一返回 `401` + `UNAUTHORIZED`。

---

### 4) 数据表按用户隔离，RLS 生效

**证据（最小任务/媒体索引表 + RLS 草案）**

```sql
create table public.tasks (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id),
  task_id text not null,
  status text not null,
  provider text not null,
  created_at timestamptz not null default now()
);

create table public.media (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id),
  task_id text not null,
  media_type text not null,
  url text not null,
  created_at timestamptz not null default now()
);

alter table public.tasks enable row level security;
alter table public.media enable row level security;

create policy "tasks_owner_select" on public.tasks
  for select using (auth.uid() = user_id);
create policy "tasks_owner_insert" on public.tasks
  for insert with check (auth.uid() = user_id);
create policy "tasks_owner_update" on public.tasks
  for update using (auth.uid() = user_id);
create policy "tasks_owner_delete" on public.tasks
  for delete using (auth.uid() = user_id);

create policy "media_owner_select" on public.media
  for select using (auth.uid() = user_id);
create policy "media_owner_insert" on public.media
  for insert with check (auth.uid() = user_id);
create policy "media_owner_update" on public.media
  for update using (auth.uid() = user_id);
create policy "media_owner_delete" on public.media
  for delete using (auth.uid() = user_id);
```

RLS 通过 `auth.uid()` 绑定 `user_id`，确保不同用户数据隔离。

---

## 回滚策略

- 若 Supabase 集成不稳定：短期内仅使用本地/内存索引，保持 JWT 鉴权链路不变。


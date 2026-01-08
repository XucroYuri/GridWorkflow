# GridWorkflow 安全策略改进方案

**文档版本**: v1.0  
**创建日期**: 2026-01-07  
**安全等级**: 🔒 内部  
**状态**: ⚠️ **待实施**  
**完成度**: 0%  
**最后更新**: 2026-01-08  

---

## 📋 文档目的

本文档基于前期代码审查和规划验证中识别的安全问题，提供系统性的安全改进方案，确保 GridWorkflow 在各阶段迭代中保持安全基线。

---

## 🔍 安全问题汇总

### 问题分类与优先级

| 编号 | 问题类别 | 严重度 | 优先级 | 影响范围 |
|------|----------|--------|--------|----------|
| SEC-01 | CORS 配置过于宽松 | 🔴 高 | P0 | 全站 |
| SEC-02 | BYOK 密钥存储安全 | 🔴 高 | P0 | v1.2-02 |
| SEC-03 | Sentry 敏感信息泄露 | 🟡 中 | P1 | v1.1-03 |
| SEC-04 | JWT 验证配置 | 🟡 中 | P1 | 认证模块 |
| SEC-05 | API 速率限制缺失 | 🟡 中 | P1 | 全站 |
| SEC-06 | 日志敏感信息 | 🟡 中 | P1 | 后端 |
| SEC-07 | RLS 策略验证 | 🟡 中 | P2 | v1.2-01 |
| SEC-08 | 依赖包安全 | 🟢 低 | P2 | 全栈 |

---

## 🔴 SEC-01: CORS 配置过于宽松

### 问题描述

当前 CORS 配置在未设置环境变量时默认允许所有源访问：

```python
# backend/app/main.py:20-25
def _parse_cors_origins(raw: str) -> list[str]:
    if not raw:
        return ["*"]  # ❌ 危险：默认允许所有源
    if raw.strip() == "*":
        return ["*"]
    return [origin.strip() for origin in raw.split(",") if origin.strip()]
```

### 风险分析

| 风险 | 描述 | 影响 |
|------|------|------|
| CSRF 攻击 | 恶意网站可发起跨站请求 | 高 |
| 数据泄露 | 任意源可读取 API 响应 | 高 |
| 凭证窃取 | 配合其他漏洞可窃取 Token | 中 |

### 改进方案

#### 方案 A: 生产环境强制配置 (推荐)

```python
# backend/app/main.py

def _parse_cors_origins(raw: str, env: str) -> list[str]:
    """
    解析 CORS 允许的源列表。
    
    安全策略：
    - 生产环境必须显式配置，否则报错
    - 开发环境默认允许 localhost
    - 禁止在生产环境使用 "*"
    """
    # 生产环境强制配置
    if env.lower() == "production":
        if not raw or not raw.strip():
            raise ValueError(
                "安全错误：生产环境必须配置 CORS_ALLOW_ORIGINS。"
                "请设置环境变量，例如：CORS_ALLOW_ORIGINS=https://your-domain.com"
            )
        if raw.strip() == "*":
            raise ValueError(
                "安全错误：生产环境禁止使用 CORS_ALLOW_ORIGINS=* 配置。"
                "请指定具体的允许域名。"
            )
    
    # 开发环境默认值
    if not raw or not raw.strip():
        return [
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000",
        ]
    
    # 解析配置的源列表
    origins = [origin.strip() for origin in raw.split(",") if origin.strip()]
    
    # 验证源格式
    for origin in origins:
        if not origin.startswith(("http://", "https://")):
            raise ValueError(f"无效的 CORS 源格式：{origin}")
    
    return origins


# 调用时传入环境
allowed_origins = _parse_cors_origins(settings.cors_allow_origins, settings.env)
```

#### 方案 B: 配置校验中间件

```python
# backend/app/core/security.py

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

class CORSValidationMiddleware(BaseHTTPMiddleware):
    """验证请求来源是否在允许列表中"""
    
    def __init__(self, app, allowed_origins: list[str]):
        super().__init__(app)
        self.allowed_origins = set(allowed_origins)
        self.allow_all = "*" in allowed_origins
    
    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")
        
        # 无 Origin 头的请求（如同源请求）放行
        if not origin:
            return await call_next(request)
        
        # 验证 Origin
        if not self.allow_all and origin not in self.allowed_origins:
            # 记录可疑请求
            logger.warning(
                "CORS 拒绝: origin=%s allowed=%s",
                origin,
                self.allowed_origins
            )
            # 不返回 403，而是不添加 CORS 头，让浏览器拦截
        
        return await call_next(request)
```

### 环境变量配置示例

```bash
# .env.production (必须配置)
CORS_ALLOW_ORIGINS=https://gridworkflow.vercel.app,https://custom.domain.com

# .env.development (可选)
CORS_ALLOW_ORIGINS=http://localhost:5173,http://localhost:3000
```

### 验证清单

- [ ] 生产环境部署时验证 CORS 配置已设置
- [ ] 测试跨域请求被正确拦截
- [ ] 验证合法域名可正常访问

---

## 🔴 SEC-02: BYOK 密钥存储安全

### 问题描述

v1.2-02 BYOK 方案中存在以下安全问题：

1. **固定 Salt**: 使用硬编码的 Salt 值
2. **密钥派生依赖**: 加密密钥从 JWT Secret 派生
3. **无密钥轮换**: 无法安全更换加密密钥
4. **缺少审计**: 密钥使用无记录

```python
# 原方案问题代码
class KeyEncryption:
    def _create_fernet(self, secret: str) -> Fernet:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'gridworkflow_api_key_salt',  # ❌ 固定 Salt
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(secret.encode()))
        return Fernet(key)
```

### 风险分析

| 风险 | 描述 | 影响 |
|------|------|------|
| 密钥泄露 | JWT Secret 泄露导致所有用户 Key 可解密 | 🔴 极高 |
| 彩虹表攻击 | 固定 Salt 降低暴力破解难度 | 🔴 高 |
| 无法轮换 | 安全事件后无法更换加密密钥 | 🟡 中 |
| 合规问题 | 无审计日志不符合安全合规要求 | 🟡 中 |

### 改进方案

#### 方案 A: 增强型自研加密 (短期)

```python
# backend/app/core/encryption.py

import os
import base64
import hashlib
from datetime import datetime
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.config import get_settings
from app.core.logger import get_logger

logger = get_logger("encryption")


class SecureKeyEncryption:
    """
    安全的 API Key 加密服务
    
    安全特性：
    1. 每用户独立 Salt
    2. 独立的加密主密钥（非 JWT Secret）
    3. 支持密钥版本和轮换
    4. 审计日志
    """
    
    # 当前加密版本
    CURRENT_VERSION = 1
    
    def __init__(self):
        settings = get_settings()
        
        # 使用独立的加密主密钥
        self.master_key = settings.encryption_master_key
        if not self.master_key:
            raise RuntimeError(
                "安全错误：ENCRYPTION_MASTER_KEY 未配置。"
                "请生成一个强随机密钥：openssl rand -base64 32"
            )
        
        # 验证密钥强度
        if len(self.master_key) < 32:
            raise RuntimeError("安全错误：ENCRYPTION_MASTER_KEY 长度不足 32 字符")
    
    def _derive_user_key(self, user_id: str, version: int = CURRENT_VERSION) -> Fernet:
        """为每个用户派生独立的加密密钥"""
        
        # 用户特定的 Salt（结合 user_id 和版本号）
        salt = hashlib.sha256(
            f"gw_key_v{version}_{user_id}".encode()
        ).digest()[:16]
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = base64.urlsafe_b64encode(
            kdf.derive(self.master_key.encode())
        )
        return Fernet(key)
    
    def encrypt(self, api_key: str, user_id: str) -> dict:
        """
        加密 API Key
        
        返回：
        {
            "encrypted": "加密后的数据",
            "version": 1,
            "user_id_hash": "用户ID哈希（用于验证）"
        }
        """
        fernet = self._derive_user_key(user_id)
        encrypted = fernet.encrypt(api_key.encode()).decode()
        
        # 记录加密操作（不记录实际 Key）
        logger.info(
            "API Key 加密: user_id_hash=%s version=%d",
            self._hash_user_id(user_id),
            self.CURRENT_VERSION
        )
        
        return {
            "encrypted": encrypted,
            "version": self.CURRENT_VERSION,
            "user_id_hash": self._hash_user_id(user_id),
        }
    
    def decrypt(self, encrypted_data: dict, user_id: str) -> str:
        """
        解密 API Key
        
        参数：
            encrypted_data: 包含 encrypted, version, user_id_hash 的字典
            user_id: 当前用户 ID
        """
        # 验证用户匹配
        stored_hash = encrypted_data.get("user_id_hash")
        if stored_hash and stored_hash != self._hash_user_id(user_id):
            logger.warning(
                "API Key 解密失败: user_id 不匹配 stored=%s current=%s",
                stored_hash,
                self._hash_user_id(user_id)
            )
            raise ValueError("密钥所有者验证失败")
        
        version = encrypted_data.get("version", 1)
        fernet = self._derive_user_key(user_id, version)
        
        try:
            decrypted = fernet.decrypt(
                encrypted_data["encrypted"].encode()
            ).decode()
            
            logger.info(
                "API Key 解密: user_id_hash=%s version=%d",
                self._hash_user_id(user_id),
                version
            )
            
            return decrypted
            
        except InvalidToken:
            logger.error(
                "API Key 解密失败: InvalidToken user_id_hash=%s",
                self._hash_user_id(user_id)
            )
            raise ValueError("密钥解密失败")
    
    def rotate_key(self, old_encrypted: dict, user_id: str) -> dict:
        """
        轮换加密密钥（重新加密）
        
        用于主密钥更换后重新加密所有用户 Key
        """
        # 用旧版本解密
        old_version = old_encrypted.get("version", 1)
        old_fernet = self._derive_user_key(user_id, old_version)
        
        try:
            plaintext = old_fernet.decrypt(
                old_encrypted["encrypted"].encode()
            ).decode()
        except InvalidToken:
            raise ValueError("旧密钥解密失败，无法轮换")
        
        # 用新版本重新加密
        new_encrypted = self.encrypt(plaintext, user_id)
        
        logger.info(
            "API Key 轮换: user_id_hash=%s old_version=%d new_version=%d",
            self._hash_user_id(user_id),
            old_version,
            self.CURRENT_VERSION
        )
        
        return new_encrypted
    
    @staticmethod
    def preview(api_key: str) -> str:
        """生成 Key 预览（前4后4）"""
        if len(api_key) <= 8:
            return '*' * len(api_key)
        return f"{api_key[:4]}{'*' * (len(api_key) - 8)}{api_key[-4:]}"
    
    @staticmethod
    def _hash_user_id(user_id: str) -> str:
        """生成用户 ID 哈希（用于日志，保护隐私）"""
        return hashlib.sha256(user_id.encode()).hexdigest()[:12]


# 单例
_encryption: Optional[SecureKeyEncryption] = None

def get_encryption() -> SecureKeyEncryption:
    global _encryption
    if _encryption is None:
        _encryption = SecureKeyEncryption()
    return _encryption
```

#### 方案 B: 使用 Supabase Vault (推荐，中期)

```sql
-- 使用 Supabase 内置的 Vault 功能存储敏感数据

-- 1. 启用 Vault 扩展
CREATE EXTENSION IF NOT EXISTS supabase_vault;

-- 2. 创建加密密钥
SELECT vault.create_secret(
  'gridworkflow-api-key-encryption',
  'encryption_key_for_user_api_keys'
);

-- 3. 存储用户 API Key
SELECT vault.create_secret(
  'user_api_key_' || user_id,
  api_key_value,
  'User API Key for ' || provider
);

-- 4. 读取时解密
SELECT vault.decrypted_secrets 
WHERE name = 'user_api_key_' || user_id;
```

```python
# backend/app/core/vault.py

from supabase import create_client

class SupabaseVault:
    """使用 Supabase Vault 存储敏感数据"""
    
    def __init__(self, supabase_url: str, service_role_key: str):
        self.client = create_client(supabase_url, service_role_key)
    
    async def store_api_key(
        self,
        user_id: str,
        provider: str,
        api_key: str
    ) -> str:
        """存储 API Key 到 Vault"""
        secret_name = f"user_api_key_{user_id}_{provider}"
        
        result = self.client.rpc('vault.create_secret', {
            'name': secret_name,
            'secret': api_key,
            'description': f'API Key for {provider}'
        }).execute()
        
        return result.data['id']
    
    async def get_api_key(
        self,
        user_id: str,
        provider: str
    ) -> str | None:
        """从 Vault 获取 API Key"""
        secret_name = f"user_api_key_{user_id}_{provider}"
        
        result = self.client.rpc('vault.decrypted_secrets', {
            'name': secret_name
        }).execute()
        
        if result.data:
            return result.data[0]['decrypted_secret']
        return None
    
    async def delete_api_key(
        self,
        user_id: str,
        provider: str
    ) -> bool:
        """删除 Vault 中的 API Key"""
        secret_name = f"user_api_key_{user_id}_{provider}"
        
        result = self.client.rpc('vault.delete_secret', {
            'name': secret_name
        }).execute()
        
        return result.data is not None
```

#### 审计日志表

```sql
-- 创建 API Key 审计日志表
CREATE TABLE api_key_audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id),
  key_id UUID REFERENCES user_api_keys(id),
  
  -- 操作类型
  action TEXT NOT NULL CHECK (action IN (
    'created', 'accessed', 'verified', 'deleted', 'rotated', 'failed_access'
  )),
  
  -- 上下文信息
  ip_address INET,
  user_agent TEXT,
  request_id TEXT,
  
  -- 结果
  success BOOLEAN DEFAULT true,
  error_message TEXT,
  
  -- 时间戳
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 索引
CREATE INDEX idx_audit_logs_user ON api_key_audit_logs(user_id);
CREATE INDEX idx_audit_logs_key ON api_key_audit_logs(key_id);
CREATE INDEX idx_audit_logs_action ON api_key_audit_logs(action);
CREATE INDEX idx_audit_logs_time ON api_key_audit_logs(created_at DESC);

-- RLS: 只有管理员可查看审计日志
ALTER TABLE api_key_audit_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Only admins can view audit logs" ON api_key_audit_logs
  FOR SELECT USING (
    auth.uid() IN (SELECT user_id FROM admin_users)
  );

-- 禁止普通用户修改
CREATE POLICY "No user modification" ON api_key_audit_logs
  FOR ALL USING (false);
```

### 配置要求

```bash
# .env (新增)
# 独立的加密主密钥（必须！不要使用 JWT Secret）
ENCRYPTION_MASTER_KEY=your-32-char-random-key-here

# 生成方法：
# openssl rand -base64 32
```

### 验证清单

- [ ] 加密主密钥与 JWT Secret 独立
- [ ] 每用户使用独立派生密钥
- [ ] 审计日志正确记录
- [ ] 密钥轮换功能可用
- [ ] 安全测试通过

---

## 🟡 SEC-03: Sentry 敏感信息泄露

### 问题描述

原方案使用黑名单过滤敏感 Headers，可能遗漏新增字段：

```typescript
// 原方案 - 黑名单
beforeSend(event) {
  if (event.request?.headers) {
    delete event.request.headers['Authorization'];
  }
  return event;
}
```

### 改进方案：白名单过滤

```typescript
// frontend/src/lib/sentry.ts

const SAFE_HEADERS = [
  'Content-Type',
  'Accept',
  'Accept-Language',
  'X-Request-ID',
  'X-Requested-With',
];

const SAFE_BODY_FIELDS = [
  'style',
  'aspect_ratio',
  'duration',
  'model',
  // 注意：不包含 plot、prompt 等可能含用户内容的字段
];

export function initSentry() {
  Sentry.init({
    dsn: import.meta.env.VITE_SENTRY_DSN,
    
    beforeSend(event, hint) {
      // 1. Headers 白名单过滤
      if (event.request?.headers) {
        const safeHeaders: Record<string, string> = {};
        for (const key of SAFE_HEADERS) {
          if (event.request.headers[key]) {
            safeHeaders[key] = event.request.headers[key];
          }
        }
        event.request.headers = safeHeaders;
      }
      
      // 2. 移除请求体中的敏感数据
      if (event.request?.data) {
        try {
          const data = typeof event.request.data === 'string'
            ? JSON.parse(event.request.data)
            : event.request.data;
          
          const safeData: Record<string, unknown> = {};
          for (const key of SAFE_BODY_FIELDS) {
            if (data[key] !== undefined) {
              safeData[key] = data[key];
            }
          }
          // 标记其他字段被过滤
          safeData['_filtered_fields'] = Object.keys(data)
            .filter(k => !SAFE_BODY_FIELDS.includes(k));
          
          event.request.data = JSON.stringify(safeData);
        } catch {
          // 无法解析则移除整个 body
          event.request.data = '[FILTERED]';
        }
      }
      
      // 3. 过滤 URL 中的查询参数
      if (event.request?.url) {
        try {
          const url = new URL(event.request.url);
          // 移除所有查询参数
          url.search = '';
          event.request.url = url.toString();
        } catch {
          // URL 解析失败则保留原值
        }
      }
      
      // 4. 过滤用户数据
      if (event.user) {
        // 只保留匿名 ID
        event.user = {
          id: event.user.id,
        };
      }
      
      // 5. 过滤面包屑中的敏感数据
      if (event.breadcrumbs) {
        event.breadcrumbs = event.breadcrumbs.map(crumb => ({
          ...crumb,
          data: crumb.data ? { _filtered: true } : undefined,
        }));
      }
      
      return event;
    },
    
    // 采样率控制
    tracesSampleRate: 0.1,  // 降低采样率
    replaysSessionSampleRate: 0.05,  // 5% 会话回放
    replaysOnErrorSampleRate: 0.5,  // 错误时 50% 回放（非 100%）
  });
}
```

### 后端 Sentry 配置

```python
# backend/app/core/sentry.py

import sentry_sdk

SAFE_HEADERS = {
    'content-type',
    'accept',
    'x-request-id',
}

def _before_send(event, hint):
    """发送前过滤敏感信息"""
    
    # 1. Headers 白名单
    if 'request' in event and 'headers' in event['request']:
        safe_headers = {}
        for key, value in event['request']['headers'].items():
            if key.lower() in SAFE_HEADERS:
                safe_headers[key] = value
        event['request']['headers'] = safe_headers
    
    # 2. 移除请求体
    if 'request' in event:
        event['request'].pop('data', None)
        event['request'].pop('cookies', None)
    
    # 3. 过滤 extra 中的敏感数据
    if 'extra' in event:
        sensitive_keys = ['api_key', 'token', 'secret', 'password', 'prompt']
        for key in list(event['extra'].keys()):
            if any(s in key.lower() for s in sensitive_keys):
                event['extra'][key] = '[FILTERED]'
    
    return event


def init_sentry():
    settings = get_settings()
    
    if settings.env.lower() != 'production':
        return
    
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.env,
        before_send=_before_send,
        traces_sample_rate=0.1,
        profiles_sample_rate=0.05,
        
        # 不发送 PII
        send_default_pii=False,
    )
```

---

## 🟡 SEC-04: JWT 验证配置

### 问题描述

JWT 验证缺少部分安全配置：

1. 未强制验证 audience
2. 未强制验证 issuer
3. Token 刷新机制不明确

### 改进方案

```python
# backend/app/core/auth.py

def _decode_supabase_jwt(token: str, settings: Settings) -> dict[str, Any]:
    """
    解码并验证 Supabase JWT
    
    安全检查：
    1. 签名验证
    2. 过期时间验证
    3. audience 验证（如配置）
    4. issuer 验证（如配置）
    """
    secret = settings.supabase_jwt_secret
    if not secret:
        logger.error("JWT Secret 未配置")
        raise AuthError("鉴权失败，请稍后重试。")
    
    # 构建验证选项
    options = {
        "verify_signature": True,
        "verify_exp": True,
        "verify_nbf": True,
        "verify_iat": True,
        "require": ["exp", "sub"],  # 必须包含这些声明
    }
    
    # audience 验证
    decode_kwargs: dict[str, Any] = {}
    if settings.supabase_jwt_audience:
        options["verify_aud"] = True
        decode_kwargs["audience"] = settings.supabase_jwt_audience
    else:
        options["verify_aud"] = False
        logger.warning("JWT audience 未配置，跳过验证")
    
    # issuer 验证
    if settings.supabase_jwt_issuer:
        options["verify_iss"] = True
        decode_kwargs["issuer"] = settings.supabase_jwt_issuer
    else:
        options["verify_iss"] = False
    
    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],  # 只允许 HS256
            options=options,
            **decode_kwargs,
        )
        
        # 额外检查：token 不应该太新（防止时间漂移攻击）
        iat = payload.get("iat", 0)
        if iat > time.time() + 60:  # 允许 60 秒时钟偏移
            logger.warning("JWT iat 在未来: iat=%d now=%d", iat, time.time())
            raise AuthError("鉴权失败，请重新登录。")
        
        return payload
        
    except jwt.ExpiredSignatureError:
        logger.info("JWT 已过期")
        raise AuthError("登录已过期，请重新登录。")
    except jwt.InvalidAudienceError:
        logger.warning("JWT audience 不匹配")
        raise AuthError("鉴权失败，请重新登录。")
    except jwt.InvalidIssuerError:
        logger.warning("JWT issuer 不匹配")
        raise AuthError("鉴权失败，请重新登录。")
    except jwt.InvalidTokenError as exc:
        logger.warning("JWT 验证失败: %s", str(exc))
        raise AuthError("鉴权失败，请登录。")
```

### 推荐配置

```bash
# .env.production
SUPABASE_JWT_SECRET=your-jwt-secret
SUPABASE_JWT_AUDIENCE=authenticated
SUPABASE_JWT_ISSUER=https://your-project.supabase.co/auth/v1
```

---

## 🟡 SEC-05: API 速率限制

### 问题描述

当前 API 无速率限制，存在以下风险：
- 暴力破解
- 资源耗尽攻击
- API 滥用

### 改进方案

#### 方案 A: 使用 slowapi (简单)

```python
# backend/app/core/rate_limit.py

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)

# main.py 集成
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 路由使用
@router.post("/concept")
@limiter.limit("10/minute")  # 每分钟 10 次
async def concept(...):
    ...

@router.post("/video/generate")
@limiter.limit("5/minute")  # 视频生成更严格
async def generate_video(...):
    ...
```

#### 方案 B: Redis 分布式限流 (推荐)

```python
# backend/app/core/rate_limit.py

import redis.asyncio as redis
from fastapi import Request, HTTPException

class RateLimiter:
    """基于 Redis 的分布式速率限制"""
    
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
    
    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int
    ) -> tuple[bool, int, int]:
        """
        检查速率限制
        
        返回: (是否允许, 当前计数, 剩余配额)
        """
        pipe = self.redis.pipeline()
        
        # 使用滑动窗口算法
        now = time.time()
        window_start = now - window_seconds
        
        # 移除过期记录
        pipe.zremrangebyscore(key, 0, window_start)
        # 添加当前请求
        pipe.zadd(key, {str(now): now})
        # 计数
        pipe.zcard(key)
        # 设置过期
        pipe.expire(key, window_seconds)
        
        results = await pipe.execute()
        count = results[2]
        
        allowed = count <= limit
        remaining = max(0, limit - count)
        
        return allowed, count, remaining
    
    def middleware(self, limit: int = 100, window: int = 60):
        """创建限流中间件"""
        async def rate_limit_middleware(request: Request, call_next):
            # 使用 user_id 或 IP 作为 key
            user_id = getattr(request.state, "user_id", None)
            key = f"rate_limit:{user_id or request.client.host}:{request.url.path}"
            
            allowed, count, remaining = await self.check_rate_limit(
                key, limit, window
            )
            
            if not allowed:
                raise HTTPException(
                    status_code=429,
                    detail={
                        "code": "RATE_LIMITED",
                        "message": f"请求过于频繁，请 {window} 秒后重试",
                        "retry_after": window,
                    },
                    headers={
                        "Retry-After": str(window),
                        "X-RateLimit-Limit": str(limit),
                        "X-RateLimit-Remaining": str(remaining),
                    }
                )
            
            response = await call_next(request)
            
            # 添加速率限制响应头
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            
            return response
        
        return rate_limit_middleware
```

### 端点限制建议

| 端点 | 限制 | 窗口 | 原因 |
|------|------|------|------|
| `/concept` | 10/分钟 | 60s | AI 调用成本 |
| `/storyboard/plan` | 10/分钟 | 60s | AI 调用成本 |
| `/storyboard/generate` | 5/分钟 | 60s | 图像生成成本高 |
| `/video/generate` | 3/分钟 | 60s | 视频生成成本最高 |
| `/video/status/*` | 60/分钟 | 60s | 轮询，允许较高频率 |
| 其他 | 100/分钟 | 60s | 默认限制 |

---

## 🟡 SEC-06: 日志敏感信息

### 问题描述

日志可能包含敏感信息：
- API Key
- 用户输入 (prompt)
- JWT Token

### 改进方案

```python
# backend/app/core/logger.py

import re
import logging
from typing import Any

# 敏感字段模式
SENSITIVE_PATTERNS = [
    (re.compile(r'(api[_-]?key|token|secret|password|authorization)\s*[=:]\s*["\']?([^"\'\s]+)["\']?', re.I), r'\1=***'),
    (re.compile(r'Bearer\s+[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+', re.I), 'Bearer ***'),
    (re.compile(r'sk-[A-Za-z0-9]{20,}'), 'sk-***'),
]

class SensitiveFilter(logging.Filter):
    """过滤日志中的敏感信息"""
    
    def filter(self, record: logging.LogRecord) -> bool:
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            for pattern, replacement in SENSITIVE_PATTERNS:
                record.msg = pattern.sub(replacement, record.msg)
        
        if hasattr(record, 'args') and record.args:
            filtered_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    for pattern, replacement in SENSITIVE_PATTERNS:
                        arg = pattern.sub(replacement, arg)
                filtered_args.append(arg)
            record.args = tuple(filtered_args)
        
        return True


def get_logger(level: str = "INFO") -> logging.Logger:
    """创建带敏感信息过滤的 Logger"""
    logger = logging.getLogger("gridworkflow")
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )
        handler.setFormatter(formatter)
        
        # 添加敏感信息过滤器
        handler.addFilter(SensitiveFilter())
        
        logger.addHandler(handler)
    
    logger.setLevel(level.upper())
    return logger


# 安全日志函数
def safe_log_request(logger: logging.Logger, request_data: dict[str, Any]):
    """安全地记录请求数据"""
    safe_data = {}
    
    # 白名单字段
    SAFE_FIELDS = ['style', 'aspect_ratio', 'duration', 'model', 'provider']
    
    for key in SAFE_FIELDS:
        if key in request_data:
            safe_data[key] = request_data[key]
    
    # 记录有哪些字段被过滤
    filtered_fields = [k for k in request_data.keys() if k not in SAFE_FIELDS]
    if filtered_fields:
        safe_data['_filtered'] = filtered_fields
    
    logger.debug("Request data: %s", safe_data)
```

---

## 🟡 SEC-07: RLS 策略验证

### 问题描述

多租户 RLS 策略可能存在：
- 性能问题（每次查询子查询）
- 策略遗漏
- 测试覆盖不足

### 改进方案

#### RLS 策略优化

```sql
-- 优化后的 RLS 策略

-- 1. 创建高效的用户组织查询函数
CREATE OR REPLACE FUNCTION user_organization_ids()
RETURNS UUID[] AS $$
  SELECT COALESCE(
    array_agg(organization_id),
    ARRAY[]::UUID[]
  )
  FROM organization_members
  WHERE user_id = auth.uid()
$$ LANGUAGE sql STABLE SECURITY DEFINER;

-- 2. 为函数创建索引支持
CREATE INDEX IF NOT EXISTS idx_org_members_user_org 
ON organization_members(user_id, organization_id);

-- 3. 优化的 RLS 策略
DROP POLICY IF EXISTS "用户组织数据访问" ON workflow_sessions;
CREATE POLICY "用户组织数据访问" ON workflow_sessions
  FOR ALL USING (
    organization_id = ANY(user_organization_ids())
  );

-- 4. 添加策略测试函数
CREATE OR REPLACE FUNCTION test_rls_policy(
  p_table_name TEXT,
  p_user_id UUID,
  p_expected_count INT
) RETURNS BOOLEAN AS $$
DECLARE
  actual_count INT;
BEGIN
  -- 临时设置用户上下文
  PERFORM set_config('request.jwt.claims', 
    json_build_object('sub', p_user_id)::text, true);
  
  EXECUTE format('SELECT count(*) FROM %I', p_table_name)
  INTO actual_count;
  
  RETURN actual_count = p_expected_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

#### RLS 测试套件

```python
# backend/tests/test_rls.py

import pytest
from supabase import create_client

class TestRLSPolicies:
    """RLS 策略测试"""
    
    @pytest.fixture
    def user_a_client(self):
        """用户 A 的 Supabase 客户端"""
        return create_client(url, user_a_token)
    
    @pytest.fixture
    def user_b_client(self):
        """用户 B 的 Supabase 客户端"""
        return create_client(url, user_b_token)
    
    def test_user_cannot_see_other_users_sessions(
        self, user_a_client, user_b_client
    ):
        """用户不能看到其他用户的会话"""
        # 用户 A 创建会话
        result_a = user_a_client.table('workflow_sessions').insert({
            'plot': 'Test plot'
        }).execute()
        session_id = result_a.data[0]['id']
        
        # 用户 B 尝试访问
        result_b = user_b_client.table('workflow_sessions').select('*').eq(
            'id', session_id
        ).execute()
        
        assert len(result_b.data) == 0, "用户 B 不应该能看到用户 A 的会话"
    
    def test_organization_members_can_see_shared_data(
        self, org_member_a_client, org_member_b_client, shared_org_id
    ):
        """同组织成员可以看到共享数据"""
        # 成员 A 创建数据
        result_a = org_member_a_client.table('workflow_sessions').insert({
            'organization_id': shared_org_id,
            'plot': 'Shared plot'
        }).execute()
        session_id = result_a.data[0]['id']
        
        # 成员 B 可以访问
        result_b = org_member_b_client.table('workflow_sessions').select('*').eq(
            'id', session_id
        ).execute()
        
        assert len(result_b.data) == 1, "同组织成员应该能看到共享数据"
```

---

## 🟢 SEC-08: 依赖包安全

### 问题描述

第三方依赖可能存在已知漏洞。

### 改进方案

#### 自动化安全扫描

```yaml
# .github/workflows/security.yml

name: Security Scan

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 0 * * 1'  # 每周一扫描

jobs:
  python-security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run Snyk for Python
        uses: snyk/actions/python@master
        with:
          args: --file=backend/requirements.txt
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
      
      - name: Run pip-audit
        run: |
          pip install pip-audit
          cd backend
          pip-audit -r requirements.txt

  javascript-security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run npm audit
        run: |
          cd frontend
          npm audit --audit-level=moderate
      
      - name: Run Snyk for JavaScript
        uses: snyk/actions/node@master
        with:
          args: --file=frontend/package.json
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}

  sast:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run Semgrep
        uses: returntocorp/semgrep-action@v1
        with:
          config: >-
            p/python
            p/javascript
            p/typescript
            p/security-audit
```

#### Dependabot 配置

```yaml
# .github/dependabot.yml

version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/backend"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
    labels:
      - "dependencies"
      - "security"
    
  - package-ecosystem: "npm"
    directory: "/frontend"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
    labels:
      - "dependencies"
      - "security"
```

---

## 📋 实施计划

### 阶段 1: 紧急修复 (本周)

| 任务 | 优先级 | 工时 | 负责人 |
|------|--------|------|--------|
| SEC-01 CORS 修复 | P0 | 2h | - |
| SEC-06 日志过滤 | P1 | 3h | - |
| SEC-05 基础限流 | P1 | 4h | - |

### 阶段 2: v1.1 配套 (2 周内)

| 任务 | 优先级 | 工时 | 负责人 |
|------|--------|------|--------|
| SEC-03 Sentry 白名单 | P1 | 2h | - |
| SEC-04 JWT 增强 | P1 | 3h | - |
| SEC-08 CI 安全扫描 | P2 | 4h | - |

### 阶段 3: v1.2 配套 (1 月内)

| 任务 | 优先级 | 工时 | 负责人 |
|------|--------|------|--------|
| SEC-02 BYOK 加密 | P0 | 8h | - |
| SEC-07 RLS 测试 | P2 | 6h | - |

---

## 📎 附录

### A. 安全配置检查清单

```bash
# 生产环境部署前检查

# 1. CORS 配置
[ ] CORS_ALLOW_ORIGINS 已设置为具体域名
[ ] 不是 "*"

# 2. JWT 配置
[ ] SUPABASE_JWT_SECRET 已设置
[ ] SUPABASE_JWT_AUDIENCE 已设置 (推荐)
[ ] SUPABASE_JWT_ISSUER 已设置 (推荐)

# 3. 加密配置
[ ] ENCRYPTION_MASTER_KEY 已设置 (BYOK 功能)
[ ] 与 JWT_SECRET 不同

# 4. 日志配置
[ ] LOG_LEVEL 设为 INFO (非 DEBUG)

# 5. 监控配置
[ ] SENTRY_DSN 已设置
[ ] Sentry 敏感信息过滤已启用

# 6. 速率限制
[ ] 限流中间件已启用
[ ] Redis 连接配置 (如使用分布式限流)
```

### B. 安全事件响应

```
安全事件响应流程:

1. 发现 → 2. 评估 → 3. 遏制 → 4. 修复 → 5. 恢复 → 6. 复盘

关键联系人:
- 安全负责人: [待指定]
- 技术负责人: [待指定]

密钥泄露响应:
1. 立即轮换泄露的密钥
2. 审计受影响的数据
3. 通知受影响用户
4. 更新安全策略
```

---

**文档维护者**: AI Security Reviewer  
**审核周期**: 每季度  
**下次审核**: 2026-04-01



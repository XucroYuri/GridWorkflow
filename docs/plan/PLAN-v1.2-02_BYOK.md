# PLAN-v1.2-02: BYOK (Bring Your Own Key)

**版本**: v1.2  
**优先级**: P1  
**预估工时**: 5-7 天  
**状态**: 📝 规划中  
**前置依赖**: v1.2-01 多租户支持  

---

## 1. 概述

### 1.1 背景

BYOK (Bring Your Own Key) 允许用户使用自己的 AI API Key：
- 降低平台运营成本
- 用户获得更大灵活性
- 支持私有部署场景
- 减轻配额压力

### 1.2 目标

- 用户可配置自己的 API Key
- 安全存储用户密钥
- 自动选择用户 Key 或平台 Key
- 支持多种 AI 服务 Key

---

## 2. 当前状态分析

### 2.1 现有实现

```python
# ai_service.py - 当前 Key 解析逻辑
def _resolve_api_key(settings: Settings, user_key: Optional[str]) -> str:
    trimmed = (user_key or "").strip()
    if trimmed:
        return trimmed  # 优先使用请求头中的 Key
    if settings.ai_gateway_api_key:
        return settings.ai_gateway_api_key  # 回退到平台 Key
    raise APIError(code="UNAUTHORIZED", message="API Key 未配置")
```

### 2.2 问题

| 问题 | 说明 |
|------|------|
| Key 传输安全 | 通过 Header 明文传递 |
| Key 存储缺失 | 每次请求需携带 |
| 无 Key 验证 | 不验证 Key 有效性 |
| 无 Key 管理 | 无法增删改查 |

---

## 3. 技术方案

### 3.1 数据模型

```sql
-- 用户 API Key 表
CREATE TABLE user_api_keys (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
  
  -- Key 信息
  provider TEXT NOT NULL,  -- 'openai', 'gemini', 't8star', 等
  name TEXT NOT NULL,  -- 用户自定义名称
  
  -- 加密存储
  encrypted_key TEXT NOT NULL,  -- 加密后的 API Key
  key_preview TEXT NOT NULL,  -- 前4后4字符预览 (sk-xxxx...xxxx)
  
  -- 状态
  is_active BOOLEAN DEFAULT true,
  last_used_at TIMESTAMPTZ,
  last_error TEXT,
  
  -- 元数据
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  
  CONSTRAINT valid_provider CHECK (provider IN (
    'openai', 'gemini', 't8star', 'anthropic', 'custom'
  ))
);

-- 索引
CREATE INDEX idx_user_api_keys_user ON user_api_keys(user_id);
CREATE INDEX idx_user_api_keys_provider ON user_api_keys(provider);

-- RLS
ALTER TABLE user_api_keys ENABLE ROW LEVEL SECURITY;

CREATE POLICY "用户只能访问自己的 Key" ON user_api_keys
  FOR ALL USING (auth.uid() = user_id);
```

### 3.2 密钥加密服务

```python
# backend/app/core/encryption.py
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.config import get_settings


class KeyEncryption:
    """API Key 加密服务"""
    
    def __init__(self):
        settings = get_settings()
        # 使用 JWT Secret 派生加密密钥
        self._fernet = self._create_fernet(settings.supabase_jwt_secret)
    
    def _create_fernet(self, secret: str) -> Fernet:
        """从 secret 派生 Fernet 密钥"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'gridworkflow_api_key_salt',  # 固定 salt
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(secret.encode()))
        return Fernet(key)
    
    def encrypt(self, api_key: str) -> str:
        """加密 API Key"""
        return self._fernet.encrypt(api_key.encode()).decode()
    
    def decrypt(self, encrypted_key: str) -> str:
        """解密 API Key"""
        return self._fernet.decrypt(encrypted_key.encode()).decode()
    
    @staticmethod
    def preview(api_key: str) -> str:
        """生成 Key 预览（前4后4）"""
        if len(api_key) <= 8:
            return '*' * len(api_key)
        return f"{api_key[:4]}...{api_key[-4:]}"


# 单例
_encryption = None

def get_encryption() -> KeyEncryption:
    global _encryption
    if _encryption is None:
        _encryption = KeyEncryption()
    return _encryption
```

### 3.3 Key 管理 API

```python
# backend/app/api/routes/keys.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.auth import require_user
from app.core.encryption import get_encryption
from app.core.supabase import get_supabase_client
from app.schemas.response import success_response, error_response

router = APIRouter(prefix="/api/v1/keys", tags=["keys"])


class CreateKeyRequest(BaseModel):
    provider: str
    name: str
    api_key: str


class KeyResponse(BaseModel):
    id: str
    provider: str
    name: str
    key_preview: str
    is_active: bool
    last_used_at: str | None
    created_at: str


@router.get("")
async def list_keys(user_id: str = Depends(require_user)):
    """获取用户的 API Keys"""
    client = get_supabase_client()
    result = client.table('user_api_keys').select(
        'id, provider, name, key_preview, is_active, last_used_at, created_at'
    ).eq('user_id', user_id).order('created_at', desc=True).execute()
    
    return success_response(result.data)


@router.post("")
async def create_key(
    payload: CreateKeyRequest,
    user_id: str = Depends(require_user)
):
    """创建 API Key"""
    encryption = get_encryption()
    client = get_supabase_client()
    
    # 验证 Key 格式
    if not payload.api_key.strip():
        raise HTTPException(400, detail="API Key 不能为空")
    
    # 检查是否已存在同 provider 的 Key
    existing = client.table('user_api_keys').select('id').eq(
        'user_id', user_id
    ).eq('provider', payload.provider).execute()
    
    if existing.data:
        raise HTTPException(400, detail=f"已存在 {payload.provider} 的 API Key")
    
    # 加密存储
    encrypted = encryption.encrypt(payload.api_key)
    preview = encryption.preview(payload.api_key)
    
    result = client.table('user_api_keys').insert({
        'user_id': user_id,
        'provider': payload.provider,
        'name': payload.name,
        'encrypted_key': encrypted,
        'key_preview': preview,
    }).execute()
    
    return success_response({
        'id': result.data[0]['id'],
        'provider': payload.provider,
        'name': payload.name,
        'key_preview': preview,
    })


@router.delete("/{key_id}")
async def delete_key(
    key_id: str,
    user_id: str = Depends(require_user)
):
    """删除 API Key"""
    client = get_supabase_client()
    
    result = client.table('user_api_keys').delete().eq(
        'id', key_id
    ).eq('user_id', user_id).execute()
    
    if not result.data:
        raise HTTPException(404, detail="Key 不存在")
    
    return success_response(None)


@router.post("/{key_id}/verify")
async def verify_key(
    key_id: str,
    user_id: str = Depends(require_user)
):
    """验证 API Key 有效性"""
    encryption = get_encryption()
    client = get_supabase_client()
    
    # 获取加密的 Key
    key_record = client.table('user_api_keys').select(
        'encrypted_key, provider'
    ).eq('id', key_id).eq('user_id', user_id).single().execute()
    
    if not key_record.data:
        raise HTTPException(404, detail="Key 不存在")
    
    # 解密
    api_key = encryption.decrypt(key_record.data['encrypted_key'])
    provider = key_record.data['provider']
    
    # 验证（根据 provider 调用对应 API）
    is_valid = await _verify_key_with_provider(api_key, provider)
    
    # 更新状态
    client.table('user_api_keys').update({
        'is_active': is_valid,
        'last_used_at': 'now()',
        'last_error': None if is_valid else '验证失败',
    }).eq('id', key_id).execute()
    
    return success_response({'valid': is_valid})


async def _verify_key_with_provider(api_key: str, provider: str) -> bool:
    """验证 Key 有效性"""
    import httpx
    
    endpoints = {
        't8star': 'https://ai.t8star.cn/v1/models',
        'openai': 'https://api.openai.com/v1/models',
        'gemini': 'https://generativelanguage.googleapis.com/v1/models',
    }
    
    url = endpoints.get(provider)
    if not url:
        return True  # 无法验证的 provider 默认有效
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                url,
                headers={'Authorization': f'Bearer {api_key}'}
            )
            return resp.status_code == 200
    except Exception:
        return False
```

### 3.4 Key 选择服务改造

```python
# backend/app/services/key_resolver.py
from typing import Optional

from app.core.config import Settings
from app.core.encryption import get_encryption
from app.core.supabase import get_supabase_client


class KeyResolver:
    """API Key 解析服务"""
    
    def __init__(self, user_id: str, settings: Settings):
        self.user_id = user_id
        self.settings = settings
        self.encryption = get_encryption()
        self.client = get_supabase_client()
    
    async def resolve(
        self,
        provider: str,
        request_key: Optional[str] = None
    ) -> tuple[str, str]:
        """
        解析 API Key
        
        Returns:
            tuple: (api_key, source) - source 为 'request'/'user'/'platform'
        """
        # 1. 优先使用请求中的 Key
        if request_key and request_key.strip():
            return request_key.strip(), 'request'
        
        # 2. 尝试获取用户存储的 Key
        user_key = await self._get_user_key(provider)
        if user_key:
            return user_key, 'user'
        
        # 3. 回退到平台 Key
        platform_key = self._get_platform_key(provider)
        if platform_key:
            return platform_key, 'platform'
        
        raise ValueError(f"未找到 {provider} 的 API Key")
    
    async def _get_user_key(self, provider: str) -> Optional[str]:
        """获取用户存储的 Key"""
        result = self.client.table('user_api_keys').select(
            'encrypted_key'
        ).eq('user_id', self.user_id).eq(
            'provider', provider
        ).eq('is_active', True).single().execute()
        
        if not result.data:
            return None
        
        # 解密
        encrypted = result.data['encrypted_key']
        return self.encryption.decrypt(encrypted)
    
    def _get_platform_key(self, provider: str) -> Optional[str]:
        """获取平台 Key"""
        key_map = {
            't8star': self.settings.ai_gateway_api_key,
            # 可扩展更多平台 Key
        }
        return key_map.get(provider)
```

### 3.5 前端 Key 管理界面

```tsx
// pages/Settings/ApiKeys.tsx
import { useState, useEffect } from 'react';
import { Key, Plus, Trash2, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import apiClient from '../../services/apiClient';

interface ApiKey {
  id: string;
  provider: string;
  name: string;
  key_preview: string;
  is_active: boolean;
  last_used_at: string | null;
  created_at: string;
}

const PROVIDERS = [
  { value: 't8star', label: 'T8Star AI' },
  { value: 'openai', label: 'OpenAI' },
  { value: 'gemini', label: 'Google Gemini' },
];

export const ApiKeysPage: React.FC = () => {
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  
  // 表单状态
  const [provider, setProvider] = useState('t8star');
  const [name, setName] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const fetchKeys = async () => {
    try {
      const response = await apiClient.get('/keys');
      setKeys(response.data || []);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchKeys();
  }, []);

  const handleAdd = async () => {
    if (!name.trim() || !apiKey.trim()) return;
    
    setSubmitting(true);
    try {
      await apiClient.post('/keys', {
        provider,
        name: name.trim(),
        api_key: apiKey.trim(),
      });
      setShowAdd(false);
      setName('');
      setApiKey('');
      fetchKeys();
    } catch (error) {
      alert('添加失败，请检查 API Key 格式');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('确定删除此 API Key?')) return;
    
    try {
      await apiClient.delete(`/keys/${id}`);
      fetchKeys();
    } catch (error) {
      alert('删除失败');
    }
  };

  const handleVerify = async (id: string) => {
    try {
      const response = await apiClient.post(`/keys/${id}/verify`);
      fetchKeys();
      alert(response.data?.valid ? 'Key 有效' : 'Key 无效');
    } catch (error) {
      alert('验证失败');
    }
  };

  if (loading) {
    return <div className="p-6">加载中...</div>;
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">API Keys</h1>
        <button
          onClick={() => setShowAdd(true)}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
        >
          <Plus className="w-4 h-4" />
          添加 Key
        </button>
      </div>

      <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4 mb-6">
        <p className="text-sm text-yellow-800">
          💡 添加自己的 API Key 后，系统将优先使用您的 Key 进行调用，
          不占用平台配额。您的 Key 将被加密存储。
        </p>
      </div>

      {/* Key 列表 */}
      <div className="space-y-4">
        {keys.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <Key className="w-12 h-12 mx-auto mb-4 opacity-30" />
            <p>暂无 API Key</p>
          </div>
        ) : (
          keys.map((key) => (
            <div
              key={key.id}
              className="bg-white border border-gray-200 rounded-lg p-4 flex justify-between items-center"
            >
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-medium">{key.name}</span>
                  <span className="text-xs bg-gray-100 px-2 py-0.5 rounded">
                    {key.provider}
                  </span>
                  {key.is_active ? (
                    <CheckCircle className="w-4 h-4 text-green-500" />
                  ) : (
                    <XCircle className="w-4 h-4 text-red-500" />
                  )}
                </div>
                <p className="text-sm text-gray-500 font-mono">
                  {key.key_preview}
                </p>
                {key.last_used_at && (
                  <p className="text-xs text-gray-400 mt-1">
                    最后使用: {new Date(key.last_used_at).toLocaleString()}
                  </p>
                )}
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => handleVerify(key.id)}
                  className="text-blue-600 hover:text-blue-800 text-sm"
                >
                  验证
                </button>
                <button
                  onClick={() => handleDelete(key.id)}
                  className="text-red-600 hover:text-red-800"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* 添加弹窗 */}
      {showAdd && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">添加 API Key</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">服务商</label>
                <select
                  value={provider}
                  onChange={(e) => setProvider(e.target.value)}
                  className="w-full border border-gray-300 rounded-md p-2"
                >
                  {PROVIDERS.map((p) => (
                    <option key={p.value} value={p.value}>
                      {p.label}
                    </option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">名称</label>
                <input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="例如：我的 Key"
                  className="w-full border border-gray-300 rounded-md p-2"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">API Key</label>
                <input
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="sk-..."
                  className="w-full border border-gray-300 rounded-md p-2 font-mono"
                />
              </div>
            </div>
            
            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => setShowAdd(false)}
                className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                取消
              </button>
              <button
                onClick={handleAdd}
                disabled={submitting || !name.trim() || !apiKey.trim()}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
              >
                {submitting && <Loader2 className="w-4 h-4 animate-spin" />}
                添加
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
```

---

## 4. 实施计划

### Phase 1: 后端基础 (Day 1-2)

| 任务 | 工时 | 产出 |
|------|------|------|
| 数据表设计 | 2h | DDL |
| 加密服务实现 | 4h | encryption.py |
| Key 管理 API | 6h | routes/keys.py |

### Phase 2: Key 解析改造 (Day 3-4)

| 任务 | 工时 | 产出 |
|------|------|------|
| KeyResolver 实现 | 4h | key_resolver.py |
| 改造 ai_service | 4h | 集成 KeyResolver |
| 改造 video_service | 4h | 集成 KeyResolver |
| 单元测试 | 4h | pytest |

### Phase 3: 前端实现 (Day 5-6)

| 任务 | 工时 | 产出 |
|------|------|------|
| API Key 管理页 | 6h | ApiKeysPage.tsx |
| 路由配置 | 1h | 设置页入口 |
| 状态指示 | 2h | Key 状态展示 |
| 测试验证 | 3h | E2E 测试 |

### Phase 4: 文档与发布 (Day 7)

| 任务 | 工时 | 产出 |
|------|------|------|
| 用户文档 | 2h | BYOK 使用指南 |
| 安全文档 | 2h | 密钥存储说明 |
| 发布检查 | 2h | 安全审计 |

---

## 5. 风险评估

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 密钥泄露 | 低 | 极高 | 加密存储 + 审计日志 |
| 加密密钥丢失 | 低 | 高 | 密钥备份 |
| Key 被滥用 | 中 | 中 | 使用量监控 |
| 验证 API 变更 | 低 | 低 | 优雅降级 |

---

## 6. 验收标准

### 6.1 功能验证

- [ ] 可添加/删除 API Key
- [ ] Key 加密存储
- [ ] 自动选择用户 Key
- [ ] Key 验证功能正常

### 6.2 安全验证

- [ ] Key 不以明文存储
- [ ] Key 预览不暴露完整信息
- [ ] 跨用户 Key 不可访问

### 6.3 兼容验证

- [ ] 无用户 Key 时回退平台 Key
- [ ] 请求头 Key 仍可用

---

## 7. 参考资料

- [Cryptography 库文档](https://cryptography.io/)
- [Fernet 对称加密](https://cryptography.io/en/latest/fernet/)
- 内部文档: `docs/specs/SPEC-ARCH-03_MULTI_TENANCY_BYOK.md`
- 内部文档: `docs/specs/SPEC-005_KEY_COST_MGMT.md`

---

**作者**: AI Planner  
**最后更新**: 2026-01-07


# SPEC-ARCH-03: 多用户架构与 BYOK 策略 (Multi-Tenancy & BYOK)

## 1. 背景与目标
为了支持商业化运营并解决单一 API Key 的并发瓶颈，系统需从"单机演示版"演进为"多租户 SaaS 架构"。
核心策略是 **BYOK (Bring Your Own Key)**：允许重度用户绑定自己的 API Key，从而绕过系统的免费配额限制。

## 2. 核心设计：混合网关策略 (Hybrid Gateway Strategy)

### 2.1 配额分层 (Quota Tiering)
系统将根据 Key 的来源，将任务分发到不同的执行通道：

| 通道类型 | Key 来源 | 速率限制 (Rate Limit) | 适用人群 | 成本承担 |
| :--- | :--- | :--- | :--- | :--- |
| **Public Lane** | `process.env.API_KEY` | 严格 (e.g., 2 RPM / User) | 访客、试用用户 | 平台方 |
| **Fast Lane** | 用户本地存储 Key | 无限制 (取决于用户配额) | 专业用户、企业 | 用户 |

### 2.2 密钥管理 (Key Management)
*   **存储位置**: 用户的 API Keys **仅存储在浏览器 LocalStorage/IndexedDB** 中。
*   **加密**: 虽然是本地存储，建议进行轻量级混淆（Base64 或简单 XOR），防止被恶意插件轻易读取。
*   **注入时机**: 在发起 API 请求的瞬间（Factory 创建 Provider 实例时），从 Context 中读取 Key 并注入。

## 3. 架构变更

### 3.1 `UserContext` 扩展
在 `User` 类型中增加配置字段（仅本地有效，不通过 Auth 同步）：

```typescript
interface UserConfig {
    apiKeys: {
        google?: string; // Gemini / Veo
        openai?: string; // Future
        midjourney?: string; // Future
    };
    preferences: {
        useOwnKey: boolean; // Toggle
    };
}
```

### 3.2 `QueueService` 路由升级
`APIDispatcher` 需要感知当前任务的"付费属性"。

```typescript
// services/queueService.ts

// 1. 任务入队时标记 Key 来源
interface TaskPayload {
    // ... existing
    useCustomKey: boolean;
}

// 2. 处理逻辑变更
// Public Lane: 维持现有的 Token Bucket 限流。
// Fast Lane: 直接放行，甚至可以并发执行（如果 Provider 支持）。
```

### 3.3 Auth Provider 固化
*   移除 `DEMO_USER` 的自动回退逻辑，在生产环境中强制要求 Firebase 登录。
*   保持 `AuthContext` 接口不变，但增强错误处理和 Session 恢复机制。

## 4. UI 交互设计
1.  **用户设置面板**: 新增 "API Gateways" 选项卡。
2.  **密钥输入**: 提供输入框绑定 Google AI Studio Key，并提供"验证有效性"按钮（调用 `listModels` 接口测试）。
3.  **状态指示**: 在 Header 区域显示当前使用的通道状态（"⚡ Fast Lane" 或 "🐢 Public Lane"）。

## 5. 安全声明
*   文档中必须明确告知用户：**"您的 API Key 仅存储在本地设备，绝不会发送至我们的服务器。"**


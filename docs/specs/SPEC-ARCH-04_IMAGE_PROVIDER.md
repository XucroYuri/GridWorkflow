# SPEC-ARCH-04: 绘图能力抽象层 (Image Provider Abstraction)

## 1. 目标
目前的 `visualService.ts` 深度绑定了 Gemini 的 `generateContent` 接口（用于 Nano Banana / Imagen）。为了支持未来的 **Imagen 3**, **Midjourney**, **Stable Diffusion**，需要构建统一的绘图适配器。

## 2. 核心接口 `IImageProvider`

```typescript
export interface ImageGenerationParams {
    prompt: string;
    negativePrompt?: string;
    aspectRatio: AspectRatio; // Enum: "16:9", "1:1", etc.
    width?: number;
    height?: number;
    referenceImages?: string[]; // Base64，用于图生图或结构参考
    styleReference?: string; // Base64，用于风格参考
    count?: number; // Default 1
}

export interface IImageProvider {
    readonly id: string; // e.g., 'gemini-nano', 'midjourney-v6'
    readonly name: string;
    
    // 核心生成方法
    // 返回 Base64 字符串或 URL
    generate(params: ImageGenerationParams): Promise<string[]>;
    
    // 能力检测
    capabilities: {
        img2img: boolean;
        controlNet: boolean; // 是否支持结构参考
    };
}
```

## 3. 适配器实现规划

### 3.1 `GeminiImageProvider` (当前)
*   迁移现有的 `visualService.ts` 逻辑。
*   处理 `gemini-3-pro-image-preview` 和 `gemini-2.5-flash-image` 的参数差异。

### 3.2 `RemoteProxyProvider` (未来通用)
*   用于接入 Midjourney 或 DALL-E 3。
*   通常这些模型不提供浏览器端 SDK，需要通过 Next.js API Route 或 Serverless Function 转发。
*   该 Provider 将负责调用后端代理接口。

## 4. 工厂模式 (`ImageFactory`)
UI 层通过 `ImageFactory` 获取实例。工厂会根据用户的 `UserConfig` (见 SPEC-ARCH-03) 决定实例化哪个 Provider，并注入对应的 API Key。

```typescript
// 伪代码
const provider = ImageFactory.getProvider(
    userConfig.preferredImageModel, // e.g. 'gemini'
    userConfig.apiKeys.google // Injected Key
);
const urls = await provider.generate({...});
```

## 5. 实施步骤
1.  定义 `IImageProvider` 接口。
2.  重构 `visualService.ts`，将其拆分为 `GeminiImageProvider`。
3.  更新 `useShotGenerator` 和 `useAssetGenerator` 使用 Factory 获取实例。
4.  在 UI 中增加模型选择器（暂仅显示 Gemini，未来扩展）。


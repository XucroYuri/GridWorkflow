# SPEC-ARCH-01: 视频生成模块重构 (Modular Video Architecture)

> **原 ID**: SPEC-003
> **优先级**: P1

## 1. 目标
目前的视频生成逻辑与 `Veo` 模型强耦合。为了应对未来可能引入的 `Sora`, `Runway`, `Kling` (可灵) 等模型，需要构建一个**多模型适配器架构**。

## 2. 架构设计

### 2.1 核心接口 `IVideoProvider`
定义所有视频生成模型必须遵循的统一契约。

```typescript
export interface VideoGenerationParams {
    prompt: string; // 核心提示词
    negativePrompt?: string;
    sourceImage?: string; // base64 (可选，用于图生视频)
    aspectRatio: '16:9' | '9:16';
    duration?: 5 | 10;
    motionStrength?: number;
    // 模型特定参数 (如 Veo 的 seed)
    modelParams?: Record<string, any>; 
}

export interface IVideoProvider {
    readonly providerId: string; // e.g., 'google-veo', 'openai-sora'
    readonly name: string; // e.g., 'Veo 3.1'
    
    // 能力检测
    capabilities: {
        img2video: boolean;
        text2video: boolean;
        maxDuration: number;
    };
    
    // 生成方法 (返回 Job ID)
    generate(params: VideoGenerationParams): Promise<string>;
    
    // 状态轮询
    checkStatus(jobId: string): Promise<{
        status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
        progress?: number;
        resultUrl?: string;
        error?: string;
    }>;
}
```

### 2.2 适配器实现 (`services/video/providers/`)
*   `VeoProvider.ts`: 封装现有的 Google GenAI Veo 逻辑。实现上述接口。
*   `MockProvider.ts`: 用于开发测试，快速返回假视频，节省 Token。

### 2.3 视频服务工厂 (`VideoServiceFactory`)
UI 层不再直接调用 `geminiService` 或 `veoService`，而是：

```typescript
// hooks/useVideoGenerator.ts
const provider = VideoServiceFactory.getProvider(selectedModelId); // 'google-veo' by default
const jobId = await provider.generate({...});
```

## 3. 数据结构更新
在 `VideoGenerationMeta` 中增加 `providerId` 字段，以便回溯该视频是由哪个模型生成的。

```typescript
export interface VideoGenerationMeta {
    // ... existing
    providerId: string; // 'google-veo-3.1'
    generationParams: any; // 存储该模型特定的参数快照
}
```

## 4. 实施步骤
1.  定义 `IVideoProvider` 接口。
2.  将现有的 `services/videoService.ts` 逻辑迁移至 `VeoProvider` 类。
3.  创建 `VideoServiceFactory`。
4.  更新 `VideoGenerationModal` UI，允许（在未来）选择模型，目前默认 Veo。

## 5. 验收标准
1.  代码中不再有硬编码的 `veo-3.1` 字符串散落在 UI 组件中。
2.  能够通过配置文件轻松切换默认视频模型。


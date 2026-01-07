# SPEC-ARCH-02: LLM 能力抽象层 (LLM Abstraction Layer)

## 1. 目标
目前的 `services/geminiService.ts` 与 Google GenAI SDK 深度绑定。为了支持未来的多模型策略（如接入 GPT-4 处理复杂逻辑，或 Claude 3 处理长文本），必须构建统一的 **LLM 适配器架构**。

## 2. 核心接口设计

### 2.1 `ILLMProvider`
定义通用的文本与多模态交互契约。

```typescript
export interface GenerationConfig {
    temperature?: number;
    maxOutputTokens?: number;
    jsonSchema?: any; // 统一的 Schema 定义
    systemInstruction?: string;
}

export interface ILLMProvider {
    readonly id: string;
    readonly name: string;

    // 1. 基础文本生成
    generateText(prompt: string, config?: GenerationConfig): Promise<string>;

    // 2. 结构化数据生成 (核心能力)
    // 强制要求返回 JSON 对象，Provider 需处理不同模型的 JSON Mode 差异
    generateStructure<T>(prompt: string, schema: any, config?: GenerationConfig): Promise<T>;

    // 3. 多模态理解 (图生文)
    // 用于 L1 阶段的视觉反推或 Asset 审查
    analyzeImage(base64Image: string, prompt: string): Promise<string>;
}
```

## 3. 适配器实现策略

### 3.1 `GeminiProvider` (默认)
*   封装现有的 `@google/genai` 调用。
*   将通用的 `jsonSchema` 转换为 Gemini 特有的 `responseSchema` 格式。
*   处理 Gemini 特有的 `SAFETY` 阻断错误，将其转化为通用的 `AppError`。

### 3.2 `OpenAIProvider` (预留)
*   使用 OpenAI SDK。
*   将 `jsonSchema` 映射为 `response_format: { type: "json_object" }` 或 Function Calling。

## 4. 服务层重构 (`Service Layer Refactor`)

原有的业务逻辑（如 `analysisService.ts`, `reasoningService.ts`）不再直接 import SDK，而是依赖注入 Provider。

**Before:**
```typescript
import { GoogleGenAI } from "@google/genai";
// ...
const ai = new GoogleGenAI(...)
await ai.models.generateContent(...)
```

**After:**
```typescript
import { LLMFactory } from "../providers/LLMFactory";
// ...
const provider = LLMFactory.getProvider('gemini-pro'); // 或从用户配置读取
const result = await provider.generateStructure(prompt, schema);
```

## 5. 实施步骤
1.  创建 `services/llm/` 目录。
2.  定义 `ILLMProvider` 接口。
3.  实现 `GeminiProvider` 类，迁移现有的重试逻辑 (Exponential Backoff) 到 Provider 内部。
4.  创建 `LLMFactory` 单例。
5.  逐步替换 `geminiService.ts` 中的直接调用。

## 6. 验收标准
1.  全局搜索代码库，除 `GeminiProvider.ts` 和 `VeoProvider.ts` 外，不得出现 `@google/genai` 的导入。
2.  可以通过修改配置文件，无缝切换到底层 mock 实现（用于测试）。


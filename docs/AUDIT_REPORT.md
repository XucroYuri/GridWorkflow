# Grid-Cine Director 架构审计报告 (Status: ACTIVE)

> **版本**: 2025-Q4 (Revised v2)
> **战略核心**: 单用户体验闭环 + 多模型架构适配 (Multi-Model Ready) + 多租户商业化准备

## 1. 战略决策矩阵 (Strategic Decision Matrix)

### 1.1 核心体验 (Core Experience)
*   **[P0] 线性时间轴 (Timeline View)**
    *   **决策**: 开发底部可折叠面板，支持分镜线性播放/拖拽。
    *   **对应 Spec**: `SPEC-UI-01`

*   **[P0] 剧本分析强韧化 (Prompt Robustness)**
    *   **决策**: 使用 JSON Schema 强约束代替模糊匹配算法，解决 L2/L3 切片对齐问题。
    *   **对应 Spec**: `SPEC-AI-01`

### 1.2 架构演进 (Architecture Evolution)
为了应对 AI 模型的快速迭代及商业化并发需求，系统必须建立全栈的抽象层。

*   **[P1] 视频模块重构 (Modular Video)**
    *   **对应 Spec**: `SPEC-ARCH-01` (解耦 Veo)

*   **[P1] LLM 能力抽象 (LLM Abstraction)**
    *   **对应 Spec**: `SPEC-ARCH-02` (解耦 Gemini Text)

*   **[P1] 多用户与 BYOK 策略 (Multi-Tenancy & BYOK)** - *NEW*
    *   **现状**: 依赖全局环境变量 Key，存在并发瓶颈；Auth 严重依赖 Demo 模式。
    *   **决策**: 实施“混合网关策略”。支持用户绑定自有 API Key (BYOK)，并在前端实现基于 Key 来源的动态限流与路由。
    *   **对应 Spec**: `SPEC-ARCH-03`

*   **[P1] 绘图能力抽象 (Image Gen Abstraction)** - *NEW*
    *   **现状**: `visualService` 强绑定 Gemini Image 模型。
    *   **决策**: 建立 `IImageProvider`，为未来接入 Imagen 3, Midjourney, SDXL 做准备。
    *   **对应 Spec**: `SPEC-ARCH-04`

---

## 2. 风险雷达 (Risk Radar)

| 风险点 | 等级 | 应对策略 |
| :--- | :--- | :--- |
| **Concurrency Bottleneck (并发瓶颈)** | **Critical** | 实施 `SPEC-ARCH-03` 的 BYOK 策略，将高频请求分流至用户自有 Key。 |
| **Vendor Lock-in (厂商锁定)** | High | 全面实施 Provider 模式 (Video/LLM/Image)。 |
| **Security (Key Leakage)** | High | 用户 Key 仅本地存储 (Client-side Storage)，严禁上传服务端。 |

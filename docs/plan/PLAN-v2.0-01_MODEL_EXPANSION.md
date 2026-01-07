# PLAN-v2.0-01: 模型扩展

**版本**: v2.0  
**优先级**: P2  
**预估工时**: 15-20 天  
**状态**: 📝 规划中  
**前置依赖**: v1.2-03 任务队列  

---

## 1. 概述

### 1.1 背景

当前仅支持 T8Star (Sora 2) 视频生成，需要扩展支持更多模型：
- Runway Gen-3
- Pika Labs
- Kling AI
- MiniMax (海螺)
- 其他新兴模型

### 1.2 目标

- 统一的模型适配层
- 用户可选择生成模型
- 模型能力元数据管理
- 模型切换无缝体验

---

## 2. 技术方案概要

### 2.1 Provider 抽象层

```python
# 目标架构
class VideoProvider(ABC):
    """视频生成 Provider 抽象基类"""
    
    @property
    @abstractmethod
    def name(self) -> str: ...
    
    @property
    @abstractmethod
    def capabilities(self) -> ProviderCapabilities: ...
    
    @abstractmethod
    async def generate(self, request: GenerateRequest) -> GenerateResponse: ...
    
    @abstractmethod
    async def get_status(self, task_id: str) -> TaskStatus: ...
    
    @abstractmethod
    async def cancel(self, task_id: str) -> bool: ...


@dataclass
class ProviderCapabilities:
    max_duration: int
    supported_ratios: list[str]
    supports_image_input: bool
    supports_hd: bool
    typical_generation_time: int  # 秒
```

### 2.2 支持的模型规划

| 模型 | Provider | 优先级 | 特点 |
|------|----------|--------|------|
| Sora 2 | T8Star | ✅ 已有 | 高质量、稳定 |
| Runway Gen-3 | Runway | P1 | 商业级、API 成熟 |
| Pika 1.5 | Pika | P2 | 风格化、低成本 |
| Kling | 快手 | P2 | 国内访问快 |
| MiniMax | 海螺 | P3 | 中文优化 |

### 2.3 关键实现点

1. **Provider 注册机制**: 动态加载可用 Provider
2. **能力发现**: 前端获取各 Provider 支持的参数
3. **统一错误处理**: 不同 Provider 错误码映射
4. **配额独立计算**: 按 Provider 分别计费

---

## 3. 实施路线

### Phase 1: 抽象层重构 (Week 1)
- 定义 Provider 接口
- 重构 T8Star 为首个实现
- 注册机制实现

### Phase 2: Runway 集成 (Week 2)
- Runway API 适配
- 参数映射
- 测试验证

### Phase 3: 其他 Provider (Week 3-4)
- Pika 集成
- Kling 集成
- 前端模型选择 UI

---

## 4. 验收标准

- [ ] 至少支持 3 种视频生成模型
- [ ] 用户可在 UI 中选择模型
- [ ] 各模型参数正确约束
- [ ] 统一的状态查询和错误处理

---

**详细设计文档待 v1.2 完成后补充**

---

**作者**: AI Planner  
**最后更新**: 2026-01-07


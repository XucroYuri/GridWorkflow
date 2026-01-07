# PLAN-v1.1-01: 前端性能优化

**版本**: v1.1  
**优先级**: P1  
**预估工时**: 3-4 天  
**状态**: 📝 规划中  

---

## 1. 概述

### 1.1 背景

当前 GridWorkflow 前端存在以下性能问题：
- 图片资源无懒加载，首屏加载时间长
- 页面切换无骨架屏，用户体验差
- 大组件（如 GridWorkflow.tsx 469行）渲染性能不佳
- 未使用 React.memo/useMemo 优化

### 1.2 目标

- 首屏加载时间 (FCP) < 1.5s
- 可交互时间 (TTI) < 3s
- Lighthouse 性能评分 > 80
- 用户感知加载流畅

---

## 2. 当前状态分析

### 2.1 现有问题

```
问题清单:
├── 图片加载
│   ├── 概念图直接 <img src={url}> 无 loading="lazy"
│   ├── 九宫格图片无渐进式加载
│   └── 视频缩略图无预加载策略
│
├── 组件渲染
│   ├── GridWorkflow.tsx 每次 state 更新全量渲染
│   ├── TaskList 无虚拟滚动
│   └── 无 React.memo 包裹纯展示组件
│
└── 资源加载
    ├── 无代码分割 (Code Splitting)
    ├── 第三方库无按需加载
    └── CSS 无 PurgeCSS 优化
```

### 2.2 性能基线测量

| 指标 | 当前值 | 目标值 |
|------|--------|--------|
| FCP (First Contentful Paint) | ~2.5s | < 1.5s |
| LCP (Largest Contentful Paint) | ~4s | < 2.5s |
| TTI (Time to Interactive) | ~5s | < 3s |
| Bundle Size | ~450KB | < 300KB |

---

## 3. 技术方案

### 3.1 图片懒加载

#### 3.1.1 原生 loading 属性

```tsx
// 简单方案：使用原生 loading="lazy"
<img 
  src={conceptImageUrl} 
  alt="Concept" 
  loading="lazy"
  decoding="async"
/>
```

#### 3.1.2 渐进式加载组件

```tsx
// components/common/ProgressiveImage.tsx
import { useState, useEffect } from 'react';

interface ProgressiveImageProps {
  src: string;
  placeholder?: string;
  alt: string;
  className?: string;
}

export const ProgressiveImage: React.FC<ProgressiveImageProps> = ({
  src,
  placeholder = 'data:image/svg+xml,...', // blur placeholder
  alt,
  className
}) => {
  const [imageSrc, setImageSrc] = useState(placeholder);
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    const img = new Image();
    img.src = src;
    img.onload = () => {
      setImageSrc(src);
      setIsLoaded(true);
    };
  }, [src]);

  return (
    <img
      src={imageSrc}
      alt={alt}
      className={`${className} transition-opacity duration-300 ${
        isLoaded ? 'opacity-100' : 'opacity-50 blur-sm'
      }`}
    />
  );
};
```

### 3.2 骨架屏实现

#### 3.2.1 通用骨架组件

```tsx
// components/common/Skeleton.tsx
interface SkeletonProps {
  width?: string | number;
  height?: string | number;
  className?: string;
  variant?: 'text' | 'rect' | 'circle';
}

export const Skeleton: React.FC<SkeletonProps> = ({
  width = '100%',
  height = 20,
  className = '',
  variant = 'rect'
}) => {
  const baseClass = 'animate-pulse bg-gray-200';
  const variantClass = {
    text: 'rounded',
    rect: 'rounded-md',
    circle: 'rounded-full'
  };

  return (
    <div
      className={`${baseClass} ${variantClass[variant]} ${className}`}
      style={{ width, height }}
    />
  );
};
```

#### 3.2.2 页面级骨架屏

```tsx
// components/video/GridWorkflowSkeleton.tsx
export const GridWorkflowSkeleton: React.FC = () => (
  <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
    {/* Header */}
    <div className="flex justify-between mb-6">
      <Skeleton width={200} height={24} />
      <Skeleton width={80} height={24} />
    </div>
    
    {/* Progress Bar */}
    <Skeleton width="100%" height={6} className="mb-6" />
    
    {/* Form Fields */}
    <div className="space-y-4">
      <Skeleton width="100%" height={120} />
      <Skeleton width="60%" height={40} />
      <div className="grid grid-cols-2 gap-4">
        <Skeleton height={40} />
        <Skeleton height={40} />
      </div>
    </div>
    
    {/* Button */}
    <Skeleton width="100%" height={48} className="mt-6" />
  </div>
);
```

### 3.3 组件优化

#### 3.3.1 React.memo 包裹

```tsx
// 包裹纯展示组件
export const TaskItem = React.memo<TaskItemProps>(({ task, onSelect }) => {
  // ...组件实现
});

// 深度比较（复杂对象）
export const VideoPreview = React.memo<VideoPreviewProps>(
  ({ task }) => { /* ... */ },
  (prevProps, nextProps) => {
    return prevProps.task?.task_id === nextProps.task?.task_id &&
           prevProps.task?.status === nextProps.task?.status;
  }
);
```

#### 3.3.2 useMemo/useCallback 优化

```tsx
// GridWorkflow.tsx
const memoizedAnchors = useMemo(() => ({
  character: { text: state.anchors.character.text },
  environment: { text: state.anchors.environment.text },
  prop: { text: state.anchors.prop.text }
}), [state.anchors]);

const handleGenerateConcept = useCallback(async () => {
  // ... 实现
}, [state.plot, state.style, memoizedAnchors, state.aspectRatio]);
```

### 3.4 代码分割

#### 3.4.1 路由级懒加载

```tsx
// App.tsx
import { lazy, Suspense } from 'react';

const VideoStudio = lazy(() => import('./pages/VideoStudio'));
const Home = lazy(() => import('./pages/Home'));

// 使用
<Suspense fallback={<PageSkeleton />}>
  <Routes>
    <Route path="/" element={<Home />} />
    <Route path="/video" element={<VideoStudio />} />
  </Routes>
</Suspense>
```

#### 3.4.2 组件级懒加载

```tsx
// 大型组件懒加载
const GridWorkflow = lazy(() => import('../components/video/GridWorkflow'));
const Lightbox = lazy(() => import('../components/Lightbox'));
```

### 3.5 Bundle 优化

#### 3.5.1 Vite 配置优化

```typescript
// vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor-react': ['react', 'react-dom', 'react-router-dom'],
          'vendor-supabase': ['@supabase/supabase-js'],
          'vendor-ui': ['lucide-react', 'clsx'],
        }
      }
    },
    // 启用 gzip 压缩预览
    reportCompressedSize: true,
  },
  // CSS 代码分割
  css: {
    devSourcemap: true,
  }
});
```

---

## 4. 实施计划

### Phase 1: 基础优化 (Day 1)

| 任务 | 工时 | 产出 |
|------|------|------|
| 添加图片 loading="lazy" | 2h | 所有 img 标签 |
| 创建 Skeleton 组件 | 2h | 通用骨架组件 |
| 路由懒加载配置 | 2h | 代码分割 |

### Phase 2: 组件优化 (Day 2)

| 任务 | 工时 | 产出 |
|------|------|------|
| React.memo 包裹 | 3h | TaskList, VideoPreview |
| useMemo/useCallback | 3h | GridWorkflow 优化 |
| 创建 ProgressiveImage | 2h | 渐进式图片组件 |

### Phase 3: Bundle 优化 (Day 3)

| 任务 | 工时 | 产出 |
|------|------|------|
| Vite 配置优化 | 2h | manualChunks |
| TailwindCSS PurgeCSS | 2h | CSS 瘦身 |
| 依赖分析优化 | 2h | 移除未用依赖 |

### Phase 4: 测试验收 (Day 4)

| 任务 | 工时 | 产出 |
|------|------|------|
| Lighthouse 测试 | 2h | 性能报告 |
| 真实场景测试 | 2h | 用户体验验证 |
| 文档更新 | 2h | 性能优化指南 |

---

## 5. 风险评估

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 懒加载导致布局抖动 | 中 | 低 | 设置固定宽高比 |
| Suspense fallback 闪烁 | 中 | 中 | 添加最小加载时间 |
| 代码分割过细 | 低 | 中 | 合理划分 chunk 边界 |
| 缓存策略冲突 | 低 | 高 | 版本化资源命名 |

---

## 6. 验收标准

### 6.1 性能指标

- [ ] FCP < 1.5s (Lighthouse)
- [ ] LCP < 2.5s (Lighthouse)
- [ ] TTI < 3s (Lighthouse)
- [ ] 性能评分 > 80 (Lighthouse)

### 6.2 功能验证

- [ ] 图片懒加载正常工作
- [ ] 骨架屏显示流畅无闪烁
- [ ] 路由切换无卡顿
- [ ] 移动端性能可接受

### 6.3 代码质量

- [ ] Bundle 主包 < 200KB
- [ ] 无 console 警告
- [ ] TypeScript 无报错

---

## 7. 参考资料

- [React 性能优化指南](https://react.dev/reference/react/memo)
- [Vite 构建优化](https://vitejs.dev/guide/build.html)
- [Web Vitals 指标](https://web.dev/vitals/)
- [Lighthouse CI](https://github.com/GoogleChrome/lighthouse-ci)

---

**作者**: AI Planner  
**最后更新**: 2026-01-07


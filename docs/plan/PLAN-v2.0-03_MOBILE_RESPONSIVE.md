# PLAN-v2.0-03: 移动端适配

**版本**: v2.0  
**优先级**: P2  
**预估工时**: 10-15 天  
**状态**: 📝 规划中  

---

## 1. 概述

### 1.1 背景

当前 UI 主要针对桌面端设计，移动端体验较差：
- GridWorkflow 组件在小屏幕上布局混乱
- 触摸交互不友好
- 视频预览尺寸问题
- 导航困难

### 1.2 目标

- 完全响应式布局
- 触摸友好交互
- 移动端专属优化
- PWA 支持（可选）

---

## 2. 现状分析

### 2.1 问题清单

| 问题 | 页面/组件 | 严重度 |
|------|-----------|--------|
| 12列网格在手机上过窄 | VideoStudio | 高 |
| 长表单滚动困难 | GridWorkflow | 中 |
| 视频播放器过小 | VideoPreview | 高 |
| 侧边栏遮挡内容 | MainLayout | 中 |
| 按钮触摸区域小 | 全局 | 中 |

### 2.2 目标设备

| 设备类型 | 屏幕宽度 | 优先级 |
|----------|----------|--------|
| 手机 | < 640px | P1 |
| 平板竖屏 | 640-1024px | P1 |
| 平板横屏 | 1024-1280px | P2 |
| 桌面 | > 1280px | ✅ 已适配 |

---

## 3. 技术方案概要

### 3.1 布局策略

```css
/* 移动优先断点 */
/* 手机 */
@media (max-width: 640px) {
  .video-studio {
    flex-direction: column;
    /* GridWorkflow 和 Preview 堆叠 */
  }
}

/* 平板 */
@media (min-width: 641px) and (max-width: 1024px) {
  .video-studio {
    grid-template-columns: 1fr 1fr;
  }
}

/* 桌面 */
@media (min-width: 1025px) {
  /* 保持现有布局 */
}
```

### 3.2 组件改造要点

1. **GridWorkflow**: 步骤向导改为全屏模态或分页
2. **VideoPreview**: 底部固定/可展开
3. **TaskList**: 底部抽屉
4. **导航**: 底部 Tab Bar

### 3.3 触摸优化

```css
/* 最小触摸目标 44x44px */
.btn-touch {
  min-height: 44px;
  min-width: 44px;
  padding: 12px 16px;
}

/* 滑动手势支持 */
.swipeable {
  touch-action: pan-x;
}
```

---

## 4. 实施路线

### Phase 1: 布局重构 (Week 1)
- Tailwind 响应式类
- VideoStudio 移动布局
- MainLayout 移动优化

### Phase 2: 组件适配 (Week 2)
- GridWorkflow 移动模式
- 触摸区域优化
- 表单交互优化

### Phase 3: 专属优化 (Week 3)
- 底部导航栏
- 手势交互
- 性能优化（图片压缩）

### Phase 4: PWA（可选）(Week 4)
- Service Worker
- 离线支持
- 安装提示

---

## 5. 验收标准

- [ ] iPhone 14 Pro (390px) 完全可用
- [ ] iPad (768px) 布局合理
- [ ] 触摸目标 >= 44px
- [ ] 无横向滚动条
- [ ] Lighthouse 移动端评分 > 70

---

**详细设计文档待 v1.2 完成后补充**

---

**作者**: AI Planner  
**最后更新**: 2026-01-07


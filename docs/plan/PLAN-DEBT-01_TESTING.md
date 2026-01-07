# PLAN-DEBT-01: 测试体系建设

**类型**: 技术债务清理  
**优先级**: P0  
**预估工时**: 15-20 天  
**状态**: 📝 规划中  

---

## 1. 概述

### 1.1 背景

代码审查报告显示测试覆盖率为 **0%**，这是重大技术风险：
- `backend/tests/` 目录存在但为空
- `frontend/` 无测试目录
- 无 CI/CD 测试流程

### 1.2 目标

- 后端单元测试覆盖率 > 70%
- 前端组件测试覆盖关键路径
- E2E 测试覆盖核心工作流
- CI 自动化测试

---

## 2. 测试策略

### 2.1 测试金字塔

```
        ▲
       /E2E\           5-10 个关键流程
      /─────\
     / 集成  \         20-30 个 API 测试
    /─────────\
   /   单元    \       100+ 个函数/组件测试
  /─────────────\
```

### 2.2 技术选型

| 层级 | 后端 | 前端 |
|------|------|------|
| 单元测试 | pytest + pytest-asyncio | Vitest + React Testing Library |
| 集成测试 | pytest + httpx | MSW (Mock Service Worker) |
| E2E 测试 | - | Playwright |
| 覆盖率 | pytest-cov | c8/istanbul |

---

## 3. 后端测试

### 3.1 目录结构

```
backend/
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # 共享 fixtures
│   ├── unit/
│   │   ├── test_ai_service.py
│   │   ├── test_video_service.py
│   │   ├── test_workflow_service.py
│   │   └── test_auth.py
│   ├── integration/
│   │   ├── test_routes_ai.py
│   │   ├── test_routes_video.py
│   │   └── test_routes_workflow.py
│   └── fixtures/
│       ├── mock_responses.py
│       └── sample_data.py
```

### 3.2 关键测试用例

#### 3.2.1 Services 单元测试

```python
# tests/unit/test_ai_service.py
import pytest
from unittest.mock import AsyncMock, patch

from app.services.ai_service import analyze_text, APIError
from app.schemas.ai import AnalyzeRequest


@pytest.fixture
def mock_settings():
    """模拟配置"""
    from app.core.config import Settings
    return Settings(
        ai_gateway_base_url="https://mock-api.test",
        ai_gateway_api_key="test-key",
        text_timeout_sec=10,
    )


class TestAnalyzeText:
    """测试 analyze_text 函数"""
    
    @pytest.mark.asyncio
    async def test_success(self, mock_settings):
        """正常响应"""
        payload = AnalyzeRequest(prompt="Hello")
        
        mock_response = {
            "choices": [{"message": {"content": "World"}}]
        }
        
        with patch("app.services.ai_service.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=MockResponse(200, mock_response)
            )
            
            result = await analyze_text(payload, None, mock_settings)
            assert result == "World"
    
    @pytest.mark.asyncio
    async def test_empty_prompt_raises(self, mock_settings):
        """空 prompt 报错"""
        payload = AnalyzeRequest(prompt="")
        
        with pytest.raises(APIError) as exc:
            await analyze_text(payload, None, mock_settings)
        
        assert exc.value.code == "BAD_REQUEST"
    
    @pytest.mark.asyncio
    async def test_timeout_error(self, mock_settings):
        """超时处理"""
        import httpx
        
        payload = AnalyzeRequest(prompt="Hello")
        
        with patch("app.services.ai_service.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=httpx.TimeoutException("Timeout")
            )
            
            with pytest.raises(APIError) as exc:
                await analyze_text(payload, None, mock_settings)
            
            assert exc.value.code == "TIMEOUT"
            assert exc.value.status_code == 504


class MockResponse:
    def __init__(self, status_code: int, json_data: dict):
        self.status_code = status_code
        self._json = json_data
    
    def json(self):
        return self._json
```

#### 3.2.2 Routes 集成测试

```python
# tests/integration/test_routes_workflow.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from app.main import app


@pytest.fixture
def client():
    """测试客户端"""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """模拟认证 headers"""
    return {"Authorization": "Bearer test-token"}


class TestConceptEndpoint:
    """测试 /concept 端点"""
    
    def test_missing_style(self, client, auth_headers):
        """缺少 style 参数"""
        with patch("app.core.auth.require_user", return_value="user-123"):
            response = client.post(
                "/api/v1/concept",
                json={"plot": "A story", "aspect_ratio": "16:9"},
                headers=auth_headers,
            )
        
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "BAD_REQUEST"
    
    def test_invalid_aspect_ratio(self, client, auth_headers):
        """无效的 aspect_ratio"""
        with patch("app.core.auth.require_user", return_value="user-123"):
            response = client.post(
                "/api/v1/concept",
                json={"style": "Anime", "plot": "A story", "aspect_ratio": "4:3"},
                headers=auth_headers,
            )
        
        assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_success(self, client, auth_headers):
        """成功生成概念图"""
        with patch("app.core.auth.require_user", return_value="user-123"):
            with patch("app.services.ai_service.generate_image") as mock_gen:
                mock_gen.return_value = [{"url": "https://example.com/image.png"}]
                
                response = client.post(
                    "/api/v1/concept",
                    json={
                        "style": "Anime style",
                        "plot": "A girl under cherry blossoms",
                        "aspect_ratio": "16:9",
                    },
                    headers=auth_headers,
                )
        
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert "concept_image_url" in data["data"]
```

### 3.3 conftest.py 配置

```python
# tests/conftest.py
import pytest
from unittest.mock import patch


@pytest.fixture(autouse=True)
def mock_supabase_jwt():
    """全局 mock JWT 验证"""
    with patch("app.core.auth._decode_supabase_jwt") as mock:
        mock.return_value = {"sub": "test-user-id"}
        yield mock


@pytest.fixture
def mock_env(monkeypatch):
    """设置测试环境变量"""
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("AI_GATEWAY_API_KEY", "test-key")
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "test-secret")
```

---

## 4. 前端测试

### 4.1 目录结构

```
frontend/
├── src/
│   └── ... 
├── tests/
│   ├── setup.ts
│   ├── unit/
│   │   ├── components/
│   │   │   ├── GridWorkflow.test.tsx
│   │   │   ├── TaskList.test.tsx
│   │   │   └── VideoPreview.test.tsx
│   │   └── hooks/
│   │       └── useWorkflowPersistence.test.ts
│   ├── integration/
│   │   └── videoService.test.ts
│   └── e2e/
│       └── workflow.spec.ts
├── vitest.config.ts
└── playwright.config.ts
```

### 4.2 Vitest 配置

```typescript
// frontend/vitest.config.ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./tests/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],
      exclude: ['node_modules', 'tests'],
    },
  },
});
```

### 4.3 组件测试示例

```tsx
// tests/unit/components/GridWorkflow.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { GridWorkflow } from '../../../src/components/video/GridWorkflow';
import { videoService } from '../../../src/services/videoService';

// Mock videoService
vi.mock('../../../src/services/videoService');

describe('GridWorkflow', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('应该渲染初始表单', () => {
    render(<GridWorkflow />);
    
    expect(screen.getByPlaceholderText(/剧情片段/i)).toBeInTheDocument();
    expect(screen.getByText(/生成概念图/i)).toBeInTheDocument();
  });

  it('空 plot 时应显示错误', async () => {
    render(<GridWorkflow />);
    
    const button = screen.getByText(/生成概念图/i);
    fireEvent.click(button);
    
    await waitFor(() => {
      expect(screen.getByText(/不能为空/i)).toBeInTheDocument();
    });
  });

  it('成功生成概念图后应进入下一步', async () => {
    vi.mocked(videoService.generateConcept).mockResolvedValue({
      concept_prompt: 'Test prompt',
      concept_image_url: 'https://example.com/image.png',
    });

    render(<GridWorkflow />);
    
    // 填写表单
    const plotInput = screen.getByPlaceholderText(/剧情片段/i);
    fireEvent.change(plotInput, { target: { value: 'A test story' } });
    
    const button = screen.getByText(/生成概念图/i);
    fireEvent.click(button);
    
    await waitFor(() => {
      expect(screen.getByText(/概念图/i)).toBeInTheDocument();
      expect(screen.getByText(/下一步/i)).toBeInTheDocument();
    });
  });
});
```

### 4.4 E2E 测试 (Playwright)

```typescript
// tests/e2e/workflow.spec.ts
import { test, expect } from '@playwright/test';

test.describe('视频工作流', () => {
  test.beforeEach(async ({ page }) => {
    // Mock 认证
    await page.addInitScript(() => {
      localStorage.setItem('supabase.auth.token', JSON.stringify({
        access_token: 'test-token',
        user: { id: 'test-user' },
      }));
    });
    
    await page.goto('/video');
  });

  test('完整工作流', async ({ page }) => {
    // Step 1: 输入
    await page.fill('textarea[placeholder*="剧情"]', '樱花树下的少女');
    await page.click('button:has-text("生成概念图")');
    
    // 等待 Step 2
    await expect(page.locator('text=概念图')).toBeVisible({ timeout: 30000 });
    await page.click('button:has-text("下一步")');
    
    // Step 3: 分镜
    await expect(page.locator('text=编辑分镜')).toBeVisible();
    await page.click('button:has-text("生成九宫格")');
    
    // 等待九宫格图片
    await expect(page.locator('img[alt*="Storyboard"]')).toBeVisible({ timeout: 30000 });
    
    // ... 继续后续步骤
  });

  test('刷新后恢复状态', async ({ page }) => {
    // 填写并进入第二步
    await page.fill('textarea[placeholder*="剧情"]', '测试剧情');
    await page.click('button:has-text("生成概念图")');
    await expect(page.locator('text=概念图')).toBeVisible({ timeout: 30000 });
    
    // 刷新页面
    await page.reload();
    
    // 验证状态恢复
    await expect(page.locator('text=概念图')).toBeVisible();
  });
});
```

---

## 5. CI/CD 集成

### 5.1 GitHub Actions

```yaml
# .github/workflows/test.yml
name: Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov
      
      - name: Run tests
        run: |
          cd backend
          pytest --cov=app --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: backend/coverage.xml

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      
      - name: Run unit tests
        run: |
          cd frontend
          npm run test:coverage
      
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: frontend/coverage/coverage-final.json

  e2e-tests:
    runs-on: ubuntu-latest
    needs: [backend-tests, frontend-tests]
    steps:
      - uses: actions/checkout@v4
      
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      
      - name: Install Playwright
        run: npx playwright install --with-deps
      
      - name: Run E2E tests
        run: |
          cd frontend
          npm run test:e2e
      
      - uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: playwright-report
          path: frontend/playwright-report
```

---

## 6. 实施计划

### Phase 1: 后端单元测试 (Day 1-5)
- pytest 环境搭建
- Services 测试 (20+ 用例)
- Schemas 测试 (10+ 用例)
- Auth 测试 (10+ 用例)

### Phase 2: 后端集成测试 (Day 6-8)
- Routes 测试 (20+ 用例)
- Mock 外部服务
- 覆盖率达标

### Phase 3: 前端测试 (Day 9-13)
- Vitest 环境搭建
- 组件测试 (15+ 用例)
- Hooks 测试 (5+ 用例)
- 集成测试

### Phase 4: E2E 与 CI (Day 14-15)
- Playwright 配置
- 关键流程测试 (5+ 场景)
- GitHub Actions 配置
- 文档更新

---

## 7. 验收标准

- [ ] 后端测试覆盖率 > 70%
- [ ] 前端测试覆盖率 > 60%
- [ ] E2E 覆盖核心工作流
- [ ] CI 自动运行所有测试
- [ ] PR 合并前测试必须通过

---

**作者**: AI Planner  
**最后更新**: 2026-01-07


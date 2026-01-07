# PLAN-DEBT-02: API 文档自动化

**类型**: 技术债务清理  
**优先级**: P1  
**预估工时**: 3-5 天  
**状态**: 📝 规划中  

---

## 1. 概述

### 1.1 背景

当前 API 文档存在问题：
- FastAPI 自动生成的 Swagger 缺少详细描述
- 无请求/响应示例
- Schemas 缺少字段说明
- 无版本管理

### 1.2 目标

- 完善 OpenAPI 规范
- 自动生成美观的文档
- 提供交互式 API 测试
- 文档版本化

---

## 2. 技术方案

### 2.1 OpenAPI 规范完善

#### 2.1.1 Schemas 添加示例

```python
# backend/app/schemas/workflow.py
from pydantic import BaseModel, Field

class ConceptRequest(BaseModel):
    """概念图生成请求"""
    
    style: str = Field(
        ...,
        description="视觉风格描述",
        example="Anime style, OLM studio, high detail"
    )
    plot: str = Field(
        ...,
        description="剧情片段描述",
        example="樱花树下，一位少女仰望天空，花瓣随风飘落"
    )
    aspect_ratio: str = Field(
        "16:9",
        description="画面比例",
        example="16:9"
    )
    anchors: dict | None = Field(
        None,
        description="视觉锚点",
        example={
            "character": {"text": "黑发少女，穿白色连衣裙"},
            "environment": {"text": "日本传统庭院"}
        }
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "style": "Anime style, Studio Ghibli",
                    "plot": "少女在花田中奔跑",
                    "aspect_ratio": "16:9",
                }
            ]
        }
    }
```

#### 2.1.2 路由添加文档

```python
# backend/app/api/routes/workflow.py
from fastapi import APIRouter

router = APIRouter(
    prefix="/api/v1",
    tags=["Workflow"],
    responses={
        401: {"description": "未授权"},
        429: {"description": "请求过于频繁"},
    }
)


@router.post(
    "/concept",
    summary="生成概念图",
    description="""
    ## 工作流 Step 1: 概念图生成
    
    根据风格和剧情生成概念图，用于确定整体视觉方向。
    
    ### 参数说明
    - **style**: 视觉风格，如 "Anime style, Studio Ghibli"
    - **plot**: 剧情片段，描述画面内容
    - **aspect_ratio**: 画面比例，支持 16:9 或 9:16
    - **anchors**: 可选的视觉锚点（角色、场景、道具）
    
    ### 返回
    - **concept_prompt**: 生成使用的 prompt
    - **concept_image_url**: 概念图 URL
    """,
    response_model=ConceptResponse,
    responses={
        200: {
            "description": "成功生成概念图",
            "content": {
                "application/json": {
                    "example": {
                        "ok": True,
                        "data": {
                            "concept_prompt": "Anime style...",
                            "concept_image_url": "https://..."
                        },
                        "error": None
                    }
                }
            }
        },
        400: {"description": "参数错误"},
        502: {"description": "上游服务异常"},
    }
)
async def concept(...):
    ...
```

### 2.2 自定义文档页面

```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi

app = FastAPI(
    title="GridWorkflow API",
    description="""
    # GridWorkflow API 文档
    
    AI 驱动的视频创作工作流 API。
    
    ## 工作流步骤
    
    1. **Concept** (`/concept`) - 生成概念图
    2. **Storyboard Plan** (`/storyboard/plan`) - 规划分镜
    3. **Storyboard Generate** (`/storyboard/generate`) - 生成九宫格
    4. **Video Prompt** (`/video/prompt`) - 生成视频 Prompt
    5. **Video Generate** (`/video/generate`) - 提交视频任务
    
    ## 认证
    
    所有 API 需要在 Header 中携带 Supabase JWT Token：
    ```
    Authorization: Bearer <token>
    ```
    """,
    version="1.1.0",
    docs_url=None,  # 禁用默认
    redoc_url=None,
)


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="GridWorkflow API",
        swagger_favicon_url="/favicon.ico",
    )


@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url="/openapi.json",
        title="GridWorkflow API - ReDoc",
    )
```

### 2.3 导出 OpenAPI 规范

```python
# backend/scripts/export_openapi.py
"""导出 OpenAPI 规范到文件"""
import json
import yaml
from app.main import app

# 获取 OpenAPI schema
schema = app.openapi()

# 导出 JSON
with open("docs/api/openapi.json", "w") as f:
    json.dump(schema, f, indent=2)

# 导出 YAML
with open("docs/api/openapi.yaml", "w") as f:
    yaml.dump(schema, f, default_flow_style=False)

print("OpenAPI 规范已导出到 docs/api/")
```

### 2.4 生成静态文档 (可选)

```yaml
# 使用 Redocly 生成静态 HTML
# docs/redocly.yaml
extends:
  - recommended

apis:
  gridworkflow:
    root: openapi.yaml
    
theme:
  colors:
    primary:
      main: "#0061A4"
  typography:
    fontFamily: "Inter, sans-serif"
  logo:
    gutter: "16px"
```

```bash
# 生成静态文档
npx @redocly/cli build-docs docs/api/openapi.yaml -o docs/api/index.html
```

---

## 3. 实施计划

### Phase 1: Schemas 完善 (Day 1)

| 任务 | 工时 | 产出 |
|------|------|------|
| workflow.py 添加示例 | 2h | 4 个 Schema |
| video.py 添加示例 | 1h | 1 个 Schema |
| ai.py 添加示例 | 1h | 2 个 Schema |
| response.py 添加示例 | 0.5h | 2 个 Schema |

### Phase 2: 路由文档 (Day 2)

| 任务 | 工时 | 产出 |
|------|------|------|
| workflow.py 路由文档 | 2h | 4 个端点 |
| video.py 路由文档 | 1.5h | 2 个端点 |
| ai.py 路由文档 | 1h | 2 个端点 |
| media.py 路由文档 | 0.5h | 1 个端点 |

### Phase 3: 文档页面 (Day 3)

| 任务 | 工时 | 产出 |
|------|------|------|
| 自定义 Swagger UI | 2h | /docs |
| ReDoc 配置 | 1h | /redoc |
| 导出脚本 | 1h | openapi.json/yaml |

### Phase 4: 静态文档（可选）(Day 4-5)

| 任务 | 工时 | 产出 |
|------|------|------|
| Redocly 配置 | 2h | 静态 HTML |
| CI 自动生成 | 2h | GitHub Actions |
| 发布到 GitHub Pages | 2h | 公开文档 |

---

## 4. 验收标准

- [ ] 所有端点有详细描述
- [ ] 所有 Schema 有字段说明
- [ ] 请求/响应有示例
- [ ] /docs 页面可正常访问
- [ ] OpenAPI 规范可导出

---

## 5. 参考资料

- [FastAPI 文档](https://fastapi.tiangolo.com/tutorial/metadata/)
- [OpenAPI 规范](https://swagger.io/specification/)
- [Redocly CLI](https://redocly.com/docs/cli/)

---

**作者**: AI Planner  
**最后更新**: 2026-01-07


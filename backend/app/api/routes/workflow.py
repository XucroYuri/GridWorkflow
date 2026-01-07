from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from app.core.auth import require_user
from app.core.config import Settings, get_settings
from app.core.prompts import (
    build_anchor_context,
    build_concept_prompt,
    build_storyboard_plan_prompt,
    build_storyboard_plan_system,
    build_video_prompt_prompt,
    build_video_prompt_system,
)
from app.schemas.ai import AnalyzeRequest, GenerateImageRequest
from app.schemas.response import error_response, success_response
from app.schemas.workflow import (
    ConceptRequest,
    StoryboardGenerateRequest,
    StoryboardPlanRequest,
    VideoPromptRequest,
)
from app.services.ai_service import APIError, analyze_text, generate_image
from app.services.workflow_service import extract_first_image_url, select_reference_image

router = APIRouter(prefix="/api/v1", tags=["workflow"], dependencies=[Depends(require_user)])

ALLOWED_ASPECT_RATIOS = {"16:9", "9:16"}
ALLOWED_IMAGE_SIZES = {"1K", "2K", "4K"}
ALLOWED_DURATIONS = {10, 15, 25}

_UPSTREAM_MESSAGE = "\u4e0a\u6e38\u670d\u52a1\u5f02\u5e38\uff0c\u8bf7\u7a0d\u540e\u91cd\u8bd5\u3002"
_ASPECT_RATIO_MESSAGE = "aspect_ratio \u4ec5\u652f\u630116:9/9:16\u3002"
_IMAGE_SIZE_MESSAGE = "image_size \u4ec5\u652f\u63011K/2K/4K\u3002"
_DURATION_MESSAGE = "duration \u4ec5\u652f\u630110/15/25\u3002"
_FPS_MESSAGE = "fps \u5fc5\u987b\u5927\u4e8e0\u3002"


def _normalize_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _field_required_message(field_name: str) -> str:
    return f"{field_name} \u5b57\u6bb5\u4e0d\u80fd\u4e3a\u7a7a\u3002"


def _error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=error_response(code, message))


@router.post("/concept")
async def concept(
    payload: ConceptRequest,
    request: Request,
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    style = _normalize_text(payload.style)
    if not style:
        return _error_response(400, "BAD_REQUEST", _field_required_message("style"))
    plot = _normalize_text(payload.plot)
    if not plot:
        return _error_response(400, "BAD_REQUEST", _field_required_message("plot"))
    aspect_ratio = _normalize_text(payload.aspect_ratio)
    if not aspect_ratio:
        return _error_response(400, "BAD_REQUEST", _field_required_message("aspect_ratio"))
    if aspect_ratio not in ALLOWED_ASPECT_RATIOS:
        return _error_response(400, "BAD_REQUEST", _ASPECT_RATIO_MESSAGE)
    image_size = _normalize_text(payload.image_size) or "1K"
    if image_size not in ALLOWED_IMAGE_SIZES:
        return _error_response(400, "BAD_REQUEST", _IMAGE_SIZE_MESSAGE)

    concept_prompt = build_concept_prompt(style, plot, payload.anchors, aspect_ratio)
    reference_image = select_reference_image(payload.anchors)

    request.state.step = "workflow.concept"
    request.state.model = settings.default_image_model
    user_key = request.headers.get("x-user-gemini-key")
    try:
        result = await generate_image(
            GenerateImageRequest(
                prompt=concept_prompt,
                image_size=image_size,
                aspect_ratio=aspect_ratio,
                image=reference_image,
                response_format="url",
            ),
            user_key,
            settings,
        )
    except APIError as exc:
        return _error_response(exc.status_code, exc.code, exc.message)

    image_url = extract_first_image_url(result)
    if not image_url:
        return _error_response(502, "UPSTREAM_ERROR", _UPSTREAM_MESSAGE)

    return JSONResponse(
        status_code=200,
        content=success_response(
            {"concept_prompt": concept_prompt, "concept_image_url": image_url}
        ),
    )


@router.post("/storyboard/plan")
async def storyboard_plan(
    payload: StoryboardPlanRequest,
    request: Request,
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    style = _normalize_text(payload.style)
    if not style:
        return _error_response(400, "BAD_REQUEST", _field_required_message("style"))
    plot = _normalize_text(payload.plot)
    if not plot:
        return _error_response(400, "BAD_REQUEST", _field_required_message("plot"))
    output_language = _normalize_text(payload.output_language) or "zh-CN"
    concept_prompt = _normalize_text(payload.concept_prompt)
    concept_image_url = _normalize_text(payload.concept_image_url)

    system_instruction = build_storyboard_plan_system(output_language)
    prompt = build_storyboard_plan_prompt(
        style,
        plot,
        build_anchor_context(payload.anchors),
        concept_prompt,
        concept_image_url,
    )

    request.state.step = "workflow.storyboard_plan"
    request.state.model = settings.default_text_model
    user_key = request.headers.get("x-user-gemini-key")
    try:
        result = await analyze_text(
            AnalyzeRequest(prompt=prompt, system_instruction=system_instruction),
            user_key,
            settings,
        )
    except APIError as exc:
        return _error_response(exc.status_code, exc.code, exc.message)

    if not isinstance(result, str):
        return _error_response(502, "UPSTREAM_ERROR", _UPSTREAM_MESSAGE)
    storyboard_prompt = result.strip()
    if not storyboard_prompt:
        return _error_response(502, "UPSTREAM_ERROR", _UPSTREAM_MESSAGE)

    return JSONResponse(
        status_code=200, content=success_response({"storyboard_prompt": storyboard_prompt})
    )


@router.post("/storyboard/generate")
async def storyboard_generate(
    payload: StoryboardGenerateRequest,
    request: Request,
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    storyboard_prompt = _normalize_text(payload.storyboard_prompt)
    if not storyboard_prompt:
        return _error_response(
            400, "BAD_REQUEST", _field_required_message("storyboard_prompt")
        )
    aspect_ratio = _normalize_text(payload.aspect_ratio)
    if not aspect_ratio:
        return _error_response(400, "BAD_REQUEST", _field_required_message("aspect_ratio"))
    if aspect_ratio not in ALLOWED_ASPECT_RATIOS:
        return _error_response(400, "BAD_REQUEST", _ASPECT_RATIO_MESSAGE)
    image_size = _normalize_text(payload.image_size) or "1K"
    if image_size not in ALLOWED_IMAGE_SIZES:
        return _error_response(400, "BAD_REQUEST", _IMAGE_SIZE_MESSAGE)

    request.state.step = "workflow.storyboard_generate"
    request.state.model = settings.default_image_model
    user_key = request.headers.get("x-user-gemini-key")
    try:
        result = await generate_image(
            GenerateImageRequest(
                prompt=storyboard_prompt,
                image_size=image_size,
                aspect_ratio=aspect_ratio,
                image=_normalize_text(payload.reference_image_base64),
                response_format="url",
            ),
            user_key,
            settings,
        )
    except APIError as exc:
        return _error_response(exc.status_code, exc.code, exc.message)

    image_url = extract_first_image_url(result)
    if not image_url:
        return _error_response(502, "UPSTREAM_ERROR", _UPSTREAM_MESSAGE)

    return JSONResponse(
        status_code=200, content=success_response({"grid_image_url": image_url})
    )


@router.post("/video/prompt")
async def video_prompt(
    payload: VideoPromptRequest,
    request: Request,
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    storyboard_prompt = _normalize_text(payload.storyboard_prompt)
    if not storyboard_prompt:
        return _error_response(
            400, "BAD_REQUEST", _field_required_message("storyboard_prompt")
        )
    original_plot = _normalize_text(payload.original_plot)
    if not original_plot:
        return _error_response(400, "BAD_REQUEST", _field_required_message("original_plot"))
    if payload.duration not in ALLOWED_DURATIONS:
        return _error_response(400, "BAD_REQUEST", _DURATION_MESSAGE)
    if payload.fps <= 0:
        return _error_response(400, "BAD_REQUEST", _FPS_MESSAGE)

    output_language = _normalize_text(payload.output_language) or "zh-CN"
    system_instruction = build_video_prompt_system(
        payload.duration, payload.fps, output_language
    )
    prompt = build_video_prompt_prompt(storyboard_prompt, original_plot)

    request.state.step = "workflow.video_prompt"
    request.state.model = settings.default_text_model
    user_key = request.headers.get("x-user-gemini-key")
    try:
        result = await analyze_text(
            AnalyzeRequest(prompt=prompt, system_instruction=system_instruction),
            user_key,
            settings,
        )
    except APIError as exc:
        return _error_response(exc.status_code, exc.code, exc.message)

    if not isinstance(result, str):
        return _error_response(502, "UPSTREAM_ERROR", _UPSTREAM_MESSAGE)
    video_prompt_text = result.strip()
    if not video_prompt_text:
        return _error_response(502, "UPSTREAM_ERROR", _UPSTREAM_MESSAGE)

    return JSONResponse(
        status_code=200, content=success_response({"video_prompt": video_prompt_text})
    )

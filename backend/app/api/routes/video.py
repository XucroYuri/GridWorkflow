import logging
import math

from fastapi import APIRouter, Depends, Header, Query, Request
from fastapi.responses import JSONResponse

from app.core.auth import require_user, require_user_or_allowlisted
from app.core.config import Settings, get_settings
from app.schemas.response import error_response, success_response
from app.schemas.video import VideoGenerateRequest
from app.services.video_service import (
    UpstreamServiceError,
    extract_video_url,
    get_video_provider_registry,
    is_valid_task_id,
    mask_task_id,
    normalize_status,
    sanitize_error_message,
)

logger = logging.getLogger("gridworkflow")

# 仅处理视频生成和状态查询，Step1-Step4 由 workflow.py 处理
router = APIRouter(prefix="/api/v1/video", tags=["video"])

ALLOWED_MODELS = {"sora-2", "sora-2-pro"}
ALLOWED_DURATIONS = {10, 15, 25}
ALLOWED_ASPECT_RATIOS = {"16:9", "9:16"}


def _get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")


@router.post("/generate", dependencies=[Depends(require_user)])
async def generate_video(
    payload: VideoGenerateRequest,
    request: Request,
    settings: Settings = Depends(get_settings),
    x_user_gemini_key: str | None = Header(default=None, alias="x-user-gemini-key"),
) -> JSONResponse:
    if payload.model not in ALLOWED_MODELS:
        return JSONResponse(
            status_code=400,
            content=error_response("BAD_REQUEST", "model 参数不支持。"),
        )
    if payload.duration not in ALLOWED_DURATIONS:
        return JSONResponse(
            status_code=400,
            content=error_response("BAD_REQUEST", "duration 仅支持 10/15/25。"),
        )
    if payload.aspect_ratio not in ALLOWED_ASPECT_RATIOS:
        return JSONResponse(
            status_code=400,
            content=error_response("BAD_REQUEST", "aspect_ratio 仅支持 16:9/9:16。"),
        )
    if payload.duration == 25 and payload.model != "sora-2-pro":
        return JSONResponse(
            status_code=400,
            content=error_response("BAD_REQUEST", "duration=25 仅支持 sora-2-pro。"),
        )
    if payload.hd and payload.model != "sora-2-pro":
        return JSONResponse(
            status_code=400,
            content=error_response("BAD_REQUEST", "hd 仅支持 sora-2-pro。"),
        )
    if not (x_user_gemini_key or settings.ai_gateway_api_key):
        return JSONResponse(
            status_code=401,
            content=error_response("UNAUTHORIZED", "缺少上游 API Key。"),
        )

    registry = get_video_provider_registry(settings)
    provider = registry.get(payload.provider)
    if provider is None:
        return JSONResponse(
            status_code=400,
            content=error_response("BAD_REQUEST", "provider 不支持。"),
        )

    upstream_payload = {
        "prompt": payload.prompt,
        "model": payload.model,
        "aspect_ratio": payload.aspect_ratio,
        "hd": payload.hd,
        "duration": str(payload.duration),
    }
    if payload.images:
        upstream_payload["images"] = payload.images

    logger.info(
        "video generate request request_id=%s model=%s duration=%s aspect_ratio=%s step=video_generate",
        _get_request_id(request),
        payload.model,
        payload.duration,
        payload.aspect_ratio,
    )

    try:
        result = await provider.generate(upstream_payload, x_user_gemini_key)
    except UpstreamServiceError as exc:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response(exc.code, exc.message),
        )

    task_id = result.get("task_id") if isinstance(result, dict) else None
    if not task_id or not is_valid_task_id(task_id):
        logger.warning(
            "video generate invalid task_id request_id=%s task_id=%s step=video_generate",
            _get_request_id(request),
            mask_task_id(str(task_id or "")),
        )
        return JSONResponse(
            status_code=502,
            content=error_response("UPSTREAM_ERROR", "上游返回异常，请稍后重试。"),
        )

    return JSONResponse(
        status_code=200,
        content=success_response({"task_id": task_id}),
    )


@router.get("/status/{task_id}", dependencies=[Depends(require_user_or_allowlisted)])
async def video_status(
    task_id: str,
    request: Request,
    settings: Settings = Depends(get_settings),
    provider: str = Query(default="t8star"),
    x_user_gemini_key: str | None = Header(default=None, alias="x-user-gemini-key"),
) -> JSONResponse:
    if not is_valid_task_id(task_id):
        return JSONResponse(
            status_code=400,
            content=error_response("BAD_REQUEST", "task_id 格式不正确。"),
        )
    if not (x_user_gemini_key or settings.ai_gateway_api_key):
        return JSONResponse(
            status_code=401,
            content=error_response("UNAUTHORIZED", "缺少上游 API Key。"),
        )

    registry = get_video_provider_registry(settings)
    provider_instance = registry.get(provider.lower())
    if provider_instance is None:
        return JSONResponse(
            status_code=400,
            content=error_response("BAD_REQUEST", "provider 不支持。"),
        )

    logger.info(
        "video status request request_id=%s task_id=%s step=video_status",
        _get_request_id(request),
        mask_task_id(task_id),
    )

    try:
        result = await provider_instance.status(task_id, x_user_gemini_key)
    except UpstreamServiceError as exc:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response(exc.code, exc.message),
        )

    status = normalize_status(result.get("status") if isinstance(result, dict) else None)
    fail_reason = None
    if isinstance(result, dict):
        fail_reason = sanitize_error_message(result.get("fail_reason"))
    if status != "failed":
        fail_reason = None
    video_url = extract_video_url(result.get("data") if isinstance(result, dict) else None)

    poll_interval_ms = max(settings.video_poll_interval_ms, 3000)
    headers = {
        "X-Poll-Interval-Ms": str(poll_interval_ms),
        "Retry-After": str(max(1, math.ceil(poll_interval_ms / 1000))),
    }
    return JSONResponse(
        status_code=200,
        content=success_response(
            {
                "task_id": task_id,
                "provider": provider.lower(),
                "status": status,
                "video_url": video_url,
                "error_message": fail_reason,
            }
        ),
        headers=headers,
    )

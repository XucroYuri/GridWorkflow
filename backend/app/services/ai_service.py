from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass
from typing import Any, Optional

import httpx

from app.core.config import Settings
from app.schemas.ai import AnalyzeRequest, GenerateImageRequest

EMPTY_1X1_PNG = bytes(
    [
        137,
        80,
        78,
        71,
        13,
        10,
        26,
        10,
        0,
        0,
        0,
        13,
        73,
        72,
        68,
        82,
        0,
        0,
        0,
        1,
        0,
        0,
        0,
        1,
        8,
        6,
        0,
        0,
        0,
        31,
        21,
        196,
        137,
        0,
        0,
        0,
        10,
        73,
        68,
        65,
        84,
        120,
        156,
        99,
        96,
        0,
        0,
        0,
        2,
        0,
        1,
        244,
        113,
        100,
        251,
        0,
        0,
        0,
        0,
        73,
        69,
        78,
        68,
        174,
        66,
        96,
        130,
    ]
)


@dataclass
class APIError(Exception):
    code: str
    message: str
    status_code: int = 400


def _resolve_api_key(settings: Settings, user_key: Optional[str]) -> str:
    trimmed = (user_key or "").strip()
    if trimmed:
        return trimmed
    if settings.ai_gateway_api_key:
        return settings.ai_gateway_api_key
    raise APIError(code="UNAUTHORIZED", message="API Key 未配置", status_code=401)


def _map_upstream_error(status_code: int) -> APIError:
    if status_code == 400:
        return APIError(code="BAD_REQUEST", message="请求参数错误", status_code=400)
    if status_code == 401:
        return APIError(code="UNAUTHORIZED", message="鉴权失败，请检查 API Key", status_code=401)
    if status_code == 403:
        return APIError(code="FORBIDDEN", message="权限不足或策略拒绝", status_code=403)
    if status_code == 404:
        return APIError(code="NOT_FOUND", message="资源不存在", status_code=404)
    if status_code in {408, 504}:
        return APIError(code="TIMEOUT", message="上游服务超时，请稍后重试", status_code=504)
    if status_code == 429:
        return APIError(code="RATE_LIMITED", message="请求过于频繁，请稍后重试", status_code=429)
    if 500 <= status_code:
        return APIError(code="UPSTREAM_ERROR", message="上游服务异常，请稍后重试", status_code=502)
    return APIError(code="UPSTREAM_ERROR", message="上游服务异常，请稍后重试", status_code=502)


def _strip_base64_prefix(raw: str) -> str:
    if raw.startswith("data:"):
        comma_index = raw.find(",")
        if comma_index >= 0:
            return raw[comma_index + 1 :]
    return raw


def _decode_image_base64(raw: Optional[str], max_bytes: int) -> bytes:
    if not raw:
        return EMPTY_1X1_PNG
    stripped = _strip_base64_prefix(raw.strip())
    if not stripped:
        return EMPTY_1X1_PNG
    approx_bytes = (len(stripped) * 3) // 4
    if approx_bytes > max_bytes:
        raise APIError(code="BAD_REQUEST", message="图片过大，超出限制", status_code=400)
    try:
        decoded = base64.b64decode(stripped, validate=True)
    except binascii.Error as exc:
        raise APIError(code="BAD_REQUEST", message="图片编码无效", status_code=400) from exc
    if len(decoded) > max_bytes:
        raise APIError(code="BAD_REQUEST", message="图片过大，超出限制", status_code=400)
    return decoded


def _normalize_base_url(settings: Settings) -> str:
    return settings.ai_gateway_base_url.rstrip("/")


def _build_response_format(value: Optional[str]) -> Optional[dict]:
    if not value:
        return None
    if value.lower() == "json":
        return {"type": "json_object"}
    return None


def _validate_image_response_format(value: Optional[str]) -> str:
    if not value:
        return "url"
    normalized = value.lower()
    if normalized in {"url", "b64_json"}:
        return normalized
    raise APIError(code="BAD_REQUEST", message="response_format 不支持", status_code=400)


def _extract_chat_content(payload: dict) -> Any:
    choices = payload.get("choices")
    if isinstance(choices, list) and choices:
        message = choices[0].get("message") if isinstance(choices[0], dict) else None
        if isinstance(message, dict) and "content" in message:
            return message.get("content")
    return payload


def _ensure_prompt(prompt: str) -> None:
    if not prompt or not prompt.strip():
        raise APIError(code="BAD_REQUEST", message="prompt 不能为空", status_code=400)


async def analyze_text(
    payload: AnalyzeRequest, user_key: Optional[str], settings: Settings
) -> Any:
    _ensure_prompt(payload.prompt)
    api_key = _resolve_api_key(settings, user_key)
    model = payload.model or settings.default_text_model
    messages = []
    if payload.system_instruction:
        messages.append({"role": "system", "content": payload.system_instruction})
    messages.append({"role": "user", "content": payload.prompt})

    body: dict[str, Any] = {"model": model, "messages": messages}
    response_format = _build_response_format(payload.response_format)
    if response_format:
        body["response_format"] = response_format

    try:
        async with httpx.AsyncClient(timeout=settings.text_timeout_sec) as client:
            resp = await client.post(
                f"{_normalize_base_url(settings)}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json=body,
            )
    except httpx.TimeoutException as exc:
        raise APIError(code="TIMEOUT", message="上游服务超时，请稍后重试", status_code=504) from exc
    except httpx.RequestError as exc:
        raise APIError(code="UPSTREAM_ERROR", message="上游服务异常，请稍后重试", status_code=502) from exc

    if resp.status_code >= 400:
        raise _map_upstream_error(resp.status_code)

    data = resp.json()
    return _extract_chat_content(data)


async def generate_image(
    payload: GenerateImageRequest, user_key: Optional[str], settings: Settings
) -> Any:
    _ensure_prompt(payload.prompt)
    api_key = _resolve_api_key(settings, user_key)
    model = payload.model or settings.default_image_model
    response_format = _validate_image_response_format(payload.response_format)
    image_bytes = _decode_image_base64(payload.image, settings.max_image_base64_bytes)

    data: dict[str, Any] = {
        "model": model,
        "prompt": payload.prompt,
        "response_format": response_format,
    }
    if payload.aspect_ratio:
        data["aspect_ratio"] = payload.aspect_ratio
    if payload.image_size:
        data["image_size"] = payload.image_size

    files = {"image": ("reference.png", image_bytes, "image/png")}

    try:
        async with httpx.AsyncClient(timeout=settings.image_timeout_sec) as client:
            resp = await client.post(
                f"{_normalize_base_url(settings)}/images/edits",
                headers={"Authorization": f"Bearer {api_key}"},
                data=data,
                files=files,
            )
    except httpx.TimeoutException as exc:
        raise APIError(code="TIMEOUT", message="上游服务超时，请稍后重试", status_code=504) from exc
    except httpx.RequestError as exc:
        raise APIError(code="UPSTREAM_ERROR", message="上游服务异常，请稍后重试", status_code=502) from exc

    if resp.status_code >= 400:
        raise _map_upstream_error(resp.status_code)

    data = resp.json()
    return data.get("data") if isinstance(data, dict) and "data" in data else data

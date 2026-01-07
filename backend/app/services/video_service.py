from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import re
from typing import Any, Optional

import httpx

from app.core.config import Settings, get_settings


TASK_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9:_-]{7,127}$")
STATUS_MAP = {
    "NOT_START": "queued",
    "IN_PROGRESS": "running",
    "SUCCESS": "succeeded",
    "FAILURE": "failed",
}


@dataclass(frozen=True)
class UpstreamServiceError(Exception):
    code: str
    message: str
    status_code: int


def is_valid_task_id(task_id: str) -> bool:
    return bool(TASK_ID_PATTERN.match(task_id or ""))


def mask_task_id(task_id: str) -> str:
    if not task_id:
        return ""
    if len(task_id) <= 10:
        return f"{task_id[:3]}***"
    return f"{task_id[:6]}***{task_id[-4:]}"


def normalize_status(status: Optional[str]) -> str:
    if not status:
        return "queued"
    return STATUS_MAP.get(status.upper(), "running")


def sanitize_error_message(message: Optional[str], limit: int = 200) -> Optional[str]:
    if not message:
        return None
    sanitized = " ".join(message.split())
    return sanitized[:limit]


def extract_video_url(data: Any) -> Optional[str]:
    if isinstance(data, dict):
        value = data.get("output") or data.get("video_url")
        if isinstance(value, str) and value.strip():
            return value
    return None


def _map_status_code(status_code: int) -> tuple[str, int]:
    if status_code == 401:
        return "UNAUTHORIZED", 401
    if status_code == 403:
        return "FORBIDDEN", 403
    if status_code == 404:
        return "NOT_FOUND", 404
    if status_code == 429:
        return "RATE_LIMITED", 429
    if status_code in (408, 504):
        return "TIMEOUT", 504
    return "UPSTREAM_ERROR", 502


class T8StarVideoProvider:
    def __init__(self, base_url: str, api_key: str, timeout_seconds: float = 180.0):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def _headers(self, user_api_key: Optional[str]) -> dict:
        key = (user_api_key or "").strip() or self.api_key
        headers = {"Content-Type": "application/json"}
        if key:
            headers["Authorization"] = f"Bearer {key}"
        return headers

    async def generate(self, payload: dict, user_api_key: Optional[str]) -> dict:
        url = f"{self.base_url}/v2/videos/generations"
        return await _request_json(
            "POST",
            url,
            headers=self._headers(user_api_key),
            payload=payload,
            timeout_seconds=self.timeout_seconds,
        )

    async def status(self, task_id: str, user_api_key: Optional[str]) -> dict:
        url = f"{self.base_url}/v2/videos/generations/{task_id}"
        return await _request_json(
            "GET",
            url,
            headers=self._headers(user_api_key),
            timeout_seconds=self.timeout_seconds,
        )


class VideoProviderRegistry:
    def __init__(self, providers: dict[str, T8StarVideoProvider]):
        self._providers = providers

    def get(self, provider: str) -> Optional[T8StarVideoProvider]:
        return self._providers.get(provider)


async def _request_json(
    method: str,
    url: str,
    headers: dict,
    payload: Optional[dict] = None,
    timeout_seconds: float = 180.0,
) -> dict:
    try:
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            response = await client.request(method, url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException as exc:
        raise UpstreamServiceError(
            code="TIMEOUT",
            message="上游服务超时，请稍后重试。",
            status_code=504,
        ) from exc
    except httpx.HTTPStatusError as exc:
        code, status_code = _map_status_code(exc.response.status_code)
        raise UpstreamServiceError(
            code=code,
            message="上游服务错误，请稍后重试。",
            status_code=status_code,
        ) from exc
    except (httpx.RequestError, ValueError) as exc:
        raise UpstreamServiceError(
            code="UPSTREAM_ERROR",
            message="上游服务不可用，请稍后重试。",
            status_code=502,
        ) from exc


@lru_cache
def get_video_provider_registry(settings: Optional[Settings] = None) -> VideoProviderRegistry:
    settings = settings or get_settings()
    providers = {
        "t8star": T8StarVideoProvider(
            base_url=settings.ai_gateway_base_url,
            api_key=settings.ai_gateway_api_key,
            timeout_seconds=settings.video_timeout_sec,
        )
    }
    return VideoProviderRegistry(providers)

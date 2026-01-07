from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import os
import re
from typing import Optional
from uuid import uuid4

from app.core.config import Settings

try:
    from qcloud_cos import CosConfig, CosS3Client
except ImportError as exc:  # pragma: no cover - runtime dependency
    CosConfig = None
    CosS3Client = None
    _COS_IMPORT_ERROR = exc
else:
    _COS_IMPORT_ERROR = None


class COSConfigError(RuntimeError):
    pass


class COSUploadError(RuntimeError):
    pass


class MediaValidationError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class UploadResult:
    url: str
    key: str
    signed: bool
    expires_in: Optional[int] = None


IMAGE_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
}

VIDEO_CONTENT_TYPES = {
    "video/mp4": ".mp4",
    "video/quicktime": ".mov",
    "video/webm": ".webm",
    "video/x-msvideo": ".avi",
}

CONTENT_TYPE_ALIASES = {
    "image/jpg": "image/jpeg",
    "image/pjpeg": "image/jpeg",
}

COMPARE_TYPE_ALIASES = {
    "video/quicktime": "video/mp4",
}


def _normalize_content_type(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    trimmed = value.split(";", 1)[0].strip()
    return CONTENT_TYPE_ALIASES.get(trimmed, trimmed)


def _detect_image_content_type(head: bytes) -> Optional[str]:
    if head.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if head[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if head.startswith(b"RIFF") and head[8:12] == b"WEBP":
        return "image/webp"
    return None


def _detect_video_content_type(head: bytes) -> Optional[str]:
    if len(head) >= 12 and head[4:8] == b"ftyp":
        return "video/mp4"
    if head.startswith(b"\x1A\x45\xDF\xA3"):
        return "video/webm"
    if head.startswith(b"RIFF") and head[8:12] == b"AVI ":
        return "video/x-msvideo"
    return None


def detect_content_type(media_type: str, head: bytes) -> Optional[str]:
    if media_type == "image":
        return _detect_image_content_type(head)
    if media_type == "video":
        return _detect_video_content_type(head)
    return None


def validate_media(
    media_type: str, content_type: Optional[str], head: bytes
) -> str:
    if media_type not in {"image", "video"}:
        raise MediaValidationError("BAD_REQUEST", "media_type must be image or video")

    normalized = _normalize_content_type(content_type)
    compare_value = COMPARE_TYPE_ALIASES.get(normalized, normalized)
    inferred = detect_content_type(media_type, head)
    allowed = IMAGE_CONTENT_TYPES if media_type == "image" else VIDEO_CONTENT_TYPES

    if normalized in {None, "", "application/octet-stream"}:
        if not inferred:
            raise MediaValidationError("BAD_REQUEST", "unsupported media type")
        return inferred

    if normalized not in allowed:
        raise MediaValidationError("BAD_REQUEST", "unsupported media type")

    if inferred and compare_value != inferred:
        raise MediaValidationError("BAD_REQUEST", "media signature mismatch")

    return normalized


def sanitize_filename(filename: Optional[str]) -> str:
    if not filename:
        return "upload"
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", filename)
    return safe or "upload"


def build_object_key(
    prefix: str, media_type: str, filename: str, content_type: str
) -> str:
    safe_name = sanitize_filename(filename)
    ext = os.path.splitext(safe_name)[1].lower()
    allowed = IMAGE_CONTENT_TYPES if media_type == "image" else VIDEO_CONTENT_TYPES
    if ext not in allowed.values():
        ext = allowed.get(content_type, "")
    date_path = datetime.now(timezone.utc).strftime("%Y/%m/%d")
    name = f"{uuid4().hex}{ext}"
    clean_prefix = prefix.strip().strip("/")
    parts = [p for p in (clean_prefix, media_type, date_path, name) if p]
    return "/".join(parts)


def clamp_signed_ttl(seconds: int) -> int:
    if seconds <= 0:
        return 300
    return max(60, min(seconds, 3600))


class COSClient:
    def __init__(self, settings: Settings) -> None:
        if _COS_IMPORT_ERROR is not None:
            raise COSConfigError("cos sdk is not installed") from _COS_IMPORT_ERROR
        if not settings.cos_secret_id or not settings.cos_secret_key:
            raise COSConfigError("cos credentials are missing")
        if not settings.cos_bucket or not settings.cos_region:
            raise COSConfigError("cos bucket or region is missing")

        self._bucket = settings.cos_bucket
        self._signed_url = settings.cos_signed_url
        self._signed_url_ttl = clamp_signed_ttl(
            settings.cos_signed_url_ttl_seconds
        )

        config = CosConfig(
            Region=settings.cos_region,
            SecretId=settings.cos_secret_id,
            SecretKey=settings.cos_secret_key,
        )
        self._client = CosS3Client(config)

    def upload_fileobj(self, fileobj, key: str, content_type: str) -> None:
        try:
            self._client.upload_file_from_buffer(
                Bucket=self._bucket,
                Body=fileobj,
                Key=key,
                ContentType=content_type,
            )
        except Exception as exc:
            raise COSUploadError("cos upload failed") from exc

    def build_access_url(self, key: str) -> UploadResult:
        if self._signed_url:
            url = self._client.get_presigned_url(
                Method="GET",
                Bucket=self._bucket,
                Key=key,
                Expired=self._signed_url_ttl,
            )
            return UploadResult(
                url=url,
                key=key,
                signed=True,
                expires_in=self._signed_url_ttl,
            )

        url = self._client.get_object_url(Bucket=self._bucket, Key=key)
        return UploadResult(url=url, key=key, signed=False, expires_in=None)

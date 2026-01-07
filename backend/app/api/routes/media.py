import logging
import os
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import JSONResponse

from app.core.auth import require_user
from app.core.config import Settings, get_settings
from app.schemas.response import error_response, success_response
from app.storage.cos_client import (
    COSClient,
    COSConfigError,
    COSUploadError,
    MediaValidationError,
    build_object_key,
    validate_media,
)

logger = logging.getLogger("gridworkflow")

router = APIRouter(dependencies=[Depends(require_user)])


def _get_upload_size(file: UploadFile) -> int:
    file.file.seek(0, os.SEEK_END)
    size = file.file.tell()
    file.file.seek(0)
    return size


@router.post("/media/upload")
async def upload_media(
    request: Request,
    media_type: str = Form(...),
    file: UploadFile = File(...),
    source_url: Optional[str] = Form(None),
    settings: Settings = Depends(get_settings),
) -> dict:
    request_id = getattr(request.state, "request_id", "unknown")
    if media_type not in {"image", "video"}:
        return JSONResponse(
            status_code=400,
            content=error_response("BAD_REQUEST", "media_type must be image or video"),
        )
    max_bytes = (
        settings.cos_image_max_bytes
        if media_type == "image"
        else settings.cos_video_max_bytes
    )

    try:
        size = _get_upload_size(file)
    except Exception:
        return JSONResponse(
            status_code=400,
            content=error_response("BAD_REQUEST", "invalid upload"),
        )

    if size <= 0 or size > max_bytes:
        return JSONResponse(
            status_code=400,
            content=error_response("BAD_REQUEST", "file size not allowed"),
        )

    head = await file.read(512)
    await file.seek(0)

    try:
        content_type = validate_media(media_type, file.content_type, head)
    except MediaValidationError as exc:
        return JSONResponse(
            status_code=400, content=error_response(exc.code, exc.message)
        )

    try:
        cos_client = COSClient(settings)
    except COSConfigError:
        if source_url:
            logger.warning(
                "cos not configured request_id=%s fallback=source_url",
                request_id,
            )
            return success_response({"url": source_url, "fallback": True})
        return JSONResponse(
            status_code=503,
            content=error_response("COS_NOT_CONFIGURED", "COS not configured"),
        )

    key = build_object_key(
        settings.cos_media_prefix, media_type, file.filename, content_type
    )

    try:
        cos_client.upload_fileobj(file.file, key, content_type)
        result = cos_client.build_access_url(key)
    except COSUploadError:
        if source_url:
            logger.warning(
                "cos upload failed request_id=%s fallback=source_url",
                request_id,
            )
            return success_response({"url": source_url, "fallback": True})
        logger.error("cos upload failed request_id=%s", request_id)
        return JSONResponse(
            status_code=502,
            content=error_response("COS_UPLOAD_FAILED", "media upload failed"),
        )
    finally:
        await file.close()

    payload = {"url": result.url, "signed": result.signed}
    if result.expires_in:
        payload["expires_in"] = result.expires_in
    return success_response(payload)

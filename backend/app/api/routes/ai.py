from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from app.core.auth import require_user
from app.core.config import Settings, get_settings
from app.schemas.ai import AnalyzeRequest, GenerateImageRequest
from app.schemas.response import error_response, success_response
from app.services.ai_service import APIError, analyze_text, generate_image

router = APIRouter(prefix="/api/v1/ai", dependencies=[Depends(require_user)])


@router.post("/analyze", response_model=None)
async def analyze(
    payload: AnalyzeRequest,
    request: Request,
    settings: Settings = Depends(get_settings),
):
    model = payload.model or settings.default_text_model
    request.state.step = "ai.analyze"
    request.state.model = model
    user_key = request.headers.get("x-user-gemini-key")
    try:
        result = await analyze_text(payload, user_key, settings)
        return success_response(result)
    except APIError as exc:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response(exc.code, exc.message),
        )


@router.post("/generate-image", response_model=None)
async def generate_image_proxy(
    payload: GenerateImageRequest,
    request: Request,
    settings: Settings = Depends(get_settings),
):
    model = payload.model or settings.default_image_model
    request.state.step = "ai.generate_image"
    request.state.model = model
    user_key = request.headers.get("x-user-gemini-key")
    try:
        result = await generate_image(payload, user_key, settings)
        return success_response(result)
    except APIError as exc:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response(exc.code, exc.message),
        )

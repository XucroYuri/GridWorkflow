import time
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import api_router
from app.core.auth import AuthError
from app.core.config import get_settings
from app.core.logger import get_logger
from app.schemas.response import error_response

settings = get_settings()
logger = get_logger(settings.log_level)

app = FastAPI(title=settings.app_name)

def _parse_cors_origins(raw: str) -> list[str]:
    if not raw:
        return ["*"]
    if raw.strip() == "*":
        return ["*"]
    return [origin.strip() for origin in raw.split(",") if origin.strip()]

allowed_origins = _parse_cors_origins(settings.cors_allow_origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content=error_response("BAD_REQUEST", "请求参数错误"),
    )


@app.exception_handler(AuthError)
async def auth_exception_handler(_: Request, exc: AuthError):
    return JSONResponse(
        status_code=401,
        content=error_response("UNAUTHORIZED", exc.message),
    )


@app.middleware("http")
async def request_context(request: Request, call_next):
    """追加 request_id、记录时延并统一异常输出。"""
    request_id = str(uuid4())
    request.state.request_id = request_id
    start_time = time.perf_counter()
    response = None
    try:
        response = await call_next(request)
    except Exception:
        step = getattr(request.state, "step", "-")
        model = getattr(request.state, "model", "-")
        logger.exception(
            "Unhandled error request_id=%s step=%s model=%s",
            request_id,
            step,
            model,
        )
        response = JSONResponse(
            status_code=500,
            content=error_response("UPSTREAM_ERROR", "服务内部异常，请稍后重试。"),
        )
    duration_ms = (time.perf_counter() - start_time) * 1000
    step = getattr(request.state, "step", "-")
    model = getattr(request.state, "model", "-")
    logger.info(
        "request completed request_id=%s step=%s model=%s latency_ms=%.2f",
        request_id,
        step,
        model,
        duration_ms,
    )
    if response is None:
        response = JSONResponse(
            status_code=500,
            content=error_response("UPSTREAM_ERROR", "服务内部异常，请稍后重试。"),
        )
    response.headers["X-Request-ID"] = request_id
    return response

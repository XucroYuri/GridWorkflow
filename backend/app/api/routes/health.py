from datetime import datetime, timezone
import logging

from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.schemas.response import success_response

logger = logging.getLogger("gridworkflow")

router = APIRouter()


@router.get("/health")
async def health(settings: Settings = Depends(get_settings)) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    logger.info("health check ok env=%s", settings.env)
    return success_response({"status": "ok", "env": settings.env, "timestamp": now})



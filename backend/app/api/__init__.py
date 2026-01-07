from fastapi import APIRouter

from app.api.routes import ai, health, media, video, workflow

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(ai.router, tags=["ai"])
api_router.include_router(video.router, tags=["video"])
api_router.include_router(media.router, tags=["media"])
api_router.include_router(workflow.router, tags=["workflow"])

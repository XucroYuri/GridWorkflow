from functools import lru_cache
import os

from pydantic import BaseModel, Field


class Settings(BaseModel):
    """应用配置，统一从环境变量读取。"""

    app_name: str = "GridWorkflow Backend"
    env: str = Field(default_factory=lambda: os.getenv("APP_ENV", "development"))
    host: str = Field(default_factory=lambda: os.getenv("APP_HOST", "0.0.0.0"))
    port: int = Field(default_factory=lambda: int(os.getenv("APP_PORT", "8000")))
    log_level: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    cors_allow_origins: str = Field(
        default_factory=lambda: os.getenv("ALLOWED_ORIGINS")
        or os.getenv("CORS_ALLOW_ORIGINS")
        or os.getenv("CORS_ORIGINS", "")
    )
    ai_gateway_base_url: str = Field(
        default_factory=lambda: os.getenv("AI_GATEWAY_BASE_URL", "https://ai.t8star.cn/v1")
    )
    ai_gateway_api_key: str = Field(
        default_factory=lambda: os.getenv("AI_GATEWAY_API_KEY", "")
    )
    default_text_model: str = Field(
        default_factory=lambda: os.getenv("DEFAULT_TEXT_MODEL", "gemini-3-pro-preview")
    )
    default_image_model: str = Field(
        default_factory=lambda: os.getenv("DEFAULT_IMAGE_MODEL", "nano-banana-2")
    )
    text_timeout_sec: float = Field(
        default_factory=lambda: float(os.getenv("TEXT_TIMEOUT_SEC", "10"))
    )
    image_timeout_sec: float = Field(
        default_factory=lambda: float(os.getenv("IMAGE_TIMEOUT_SEC", "30"))
    )
    max_image_base64_bytes: int = Field(
        default_factory=lambda: int(os.getenv("MAX_IMAGE_BASE64_BYTES", str(2 * 1024 * 1024)))
    )
    video_poll_interval_ms: int = Field(
        default_factory=lambda: int(os.getenv("VIDEO_POLL_INTERVAL_MS", "3000"))
    )
    video_timeout_sec: float = Field(
        default_factory=lambda: float(os.getenv("VIDEO_TIMEOUT_SEC", "180"))
    )
    cos_secret_id: str | None = Field(default_factory=lambda: os.getenv("COS_SECRET_ID"))
    cos_secret_key: str | None = Field(default_factory=lambda: os.getenv("COS_SECRET_KEY"))
    cos_bucket: str | None = Field(default_factory=lambda: os.getenv("COS_BUCKET"))
    cos_region: str | None = Field(default_factory=lambda: os.getenv("COS_REGION"))
    cos_signed_url: bool = Field(
        default_factory=lambda: os.getenv("COS_SIGNED_URL", "false").lower()
        in {"1", "true", "yes", "on"}
    )
    cos_signed_url_ttl_seconds: int = Field(
        default_factory=lambda: int(os.getenv("COS_SIGNED_URL_TTL_SECONDS", "300"))
    )
    cos_media_prefix: str = Field(
        default_factory=lambda: os.getenv("COS_MEDIA_PREFIX", "media")
    )
    cos_image_max_bytes: int = Field(
        default_factory=lambda: int(os.getenv("COS_IMAGE_MAX_BYTES", "10485760"))
    )
    cos_video_max_bytes: int = Field(
        default_factory=lambda: int(os.getenv("COS_VIDEO_MAX_BYTES", "104857600"))
    )
    supabase_url: str | None = Field(default_factory=lambda: os.getenv("SUPABASE_URL"))
    supabase_anon_key: str | None = Field(
        default_factory=lambda: os.getenv("SUPABASE_ANON_KEY")
    )
    supabase_service_role_key: str | None = Field(
        default_factory=lambda: os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    )
    supabase_jwt_secret: str | None = Field(
        default_factory=lambda: os.getenv("SUPABASE_JWT_SECRET")
    )
    supabase_jwt_audience: str | None = Field(
        default_factory=lambda: os.getenv("SUPABASE_JWT_AUDIENCE")
    )
    supabase_jwt_issuer: str | None = Field(
        default_factory=lambda: os.getenv("SUPABASE_JWT_ISSUER")
    )
    ip_allowlist_enabled: bool = Field(
        default_factory=lambda: os.getenv("IP_ALLOWLIST_ENABLED", "false").lower()
        in {"1", "true", "yes", "on"}
    )
    ip_allowlist: str = Field(
        default_factory=lambda: os.getenv("IP_ALLOWLIST", "97.64.29.114")
    )
    ip_allowlist_configured: bool = Field(
        default_factory=lambda: os.getenv("IP_ALLOWLIST") is not None
    )
    trusted_proxy_cidrs: str = Field(
        default_factory=lambda: os.getenv("TRUSTED_PROXY_CIDRS", "")
    )


@lru_cache
def get_settings() -> Settings:
    """缓存配置，避免重复解析。"""
    return Settings()



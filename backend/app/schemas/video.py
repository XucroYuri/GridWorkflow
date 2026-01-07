from typing import List, Optional

from pydantic import BaseModel, Field, validator


class VideoGenerateRequest(BaseModel):
    """视频生成请求（契约冻结版）"""
    prompt: str = Field(..., min_length=1)
    model: str = Field(..., min_length=1)
    images: Optional[List[str]] = None
    aspect_ratio: str = Field(..., min_length=1)
    hd: bool = False
    duration: int = Field(..., ge=1)
    provider: str = Field("t8star")

    @validator("prompt", "model", "aspect_ratio", "provider")
    def strip_strings(cls, value: str) -> str:
        return value.strip()

    @validator("images", each_item=True)
    def validate_images(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("images must not be empty")
        return value

    @validator("images")
    def normalize_images(cls, value: Optional[List[str]]) -> Optional[List[str]]:
        if value is None:
            return value
        if len(value) == 0:
            raise ValueError("images must not be empty")
        return value

    @validator("provider")
    def normalize_provider(cls, value: str) -> str:
        return value.lower()

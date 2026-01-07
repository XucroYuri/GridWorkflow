from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    prompt: str = Field(min_length=1)
    model: Optional[str] = None
    system_instruction: Optional[str] = Field(default=None, alias="systemInstruction")
    response_format: Optional[str] = Field(default=None, alias="responseFormat")


class GenerateImageRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    prompt: str = Field(min_length=1)
    model: Optional[str] = None
    image_size: Optional[str] = None
    aspect_ratio: Optional[str] = None
    image: Optional[str] = None
    response_format: Optional[str] = Field(default=None, alias="responseFormat")

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class AnchorItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    text: Optional[str] = None
    image_base64: Optional[str] = Field(default=None, alias="image_base64")


class Anchors(BaseModel):
    model_config = ConfigDict(extra="ignore")

    character: Optional[AnchorItem] = None
    environment: Optional[AnchorItem] = None
    prop: Optional[AnchorItem] = None


class ConceptRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    style: Optional[str] = None
    plot: Optional[str] = None
    anchors: Optional[Anchors] = None
    aspect_ratio: Optional[str] = None
    image_size: Optional[str] = "1K"


class StoryboardPlanRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    style: Optional[str] = None
    plot: Optional[str] = None
    anchors: Optional[Anchors] = None
    concept_prompt: Optional[str] = None
    concept_image_url: Optional[str] = None
    output_language: Optional[str] = "zh-CN"


class StoryboardGenerateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    storyboard_prompt: Optional[str] = None
    reference_image_base64: Optional[str] = None
    aspect_ratio: Optional[str] = None
    image_size: Optional[str] = "1K"


class VideoPromptRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    storyboard_prompt: Optional[str] = None
    original_plot: Optional[str] = None
    duration: int = 10
    fps: int = 60
    output_language: Optional[str] = "zh-CN"

from __future__ import annotations

from typing import Optional

from app.schemas.workflow import Anchors


def output_language_rule(output_language: Optional[str]) -> str:
    normalized = (output_language or "").strip()
    if not normalized:
        return "Please respond in Simplified Chinese."
    lowered = normalized.lower()
    if lowered in {"zh", "zh-cn", "zh-hans", "zh-hans-cn"}:
        return "Please respond in Simplified Chinese."
    if lowered in {"en", "en-us", "en-gb", "english"}:
        return "Please respond in English."
    return f"Please respond in {normalized}."


def build_anchor_context(anchors: Optional[Anchors]) -> str:
    if anchors is None:
        return ""
    parts: list[str] = []
    if anchors.character and anchors.character.text:
        parts.append(f"Character: {anchors.character.text.strip()}")
    if anchors.environment and anchors.environment.text:
        parts.append(f"Environment: {anchors.environment.text.strip()}")
    if anchors.prop and anchors.prop.text:
        parts.append(f"Prop: {anchors.prop.text.strip()}")
    return "; ".join(part for part in parts if part)


def build_concept_prompt(
    style: str, plot: str, anchors: Optional[Anchors], aspect_ratio: str
) -> str:
    anchor_text = build_anchor_context(anchors)
    parts = [style.strip(), f"Plot: {plot.strip()}"]
    if anchor_text:
        parts.append(f"Anchors: {anchor_text}")
    parts.append(f"Aspect ratio {aspect_ratio}")
    return " ".join(parts)


def build_storyboard_plan_system(output_language: Optional[str]) -> str:
    return "\n".join(
        [
            "Role: Storyboard Artist & Director.",
            "Task: Convert the following plot into a 3x3 grid image prompt.",
            "Requirements:",
            "- Output a single prompt text for a 3x3 storyboard grid image.",
            "- Include shot labels: ELS, LS, MLS, MS, MCU, CU, ECU, Low Angle, High Angle.",
            "- Do not output JSON or Markdown.",
            output_language_rule(output_language),
        ]
    )


def build_storyboard_plan_prompt(
    style: str,
    plot: str,
    anchor_context: str,
    concept_prompt: Optional[str],
    concept_image_url: Optional[str],
) -> str:
    lines = [f"Style: {style.strip()}", f"Plot: {plot.strip()}"]
    if anchor_context:
        lines.append(f"Character/Scene Context: {anchor_context}")
    if concept_prompt:
        lines.append(f"Concept Prompt: {concept_prompt.strip()}")
    if concept_image_url:
        lines.append(f"Concept Image URL: {concept_image_url.strip()}")
    return "\n".join(lines)


def build_video_prompt_system(
    duration: int, fps: int, output_language: Optional[str]
) -> str:
    return "\n".join(
        [
            "Task: Generate a video prompt based on the storyboard logic.",
            "Constraints:",
            f"- Duration: {duration} seconds; FPS: {fps}.",
            "- Keep the original plot intact.",
            "- Describe camera movement and pacing.",
            "- No emoji.",
            output_language_rule(output_language),
        ]
    )


def build_video_prompt_prompt(storyboard_prompt: str, original_plot: str) -> str:
    return "\n".join(
        [
            f"Storyboard Prompt: {storyboard_prompt.strip()}",
            f"Original Plot: {original_plot.strip()}",
        ]
    )

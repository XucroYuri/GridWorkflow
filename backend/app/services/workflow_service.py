from __future__ import annotations

from typing import Any, Optional

from app.schemas.workflow import Anchors


def select_reference_image(anchors: Optional[Anchors]) -> Optional[str]:
    if anchors is None:
        return None
    for key in ("character", "environment", "prop"):
        item = getattr(anchors, key, None)
        if item and item.image_base64:
            value = item.image_base64.strip()
            if value:
                return value
    return None


def extract_first_image_url(result: Any) -> Optional[str]:
    if isinstance(result, dict):
        direct = _extract_url_from_item(result)
        if direct:
            return direct
        nested = result.get("data")
        return extract_first_image_url(nested)
    if isinstance(result, list):
        for item in result:
            direct = _extract_url_from_item(item)
            if direct:
                return direct
    return None


def _extract_url_from_item(item: Any) -> Optional[str]:
    if not isinstance(item, dict):
        return None
    for key in ("url", "image_url", "imageUrl", "output_url"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None

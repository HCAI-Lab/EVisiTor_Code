"""
Shared utilities for UI element extraction across EGM / Gemma 4 / Qwen3-VL pipelines.

All three model scripts (run_egm.py, run_gemma4.py, run_qwen3vl.py) import from
this module so the I/O, prompt, schema, and drawing logic stay identical and
the only thing that varies is the model backend.
"""

from __future__ import annotations

import json
import os
import re
from typing import List, Optional

from PIL import Image, ImageDraw, ImageFont
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Schema (unchanged from the original Gemini script)
# ---------------------------------------------------------------------------
class UIElement(BaseModel):
    name: str = Field(description="A short, descriptive name of the element")
    type: str = Field(
        description=(
            "The type of the element, such as button, menu, icon, "
            "spreadsheet cell, column header, or row header"
        )
    )
    text: Optional[str] = Field(
        default=None,
        description="The visible text content of the element, if applicable",
    )
    bbox: List[int] = Field(
        description=(
            "Bounding box [ymin, xmin, ymax, xmax] as integers in 0-1000 "
            "normalized coordinates (0 = top/left, 1000 = bottom/right)"
        )
    )


class UIAnalysis(BaseModel):
    elements: List[UIElement] = Field(
        description="List of the smallest visible UI elements found in the screenshot"
    )


# ---------------------------------------------------------------------------
# Prompt (kept verbatim so outputs are comparable across backends)
# ---------------------------------------------------------------------------
PROMPT = """\
Analyze this UI screenshot.

Return only stable visible UI elements:
- top menu items
- toolbar buttons/icons
- spreadsheet column headers
- spreadsheet row headers
- non-empty spreadsheet cells
- status/mode-line regions

Do not return individual characters.
Do not return red annotation labels or red rectangles if present.
Do not infer hidden cells.
Use bbox as [ymin, xmin, ymax, xmax], normalized 0 to 1000.
Return JSON only.
"""


# ---------------------------------------------------------------------------
# JSON extraction (models often wrap output in fences or prose)
# ---------------------------------------------------------------------------
def extract_json(text: str) -> dict:
    """Best-effort JSON extraction from a model's free-form reply."""
    if not text:
        raise ValueError("Empty model output")

    # Strip ```json ... ``` fences if present
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1)

    # Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Fall back to the first {...} block
    brace = re.search(r"\{.*\}", text, re.DOTALL)
    if brace:
        return json.loads(brace.group(0))

    raise ValueError(f"Could not extract JSON from model output:\n{text[:500]}")


# ---------------------------------------------------------------------------
# Annotation drawing
# ---------------------------------------------------------------------------
def _load_font(size: int = 14) -> Optional[ImageFont.ImageFont]:
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ):
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def annotate_and_save(
    img: Image.Image,
    data: dict,
    base_name: str,
    annotated_dir: str,
    json_dir: str,
) -> None:
    """Draw red bboxes + labels and persist both PNG and JSON."""
    img = img.copy()
    draw = ImageDraw.Draw(img)
    font = _load_font(14)
    w, h = img.size

    for item in data.get("elements", []):
        bbox = item.get("bbox")
        if not (isinstance(bbox, list) and len(bbox) == 4):
            continue
        ymin, xmin, ymax, xmax = bbox
        x0 = (xmin / 1000.0) * w
        y0 = (ymin / 1000.0) * h
        x1 = (xmax / 1000.0) * w
        y1 = (ymax / 1000.0) * h
        draw.rectangle([x0, y0, x1, y1], outline="red", width=3)
        label = item.get("name", "Unknown")
        draw.text((x0, max(0, y0 - 15)), label, fill="red", font=font)

    os.makedirs(annotated_dir, exist_ok=True)
    os.makedirs(json_dir, exist_ok=True)

    json_path = os.path.join(json_dir, f"{base_name}.json")
    img_path = os.path.join(annotated_dir, f"{base_name}.png")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    img.save(img_path)

    print(f"  -> json: {json_path}")
    print(f"  -> png : {img_path}")


# ---------------------------------------------------------------------------
# Input discovery
# ---------------------------------------------------------------------------
SUPPORTED_IMG_EXT = (".png", ".jpg", ".jpeg", ".webp")


def discover_images(input_dir: str, filter_substr: str = "step0") -> list[str]:
    """Return absolute paths to images matching the original script's filter.

    The original code only processes filenames containing 'step0' (case-insensitive).
    Pass filter_substr='' to disable that filter.
    """
    if not os.path.isdir(input_dir):
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    paths = []
    for name in sorted(os.listdir(input_dir)):
        low = name.lower()
        if not low.endswith(SUPPORTED_IMG_EXT):
            continue
        if filter_substr and filter_substr.lower() not in low:
            continue
        paths.append(os.path.join(input_dir, name))
    return paths


def load_image(path: str) -> Image.Image:
    return Image.open(path).convert("RGB")

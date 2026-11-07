""""The outliers that break INT8"

Diagram proposed by the diagram studio from the recommendation
«The outliers that break INT8»: a hidden layer has a narrow bell around
zero and, as the model grows, atypical values of 60 to 70 appear and
stretch the quantization scale. Zeroing those outliers sinks the model; zeroing
the same number of random values barely changes it.

Self-contained: Pillow only. `python3 source.py` writes out.png and
`DIAGRAM_OUT=versions/v1.png python3 source.py` writes wherever the studio says.
"""

from __future__ import annotations

import math
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# 1. Palette and typography (PyramidSpace dark theme)
# ---------------------------------------------------------------------------
BG = "#090B0D"
CARD = "#111519"
RAISED = "#171C21"
HAIR = "#262A2E"
AXIS = "#3F4142"
TEXT = "#F8FAFC"
MUTED = "#94A3B8"
FAINT = "#64748B"
AMBER = "#F59E0B"
RED = "#F87171"
GREEN = "#4ADE80"

W, H = 1800, 1200
MARGIN = 90

FONT_DIR = Path("/usr/share/fonts/truetype")
LIBERATION = FONT_DIR / "liberation"
DEJAVU = FONT_DIR / "dejavu"


# ---------------------------------------------------------------------------
# 2. Utilities
# ---------------------------------------------------------------------------
def rgb(value: str) -> tuple[int, int, int]:
    """Convert `#RRGGBB` to an RGB tuple."""
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def mix(c1: str, c2: str, t: float) -> tuple[int, int, int]:
    """Interpolate two hex colors; `t` is the weight of `c2` (0..1)."""
    t = max(0.0, min(1.0, t))
    a, b = rgb(c1), rgb(c2)
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Liberation Sans (the blog sans) with DejaVu as fallback."""
    path = LIBERATION / ("LiberationSans-Bold.ttf" if bold else "LiberationSans-Regular.ttf")
    try:
        return ImageFont.truetype(str(path), size)
    except OSError:
        fallback = DEJAVU / ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf")
        try:
            return ImageFont.truetype(str(fallback), size)
        except OSError:
            return ImageFont.load_default()


def new_canvas() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    """Dark canvas without a frame (the blog CSS rounds the corners)."""
    image = Image.new("RGB", (W, H), rgb(BG))
    return image, ImageDraw.Draw(image)


def rich_text(draw: ImageDraw.ImageDraw, x: int, cy: int,
              parts: list[tuple[str, str, bool]], size: int) -> None:
    """Text in runs with their own color and weight, left-aligned."""
    cursor = x
    for text, color, bold in parts:
        face = font(size, bold=bold)
        draw.text((cursor, cy), text, font=face, fill=rgb(color), anchor="lm")
        cursor += draw.textlength(text, font=face)


def rich_center(draw: ImageDraw.ImageDraw, cx: int, cy: int,
                parts: list[tuple[str, str, bool]], size: int) -> None:
    """Like `rich_text`, but centered on `cx`."""
    total = sum(draw.textlength(text, font=font(size, bold=bold)) for text, _, bold in parts)
    rich_text(draw, round(cx - total / 2), cy, parts, size)


# ---------------------------------------------------------------------------
# 3. Diagram pieces
# ---------------------------------------------------------------------------
PLOT_X0, PLOT_X1 = 170, 1100
BASE_Y, TOP_Y = 790, 300
BELL_CX, BELL_W = 480, 562
BELL_N, BELL_BAR_W, BELL_GAP = 15, 30, 8
BELL_PEAK, BELL_SIGMA = 165, 2.3
OUT_X, OUT_BAR_W, OUT_GAP = 900, 34, 14
OUT_HEIGHTS = (380, 450, 410)

RES_X0, RES_X1 = 1170, 1710
ROW1_LABEL_Y, ROW1_BAR_Y = 480, 540
ROW2_LABEL_Y, ROW2_BAR_Y = 700, 760
RES_BAR_H = 34

BAND = (MARGIN, 970, W - MARGIN, 1080)
BAND_DIV = 740


def bell(draw: ImageDraw.ImageDraw) -> None:
    """Hidden-layer histogram: a narrow bell around zero."""
    start = BELL_CX - BELL_W // 2
    center = (BELL_N - 1) / 2
    for index in range(BELL_N):
        height = round(BELL_PEAK * math.exp(-((index - center) ** 2) / (2 * BELL_SIGMA ** 2)))
        if height < 8:  # the bell tails add nothing and look like dust on the axis
            continue
        x = start + index * (BELL_BAR_W + BELL_GAP)
        draw.rectangle((x, BASE_Y - height, x + BELL_BAR_W, BASE_Y), fill=rgb(AMBER))


def outliers(draw: ImageDraw.ImageDraw) -> None:
    """The three atypical columns that stretch the scale."""
    for index, height in enumerate(OUT_HEIGHTS):
        x = OUT_X + index * (OUT_BAR_W + OUT_GAP)
        draw.rectangle((x, BASE_Y - height, x + OUT_BAR_W, BASE_Y), fill=rgb(RED))


def result_bar(draw: ImageDraw.ImageDraw, cy: int, fraction: float, color: str) -> None:
    """Horizontal result bar over a faint track."""
    top, bottom = cy - RES_BAR_H // 2, cy + RES_BAR_H // 2
    draw.rounded_rectangle((RES_X0, top, RES_X1, bottom), radius=RES_BAR_H // 2,
                           fill=mix(color, BG, 0.9), outline=mix(color, BG, 0.55), width=2)
    filled = max(RES_BAR_H, round((RES_X1 - RES_X0) * fraction))
    draw.rounded_rectangle((RES_X0, top, RES_X0 + filled, bottom), radius=RES_BAR_H // 2,
                           fill=rgb(color))


def band(image: Image.Image, draw: ImageDraw.ImageDraw) -> None:
    """Model-scale strip with two segments and the threshold in the middle."""
    shape = Image.new("L", (W, H), 0)
    ImageDraw.Draw(shape).rounded_rectangle(BAND, radius=24, fill=255)

    left_mask = shape.copy()
    ImageDraw.Draw(left_mask).rectangle((BAND_DIV, 0, W, H), fill=0)
    right_mask = shape.copy()
    ImageDraw.Draw(right_mask).rectangle((0, 0, BAND_DIV, H), fill=0)

    image.paste(rgb(RAISED), (0, 0), left_mask)
    image.paste(mix(RED, CARD, 0.9), (0, 0), right_mask)

    draw.rounded_rectangle(BAND, radius=24, outline=rgb(HAIR), width=2)
    draw.line((BAND_DIV, BAND[1] + 2, BAND_DIV, BAND[3] - 2), fill=rgb(AXIS), width=2)

    mid = (BAND[1] + BAND[3]) / 2
    rich_center(draw, (BAND[0] + BAND_DIV) / 2, mid, [
        ("<6B", TEXT, True),
        (": rare", MUTED, False),
    ], size=32)
    rich_center(draw, (BAND_DIV + BAND[2]) / 2, mid, [
        (">6B", RED, True),
        (": in every layer", MUTED, False),
    ], size=32)


# ---------------------------------------------------------------------------
# 4. Composition
# ---------------------------------------------------------------------------
def draw() -> Image.Image:
    """Compose the diagram and return the final image."""
    image, canvas = new_canvas()

    # Header
    canvas.text((MARGIN, 130), "The outliers that break INT8",
                font=font(62, bold=True), fill=rgb(TEXT), anchor="lm")
    canvas.text((MARGIN, 204), "they appear past the critical scale",
                font=font(30), fill=rgb(MUTED), anchor="lm")

    # Histogram axes (broken between the bell and the outliers)
    canvas.line((PLOT_X0, TOP_Y, PLOT_X0, BASE_Y), fill=rgb(AXIS), width=2)
    canvas.line((PLOT_X0, BASE_Y, 795, BASE_Y), fill=rgb(AXIS), width=2)
    canvas.line((835, BASE_Y, PLOT_X1, BASE_Y), fill=rgb(AXIS), width=2)
    for offset in (0, 16):
        canvas.line((802 + offset, BASE_Y + 11, 814 + offset, BASE_Y - 11),
                    fill=rgb(AXIS), width=3)

    canvas.text((PLOT_X0 + 6, 336), "hidden layer", font=font(26), fill=rgb(MUTED), anchor="lm")

    bell(canvas)
    outliers(canvas)

    canvas.text((BELL_CX, 824), "−3 … 3", font=font(28), fill=rgb(AMBER), anchor="mm")
    canvas.text((OUT_X + 51, 824), "outliers 60–70", font=font(28), fill=rgb(RED), anchor="mm")

    # Cause: the atypical column stretches the scale of the whole matrix
    rich_text(canvas, PLOT_X0, 882, [
        ("an atypical column ", MUTED, False),
        ("stretches the scale", TEXT, False),
    ], size=26)

    # Result of the value-zeroing experiment
    rich_text(canvas, RES_X0, ROW1_LABEL_Y, [
        ("zeroing outliers", MUTED, False),
        ("  →  ", FAINT, False),
        ("collapse", RED, True),
    ], size=30)
    result_bar(canvas, ROW1_BAR_Y, 0.07, RED)

    rich_text(canvas, RES_X0, ROW2_LABEL_Y, [
        ("zeroing at random", MUTED, False),
        ("  →  ", FAINT, False),
        ("barely changes", GREEN, True),
    ], size=30)
    result_bar(canvas, ROW2_BAR_Y, 1.0, GREEN)

    # Model-scale strip: the ~6B threshold
    band(image, canvas)

    return image


def save(image: Image.Image, path: str | Path | None = None) -> Path:
    """Save the PNG to `DIAGRAM_OUT` (or out.png when run by hand)."""
    target = Path(path or os.environ.get("DIAGRAM_OUT", "out.png"))
    target.parent.mkdir(parents=True, exist_ok=True)
    image.save(target, format="PNG")
    return target


if __name__ == "__main__":
    destination = save(draw())
    print(f"diagram written to {destination}")

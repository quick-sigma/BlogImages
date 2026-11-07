"""Stochastic rounding

Diagram proposed by the diagram studio from the recommendation
«Stochastic rounding in FP4»: deterministic rounding always falls on the same
side and accumulates bias; stochastic rounding spreads the probability between
the two neighbouring values and leaves the gradient unbiased.

Self-contained: Pillow only. `python3 source.py` writes out.png and
`DIAGRAM_OUT=versions/v1.png python3 source.py` writes where the studio says.
"""

from __future__ import annotations

import math
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# 1. Palette and type (PyramidSpace dark theme)
# ---------------------------------------------------------------------------
BG = "#090B0D"
CARD = "#111519"
HAIR = "#1F2123"
AXIS = "#3F4142"
TEXT = "#F8FAFC"
MUTED = "#94A3B8"
FAINT = "#64748B"
TEAL = "#2DD4BF"
AMBER = "#F59E0B"
RED = "#F87171"

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


def font(size: int, bold: bool = False, mono: bool = False) -> ImageFont.FreeTypeFont:
    """Liberation Sans for labels and DejaVu Sans Mono for the figures."""
    if mono:
        path = DEJAVU / ("DejaVuSansMono-Bold.ttf" if bold else "DejaVuSansMono.ttf")
    else:
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
    """Frameless dark canvas (the blog CSS rounds the corners)."""
    image = Image.new("RGB", (W, H), rgb(BG))
    return image, ImageDraw.Draw(image)


def arrow(draw: ImageDraw.ImageDraw, x0: float, y0: float, x1: float, y1: float,
          color: str, width: int = 4, head: int = 16) -> None:
    """Straight arrow with a triangular head."""
    draw.line((x0, y0, x1, y1), fill=rgb(color), width=width)
    ang = math.atan2(y1 - y0, x1 - x0)
    left = (x1 - head * math.cos(ang - 0.45), y1 - head * math.sin(ang - 0.45))
    right = (x1 - head * math.cos(ang + 0.45), y1 - head * math.sin(ang + 0.45))
    draw.polygon([(x1, y1), left, right], fill=rgb(color))


# ---------------------------------------------------------------------------
# 3. Diagram pieces
# ---------------------------------------------------------------------------
AXIS_X0, AXIS_X1 = MARGIN, 1710
MARKS = 6
SPACING = (AXIS_X1 - AXIS_X0) / (MARKS - 1)
ROW_A_AXIS, ROW_B_AXIS = 520, 830
DOT_Y_OFFSET = 60
DOT_R = 10


def mark_x(index: int) -> float:
    """X of the representable mark `index`."""
    return AXIS_X0 + index * SPACING


def draw_axis(draw: ImageDraw.ImageDraw, y: int) -> None:
    """Line with its representable values."""
    draw.line((AXIS_X0, y, AXIS_X1, y), fill=rgb(FAINT), width=2)
    for index in range(MARKS):
        x = mark_x(index)
        draw.line((x, y - 10, x, y + 10), fill=rgb(TEAL), width=3)


def draw_dot(draw: ImageDraw.ImageDraw, x: float, y: int) -> None:
    """The real value that is going to be rounded."""
    draw.ellipse((x - DOT_R, y - DOT_R, x + DOT_R, y + DOT_R), fill=rgb(AMBER))


def draw_row_labels(draw: ImageDraw.ImageDraw, y: int, label: str) -> None:
    """Row label, to the left of its line."""
    draw.text((MARGIN, y), label, font=font(30, bold=True), fill=rgb(MUTED), anchor="lm")


def draw_verdict(draw: ImageDraw.ImageDraw, y: int, label: str, color: str) -> None:
    """Row verdict, to the right of the line."""
    draw.text((AXIS_X1, y), label, font=font(30, bold=True), fill=rgb(color), anchor="rm")


def draw_threshold(draw: ImageDraw.ImageDraw) -> None:
    """Dimension of the noise threshold √3 σ, to the right of the stochastic row."""
    x, y0, y1 = 1640, ROW_B_AXIS, ROW_B_AXIS - 140
    draw.line((x, y0, x, y1), fill=mix(MUTED, BG, 0.45), width=2)
    for yy in (y0, y1):
        draw.line((x - 8, yy, x + 8, yy), fill=mix(MUTED, BG, 0.45), width=2)
    draw.line((MARGIN, y1, x, y1), fill=mix(FAINT, BG, 0.55), width=1)
    draw.text((x - 24, (y0 + y1) / 2), "√3 σ", font=font(24, mono=True),
              fill=rgb(MUTED), anchor="rm")


# ---------------------------------------------------------------------------
# 4. Composition
# ---------------------------------------------------------------------------
def draw() -> Image.Image:
    """Compose the diagram and return the final image."""
    image, canvas = new_canvas()

    canvas.text((MARGIN, 140), "Stochastic rounding",
                font=font(58, bold=True), fill=rgb(TEXT), anchor="lm")

    # Deterministic row: everything falls to the value below
    draw_row_labels(canvas, ROW_A_AXIS - 190, "deterministic")
    draw_axis(canvas, ROW_A_AXIS)
    for mark in range(4):
        x = mark_x(mark) + 0.30 * SPACING
        draw_dot(canvas, x, ROW_A_AXIS - DOT_Y_OFFSET)
        arrow(canvas, x - 8, ROW_A_AXIS - DOT_Y_OFFSET + 8,
              mark_x(mark) + 12, ROW_A_AXIS - 6, AMBER)
    draw_verdict(canvas, ROW_A_AXIS - 190, "bias", RED)

    # Stochastic row: it falls up or down depending on the distance
    draw_row_labels(canvas, ROW_B_AXIS - 190, "stochastic")
    draw_axis(canvas, ROW_B_AXIS)
    for fraction, mark in ((0.30, 0), (0.80, 1), (0.50, 2), (0.25, 3)):
        x = mark_x(mark) + fraction * SPACING
        draw_dot(canvas, x, ROW_B_AXIS - DOT_Y_OFFSET)
        arrow(canvas, x - 8, ROW_B_AXIS - DOT_Y_OFFSET + 8,
              mark_x(mark) + 12, ROW_B_AXIS - 6, AMBER)
        arrow(canvas, x + 8, ROW_B_AXIS - DOT_Y_OFFSET + 8,
              mark_x(mark + 1) - 12, ROW_B_AXIS - 6, AMBER)
        if fraction == 0.80:
            canvas.text((x, ROW_B_AXIS - DOT_Y_OFFSET - 44), "p = 0.8",
                        font=font(26, mono=True), fill=rgb(AMBER), anchor="mm")
    draw_verdict(canvas, ROW_B_AXIS - 190, "unbiased", TEAL)
    draw_threshold(canvas)

    canvas.text((MARGIN, 1000), "unbiased, no freezing",
                font=font(28), fill=rgb(MUTED), anchor="lm")

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

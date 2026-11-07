"""Layer-by-layer distillation (LKD)

Diagram proposed by the diagram studio from the recommendation
«Layer-by-layer distillation (LKD)»: ZeroQuant drops to INT4 without a full QAT
by freezing the model and tuning each quantized layer so that it reproduces the
output of its FP16 twin, in minutes per layer.

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
HAIR = "#1F2123"
AXIS = "#3F4142"
TEXT = "#F8FAFC"
MUTED = "#94A3B8"
FAINT = "#64748B"
TEAL = "#2DD4BF"
AMBER = "#F59E0B"

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
    """Liberation Sans for labels and DejaVu Sans Mono for figures."""
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
    """Dark canvas without a frame (the blog CSS rounds the corners)."""
    image = Image.new("RGB", (W, H), rgb(BG))
    return image, ImageDraw.Draw(image)


def arrow(draw: ImageDraw.ImageDraw, x0: int, y: int, x1: int, color: str,
          width: int = 4, head: int = 16) -> None:
    """Horizontal arrow with a triangular head."""
    draw.line((x0, y, x1, y), fill=rgb(color), width=width)
    draw.polygon([(x1, y), (x1 - head, y - head * 0.55), (x1 - head, y + head * 0.55)],
                 fill=rgb(color))


# ---------------------------------------------------------------------------
# 3. Diagram pieces
# ---------------------------------------------------------------------------
FP16_X0, FP16_X1 = 320, 760
INT4_X0, INT4_X1 = 1040, 1480
ROWS = (380, 520, 660, 800)
ROW_H = 100


def draw_padlock(draw: ImageDraw.ImageDraw, x: int, y: int) -> None:
    """Small padlock: body and shackle."""
    draw.arc((x + 6, y - 2, x + 30, y + 24), start=180, end=360, fill=rgb(MUTED), width=5)
    draw.rounded_rectangle((x, y + 12, x + 36, y + 40), radius=7, fill=mix(MUTED, BG, 0.72))


def draw_columns(draw: ImageDraw.ImageDraw) -> None:
    """Two columns of layers: the FP16 reference and the INT4 copy."""
    draw.rounded_rectangle((FP16_X0, 260, FP16_X1, 940), radius=20, fill=rgb(CARD),
                           outline=rgb(HAIR), width=2)
    draw.rounded_rectangle((INT4_X0, 260, INT4_X1, 940), radius=20, fill=rgb(CARD),
                           outline=rgb(HAIR), width=2)
    draw.text((FP16_X0 + 30, 320), "FP16", font=font(30, bold=True), fill=rgb(MUTED), anchor="lm")
    draw_padlock(draw, FP16_X1 - 66, 300)
    draw.text((INT4_X0 + 30, 320), "INT4", font=font(30, bold=True), fill=rgb(TEAL), anchor="lm")
    for index, y in enumerate(ROWS, start=1):
        draw.rounded_rectangle((FP16_X0 + 30, y, FP16_X1 - 30, y + ROW_H), radius=12,
                               fill=mix(MUTED, BG, 0.86), outline=mix(MUTED, BG, 0.45), width=2)
        draw.text((FP16_X0 + 56, y + ROW_H / 2), str(index), font=font(26, mono=True),
                  fill=rgb(MUTED), anchor="lm")
        draw.rounded_rectangle((INT4_X0 + 30, y, INT4_X1 - 30, y + ROW_H), radius=12,
                               fill=mix(TEAL, BG, 0.86), outline=mix(TEAL, BG, 0.45), width=2)
        draw.text((INT4_X0 + 56, y + ROW_H / 2), str(index), font=font(26, mono=True),
                  fill=rgb(TEAL), anchor="lm")


def draw_imitations(draw: ImageDraw.ImageDraw) -> None:
    """One arrow per pair: the INT4 layer mimics the FP16 output."""
    for i, y in enumerate(ROWS):
        cy = y + ROW_H / 2
        arrow(draw, FP16_X1 + 8, cy, INT4_X0 - 8, AMBER)
        if i == 0:
            draw.text(((FP16_X1 + INT4_X0) / 2, cy - 34), "mimics the output",
                      font=font(26), fill=rgb(AMBER), anchor="mm")


def draw_clock(draw: ImageDraw.ImageDraw, cx: int, cy: int, radius: int) -> None:
    """Minutes-per-layer clock."""
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius),
                 outline=mix(MUTED, BG, 0.4), width=4)
    for step in range(12):
        theta = math.radians(step * 30)
        x0 = cx + (radius - 10) * math.cos(theta)
        y0 = cy + (radius - 10) * math.sin(theta)
        x1 = cx + (radius - 4) * math.cos(theta)
        y1 = cy + (radius - 4) * math.sin(theta)
        draw.line((x0, y0, x1, y1), fill=mix(MUTED, BG, 0.4), width=3)
    draw.line((cx, cy, cx, cy - radius * 0.55), fill=rgb(MUTED), width=5)
    draw.line((cx, cy, cx + radius * 0.4, cy), fill=rgb(MUTED), width=5)


# ---------------------------------------------------------------------------
# 4. Composition
# ---------------------------------------------------------------------------
def draw() -> Image.Image:
    """Compose the diagram and return the final image."""
    image, canvas = new_canvas()

    canvas.text((MARGIN, 140), "Layer-by-layer distillation",
                font=font(58, bold=True), fill=rgb(TEXT), anchor="lm")

    draw_columns(canvas)
    draw_imitations(canvas)

    # The clock and the footnote
    draw_clock(canvas, 370, 1020, 44)
    canvas.text((440, 1020), "minutes per layer", font=font(28), fill=rgb(MUTED), anchor="lm")

    canvas.rounded_rectangle((1040, 984, 1260, 1046), radius=31, fill=mix(TEAL, BG, 0.9),
                             outline=mix(TEAL, BG, 0.55), width=2)
    canvas.text((1150, 1015), "no QAT", font=font(26, bold=True), fill=rgb(TEAL), anchor="mm")

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

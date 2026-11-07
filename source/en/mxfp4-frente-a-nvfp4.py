"""«MXFP4 vs NVFP4»

Diagram proposed by the diagram studio from the recommendation
«MXFP4 vs NVFP4»: the same E2M1 element with two ways of storing the scale
(blocks of 32 with E8M0 vs blocks of 16 with E4M3 plus a global scale) and its
effective bits per weight.

Self-contained: Pillow only. `python3 source.py` writes out.png and
`DIAGRAM_OUT=versions/v1.png python3 source.py` writes where the studio says.
"""

from __future__ import annotations

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
    """Convert `#RRGGBB` into an RGB tuple."""
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def mix(c1: str, c2: str, t: float) -> tuple[int, int, int]:
    """Interpolate two hex colors; `t` is the weight of `c2` (0..1)."""
    t = max(0.0, min(1.0, t))
    a, b = rgb(c1), rgb(c2)
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def font(size: int, bold: bool = False, mono: bool = False) -> ImageFont.FreeTypeFont:
    """Liberation Sans for labels and DejaVu Sans Mono for the numbers."""
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
    """Dark canvas without frame (the blog CSS rounds the corners)."""
    image = Image.new("RGB", (W, H), rgb(BG))
    return image, ImageDraw.Draw(image)


Part = tuple[str, str, bool, bool]  # text, color, bold, monospace


def rich(draw: ImageDraw.ImageDraw, x: int, cy: int, parts: list[Part], size: int) -> int:
    """Text in runs with their own color, weight and font; returns the width."""
    cursor = x
    for text, color, bold, mono in parts:
        face = font(size, bold=bold, mono=mono)
        draw.text((cursor, cy), text, font=face, fill=rgb(color), anchor="lm")
        cursor += draw.textlength(text, font=face)
    return round(cursor - x)


# ---------------------------------------------------------------------------
# 3. Diagram pieces
# ---------------------------------------------------------------------------
PANEL_L = (90, 280, 880, 900)
PANEL_R = (920, 280, 1710, 900)

CELL_W, CELL_H, GAP = 18, 100, 4


def draw_panel(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], title: str) -> None:
    """Panel card with its title."""
    x0, y0, x1, y1 = box
    draw.rounded_rectangle((x0, y0, x1, y1), radius=20, fill=rgb(CARD),
                           outline=rgb(HAIR), width=2)
    draw.text((x0 + 30, y0 + 52), title, font=font(26, bold=True), fill=rgb(TEXT), anchor="lm")


def draw_block(draw: ImageDraw.ImageDraw, x0: int, y: int, count: int) -> int:
    """Row of E2M1 cells; returns the total width."""
    for i in range(count):
        x = x0 + i * (CELL_W + GAP)
        draw.rounded_rectangle((x, y, x + CELL_W, y + CELL_H), radius=4,
                               fill=mix(TEAL, BG, 0.85), outline=rgb(TEAL), width=1)
    return count * (CELL_W + GAP) - GAP


def draw_scale_box(draw: ImageDraw.ImageDraw, cx: int, y: int, label: str) -> None:
    """Local scale box: E8M0 or E4M3."""
    width, height = 130, 48
    draw.rounded_rectangle((cx - width / 2, y, cx + width / 2, y + height), radius=10,
                           fill=mix(AMBER, BG, 0.88), outline=mix(AMBER, BG, 0.5), width=2)
    draw.text((cx, y + height / 2), label, font=font(20, bold=True, mono=True),
              fill=rgb(AMBER), anchor="mm")
    draw.line((cx, y + height, cx, y + height + 20), fill=mix(AMBER, BG, 0.45), width=2)


def draw_bits_bar(image: Image.Image, draw: ImageDraw.ImageDraw, x0: int, y: int,
                  width: int, split: float, number: str) -> None:
    """Stacked effective-bits bar: element in teal and scale in amber."""
    height = 32
    split_x = round(x0 + width * split)
    layer = Image.new("RGB", (W, H), rgb(BG))
    bar = ImageDraw.Draw(layer)
    bar.rectangle((x0, y, x0 + width, y + height), fill=rgb(TEAL))
    bar.rectangle((split_x, y, x0 + width, y + height), fill=rgb(AMBER))
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).rounded_rectangle((x0, y, x0 + width, y + height), radius=10, fill=255)
    image.paste(layer, (0, 0), mask)
    draw.text((x0, y - 30), "effective bits per weight", font=font(20), fill=rgb(FAINT), anchor="lm")
    text_width = draw.textlength(number, font=font(26, bold=True, mono=True))
    draw.text((x0 + width - text_width, y - 30), number, font=font(26, bold=True, mono=True),
              fill=rgb(TEXT), anchor="lm")


def draw_global_bracket(draw: ImageDraw.ImageDraw, x0: int, x1: int, y: int, label: str) -> None:
    """Grey bracket for the global scale, above the two blocks."""
    draw.line((x0, y, x1, y), fill=mix(MUTED, BG, 0.45), width=2)
    for x in (x0, x1):
        draw.line((x, y, x, y - 14), fill=mix(MUTED, BG, 0.45), width=2)
    draw.text(((x0 + x1) / 2, y - 34), label, font=font(22), fill=rgb(MUTED), anchor="mm")


def draw_legend(draw: ImageDraw.ImageDraw, y: int) -> None:
    """Color legend at the foot."""
    items = (
        (MARGIN, TEAL, "E2M1 · 4 bits"),
        (520, AMBER, "local scale · 8 bits"),
        (1080, MUTED, "global scale · FP32"),
    )
    for x, color, text in items:
        draw.ellipse((x, y - 7, x + 14, y + 7), fill=rgb(color))
        draw.text((x + 26, y), text, font=font(22), fill=rgb(MUTED), anchor="lm")


# ---------------------------------------------------------------------------
# 4. Composition
# ---------------------------------------------------------------------------
def draw() -> Image.Image:
    """Compose the diagram and return the final image."""
    image, canvas = new_canvas()

    canvas.text((MARGIN, 140), "MXFP4 vs NVFP4",
                font=font(58, bold=True), fill=rgb(TEXT), anchor="lm")

    draw_panel(canvas, PANEL_L, "MXFP4 (OCP)")
    draw_panel(canvas, PANEL_R, "NVFP4 (NVIDIA)")

    # MXFP4: one block of 32 with its E8M0 scale
    draw_scale_box(canvas, 470, 450, "E8M0")
    draw_block(canvas, 120, 520, 32)
    canvas.text((120, 660), "E2M1", font=font(22), fill=rgb(MUTED), anchor="lm")
    canvas.text((820, 660), "block 32", font=font(22), fill=rgb(MUTED), anchor="rm")
    draw_bits_bar(image, canvas, 120, 770, 580, 4 / 4.25, "≈4.25 bits")

    # NVFP4: two blocks of 16, each with E4M3, and a global FP32 scale
    draw_global_bracket(canvas, 960, 1664, 424, "FP32 scale")
    for block_x, scale_x in ((960, 1126), (1332, 1498)):
        draw_scale_box(canvas, scale_x, 450, "E4M3")
        draw_block(canvas, block_x, 520, 16)
    canvas.text((960, 660), "E2M1", font=font(22), fill=rgb(MUTED), anchor="lm")
    canvas.text((1664, 660), "block 16", font=font(22), fill=rgb(MUTED), anchor="rm")
    draw_bits_bar(image, canvas, 950, 770, 580, 4 / 4.5, "≈4.50 bits")

    draw_legend(canvas, 1000)

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

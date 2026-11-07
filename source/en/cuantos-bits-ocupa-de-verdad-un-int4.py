""""How many bits an INT4 really takes"

Diagram proposed by the diagram studio from the recommendation
«How many bits an INT4 really takes»: an INT4 is not alone, every block of
values carries its scale and that scale also takes space. Top: one FP32 scale
per 64 weights (4 + 0.5 = 4.5 bits/parameter); bottom: QLoRA's double
quantization (FP8 scale + FP32 scale of scales, 4 + 0.125 + 0.002 ≈ 4.127).
At the foot: the stacked bar with the three slices.

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
REF_GREY = "#94A3B8"
AMBER = "#F59E0B"
TEAL = "#2DD4BF"

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
    """Liberation Sans for labels and DejaVu Sans Mono for the math."""
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


def rich_center(draw: ImageDraw.ImageDraw, cx: float, cy: int, parts: list[Part], size: int) -> None:
    """Like `rich`, but centered on `cx`."""
    total = sum(draw.textlength(text, font=font(size, bold=bold, mono=mono))
                for text, _, bold, mono in parts)
    rich(draw, round(cx - total / 2), cy, parts, size)


def rich_right(draw: ImageDraw.ImageDraw, right: int, cy: int, parts: list[Part], size: int) -> None:
    """Like `rich`, but right-aligned."""
    total = sum(draw.textlength(text, font=font(size, bold=bold, mono=mono))
                for text, _, bold, mono in parts)
    rich(draw, round(right - total), cy, parts, size)


# ---------------------------------------------------------------------------
# 3. Diagram pieces
# ---------------------------------------------------------------------------
CELL, GAP, NCELLS = 110, 10, 6
CELLS_X = MARGIN
CELLS_W = NCELLS * CELL + (NCELLS - 1) * GAP     # 650
BOX_X, BOX_W = 830, 210
SECOND_X, SECOND_W = 1070, 210

ROW1_Y = 340
ROW2_Y = 580
ROW_H = CELL

TITLE_Y, SUB_Y = 130, 204
CAPTION_Y, LEGEND_Y = 810, 890
BAR_Y0, BAR_Y1 = 950, 1030


def draw_values_row(draw: ImageDraw.ImageDraw, y: int) -> None:
    """Six INT4 value boxes: each one with its four bits."""
    for index in range(NCELLS):
        x = CELLS_X + index * (CELL + GAP)
        draw.rounded_rectangle((x, y, x + CELL, y + CELL), radius=16,
                               fill=mix(TEAL, BG, 0.9))
        # four little squares: the 4 bits of each value
        bit_w, bit_gap = 20, 5
        total = 4 * bit_w + 3 * bit_gap
        bx = x + (CELL - total) / 2
        by = y + (CELL - 20) / 2
        for bit in range(4):
            sx = bx + bit * (bit_w + bit_gap)
            draw.rounded_rectangle((sx, by, sx + bit_w, by + 20), radius=4, fill=rgb(TEAL))


def draw_scale_box(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, title: str,
                   detail: str, voice: str, color: str) -> None:
    """Scale box: title, size in bits and how many elements per scale."""
    draw.rounded_rectangle((x, y, x + w, y + ROW_H), radius=16, fill=rgb(CARD),
                           outline=mix(color, CARD, 0.6), width=2)
    draw.rounded_rectangle((x + 2, y + 16, x + 8, y + ROW_H - 16), radius=3, fill=rgb(color))
    draw.text((x + 22, y + 26), title, font=font(24, bold=True), fill=rgb(TEXT), anchor="lm")
    draw.text((x + 22, y + 54), detail, font=font(22, mono=True), fill=rgb(color), anchor="lm")
    draw.text((x + 22, y + 79), voice, font=font(22), fill=rgb(MUTED), anchor="lm")


def draw_connector(draw: ImageDraw.ImageDraw, x0: int, x1: int, y: int) -> None:
    """Horizontal connector between the row and its scale."""
    draw.line((x0, y, x1, y), fill=rgb(AXIS), width=3)


def draw_equations(draw: ImageDraw.ImageDraw) -> None:
    """The two calculations, to the right of each row."""
    rich_right(draw, W - MARGIN, ROW1_Y + ROW_H / 2, [
        ("4", TEXT, True, True),
        (" + ", MUTED, False, False),
        ("0.5", AMBER, True, True),
        (" = ", MUTED, False, False),
        ("4.5", TEXT, True, True),
        (" bits/parameter", MUTED, False, False),
    ], size=30)
    rich_right(draw, W - MARGIN, ROW2_Y + ROW_H / 2, [
        ("4", TEXT, True, True),
        (" + ", MUTED, False, False),
        ("0.125", AMBER, True, True),
        (" + ", MUTED, False, False),
        ("0.002", REF_GREY, True, True),
        (" ≈ ", MUTED, False, False),
        ("4.127", TEXT, True, True),
    ], size=30)


def draw_footer(image: Image.Image, draw: ImageDraw.ImageDraw) -> None:
    """Closing calculation, legend and stacked bar with the three slices."""
    rich(draw, MARGIN, CAPTION_Y, [
        ("the overhead drops from ", MUTED, False, False),
        ("0.5", AMBER, True, True),
        (" to ", MUTED, False, False),
        ("0.127", TEXT, True, True),
        (" bits", MUTED, False, False),
    ], size=32)

    # Bar legend
    legend = (
        (MARGIN, TEAL, "value", "4", " bits"),
        (700, AMBER, "scale", "0.125", ""),
        (1150, REF_GREY, "scale of scales", "0.002", ""),
    )
    for x, color, name, value, unit in legend:
        draw.ellipse((x, LEGEND_Y - 7, x + 14, LEGEND_Y + 7), fill=rgb(color))
        rich(draw, x + 26, LEGEND_Y, [
            (name + " · ", MUTED, False, False),
            (value, TEXT, True, True),
            (unit, MUTED, False, False),
        ], size=26)

    # Stacked bar, clipped with rounded corners
    layer = Image.new("RGB", (W, H), rgb(BG))
    bar = ImageDraw.Draw(layer)
    bar.rectangle((MARGIN, BAR_Y0, W - MARGIN, BAR_Y1), fill=rgb(TEAL))
    bar.rectangle((1656, BAR_Y0, 1704, BAR_Y1), fill=rgb(AMBER))
    bar.rectangle((1706, BAR_Y0, W - MARGIN, BAR_Y1), fill=rgb(REF_GREY))
    bar.line((1655, BAR_Y0, 1655, BAR_Y1), fill=rgb(HAIR), width=2)
    bar.line((1705, BAR_Y0, 1705, BAR_Y1), fill=rgb(HAIR), width=2)
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).rounded_rectangle((MARGIN, BAR_Y0, W - MARGIN, BAR_Y1),
                                           radius=14, fill=255)
    image.paste(layer, (0, 0), mask)


# ---------------------------------------------------------------------------
# 4. Composition
# ---------------------------------------------------------------------------
def draw() -> Image.Image:
    """Compose the diagram and return the final image."""
    image, canvas = new_canvas()

    canvas.text((MARGIN, TITLE_Y), "How many bits an INT4 really takes",
                font=font(58, bold=True), fill=rgb(TEXT), anchor="lm")
    canvas.text((MARGIN, SUB_Y), "the value and its scale",
                font=font(32), fill=rgb(MUTED), anchor="lm")

    # Top row: values + FP32 scale
    canvas.text((MARGIN, ROW1_Y - 28), "INT4 values · 4 bits",
                font=font(26), fill=rgb(MUTED), anchor="lm")
    draw_values_row(canvas, ROW1_Y)
    draw_connector(canvas, CELLS_X + CELLS_W, BOX_X, ROW1_Y + ROW_H // 2)
    draw_scale_box(canvas, BOX_X, ROW1_Y, BOX_W, "FP32 scale",
                   "32 bits", "per 64 weights", AMBER)

    # Bottom row: the same values with double quantization
    draw_values_row(canvas, ROW2_Y)
    draw_connector(canvas, CELLS_X + CELLS_W, BOX_X, ROW2_Y + ROW_H // 2)
    draw_scale_box(canvas, BOX_X, ROW2_Y, BOX_W, "FP8 scale",
                   "8 bits", "per 64 weights", AMBER)
    draw_connector(canvas, BOX_X + BOX_W, SECOND_X, ROW2_Y + ROW_H // 2)
    draw_scale_box(canvas, SECOND_X, ROW2_Y, SECOND_W, "scale of scales",
                   "FP32", "per 256 scales", REF_GREY)

    draw_equations(canvas)
    draw_footer(image, canvas)

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

""""INT8: 8 bits and 256 steps"

Diagram proposed by the diagram studio from the recommendation
«INT8: 8 bits and 256 steps»: an INT8 spends 1 bit on the sign and 7 on the value, and
splits the range −128…+127 into 256 equal steps. Because the grid is
uniform, a single spike of 70 forces the scale to stretch (step ≈ 0.55) and
normal values of ±3 fit in only ~11 steps.

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
AMBER = "#F59E0B"
TEAL = "#2DD4BF"

CELL_TEXT_AMBER = "#2A1A00"
CELL_TEXT_TEAL = "#06201C"

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
    """Liberation Sans for labels and DejaVu Sans Mono for the bit figures."""
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


Part = tuple[str, str, bool, bool]  # text, color, bold, monospaced


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


def arrow(draw: ImageDraw.ImageDraw, start, end, color: str, width: int = 3, head: int = 16) -> None:
    """Straight arrow with a triangular head."""
    draw.line((start, end), fill=rgb(color), width=width)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    left = (end[0] - head * math.cos(angle - math.pi / 7), end[1] - head * math.sin(angle - math.pi / 7))
    right = (end[0] - head * math.cos(angle + math.pi / 7), end[1] - head * math.sin(angle + math.pi / 7))
    draw.polygon([end, left, right], fill=rgb(color))


# ---------------------------------------------------------------------------
# 3. Diagram pieces
# ---------------------------------------------------------------------------
CELL, GAP, NBITS = 120, 6, 8
STRIP_X = MARGIN
STRIP_W = NBITS * CELL + (NBITS - 1) * GAP      # 1002
STRIP_Y = 360

AXIS_X0, AXIS_X1 = MARGIN, W - MARGIN
AXIS_Y = 660
STEP_TOP = AXIS_Y - 60

TITLE_Y, SUB_Y = 136, 214


def value_x(value: float) -> float:
    """Position on the line of a value in the range −128…+127."""
    return AXIS_X0 + (value + 128) / 255 * (AXIS_X1 - AXIS_X0)


def draw_strip(draw: ImageDraw.ImageDraw) -> None:
    """The INT8 strip: 1 sign bit and 7 value bits, with their bit number."""
    fields = (
        ("sign", 1, AMBER, CELL_TEXT_AMBER),
        ("value", 7, TEAL, CELL_TEXT_TEAL),
    )
    x = STRIP_X
    bit = NBITS - 1
    for name, count, color, text_color in fields:
        group_w = count * CELL + (count - 1) * GAP
        for index in range(count):
            cell_x = x + index * (CELL + GAP)
            draw.rounded_rectangle((cell_x, STRIP_Y, cell_x + CELL, STRIP_Y + CELL), radius=16,
                                   fill=rgb(color))
            draw.text((cell_x + CELL / 2, STRIP_Y + CELL / 2), str(bit),
                      font=font(30, bold=True, mono=True), fill=rgb(text_color), anchor="mm")
            bit -= 1
        draw.text((x + group_w / 2, STRIP_Y - 28), name,
                  font=font(28), fill=rgb(color), anchor="mm")
        x += group_w + GAP


def draw_scale_card(draw: ImageDraw.ImageDraw) -> None:
    """Scale card, connected to the line by an arrow."""
    box = (1380, 345, W - MARGIN, 495)
    draw.rounded_rectangle(box, radius=22, fill=rgb(CARD), outline=rgb(HAIR), width=2)
    draw.text((box[0] + 34, box[1] + 48), "scale s", font=font(40, bold=True),
              fill=rgb(TEXT), anchor="lm")
    draw.text((box[0] + 34, box[1] + 106), "constant step", font=font(28),
              fill=rgb(MUTED), anchor="lm")
    arrow(draw, (1545, box[3] + 10), (1545, AXIS_Y - 14), MUTED, width=3, head=16)


def draw_axis(draw: ImageDraw.ImageDraw) -> None:
    """256-step line with the ±3 zone and the spike of 70 marked."""
    # Steps: 256 uniform marks from −128 to +127, with a longer tick every 16 codes
    for code in range(256):
        x = value_x(code - 128)
        major = code % 16 == 0
        draw.line((x, STEP_TOP + (0 if major else 12), x, AXIS_Y),
                  fill=rgb(TEAL) if major else mix(TEAL, BG, 0.62),
                  width=3 if major else 2)

    # The ±3 zone: the ~11 steps the normal range takes up
    left, right = value_x(-5.5), value_x(5.5)
    draw.rounded_rectangle((left, STEP_TOP - 10, right, AXIS_Y + 14), radius=8,
                           fill=mix(TEAL, BG, 0.82))
    for code in range(-5, 6):
        x = value_x(code)
        draw.line((x, STEP_TOP - 4, x, AXIS_Y + 8), fill=rgb(TEAL), width=4)

    # The line
    draw.line((AXIS_X0, AXIS_Y, AXIS_X1, AXIS_Y), fill=rgb(AXIS), width=3)

    # The spike of 70: the atypical value keeps the last step
    peak_x = AXIS_X1
    draw.line((peak_x, AXIS_Y, peak_x, AXIS_Y - 130), fill=rgb(AMBER), width=6)
    draw.ellipse((peak_x - 9, AXIS_Y - 147, peak_x + 9, AXIS_Y - 129), fill=rgb(AMBER))

    draw.text((AXIS_X0, 574), "−128 … +127", font=font(28), fill=rgb(MUTED), anchor="lm")


def rich_right(draw: ImageDraw.ImageDraw, right: int, cy: int, parts: list[Part], size: int) -> None:
    """Like `rich`, but right-aligned."""
    total = sum(draw.textlength(text, font=font(size, bold=bold, mono=mono))
                for text, _, bold, mono in parts)
    rich(draw, round(right - total), cy, parts, size)


def draw_examples(draw: ImageDraw.ImageDraw) -> None:
    """The two numeric examples, at the foot of the line under their mark."""
    rich_center(draw, value_x(0), 745, [
        ("±3", TEXT, True, True),
        (" fit in ", MUTED, False, False),
        ("~11", TEXT, True, True),
        (" steps", MUTED, False, False),
    ], size=34)
    rich_right(draw, AXIS_X1, 745, [
        ("spike ", MUTED, False, False),
        ("70", TEXT, True, True),
        (" → step ≈ ", MUTED, False, False),
        ("0.55", TEXT, True, True),
    ], size=34)


def draw_note(draw: ImageDraw.ImageDraw) -> None:
    """Closing note across the full width."""
    box = (MARGIN, 900, W - MARGIN, 1040)
    draw.rounded_rectangle(box, radius=22, fill=rgb(CARD), outline=rgb(HAIR), width=2)
    rich_center(draw, W / 2, (box[1] + box[3]) / 2, [
        ("the step does not adapt: if the spike grows, all others lose resolution", MUTED, False, False),
    ], size=36)


# ---------------------------------------------------------------------------
# 4. Composition
# ---------------------------------------------------------------------------
def draw() -> Image.Image:
    """Compose the diagram and return the final image."""
    image, canvas = new_canvas()

    canvas.text((MARGIN, TITLE_Y), "INT8: 8 bits and 256 steps",
                font=font(64, bold=True), fill=rgb(TEXT), anchor="lm")
    canvas.text((MARGIN, SUB_Y), "1 sign bit, 7 value bits",
                font=font(34), fill=rgb(MUTED), anchor="lm")

    draw_strip(canvas)
    draw_scale_card(canvas)
    draw_axis(canvas)
    draw_examples(canvas)
    draw_note(canvas)

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

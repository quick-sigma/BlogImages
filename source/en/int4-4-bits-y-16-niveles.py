"""INT4: 4 bits and 16 levels

Diagram proposed by the diagram studio from the recommendation
«INT4: 4 bits and 16 levels»: the same byte split with half the little boxes
(1 sign bit and 3 value bits, sixteen codes from −8 to +7). Its grid of
sixteen steps is compared with the INT8 grid (256 levels) drawn behind in
grey: the INT4 step is sixteen times thicker.

Self-contained: Pillow only. `python3 source.py` writes out.png and
`DIAGRAM_OUT=versions/v1.png python3 source.py` writes where the studio says.
"""

from __future__ import annotations

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
REF_GREY = "#64748B"
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


def rich_right(draw: ImageDraw.ImageDraw, right: int, cy: int, parts: list[Part], size: int) -> None:
    """Like `rich`, but right-aligned."""
    total = sum(draw.textlength(text, font=font(size, bold=bold, mono=mono))
                for text, _, bold, mono in parts)
    rich(draw, round(right - total), cy, parts, size)


# ---------------------------------------------------------------------------
# 3. Diagram pieces
# ---------------------------------------------------------------------------
CELL, GAP, NBITS = 130, 6, 4
STRIP_X = MARGIN
STRIP_W = NBITS * CELL + (NBITS - 1) * GAP      # 482
STRIP_Y = 322

AXIS_X0, AXIS_X1 = MARGIN, W - MARGIN
AXIS_Y = 700

TITLE_Y, SUB_Y = 140, 216

INT4_TICK_TOP = AXIS_Y - 110
INT8_TICK_TOP = AXIS_Y - 50
STEP_INDEX = 8                                  # step between levels 8 and 9


def level_x(index: int, levels: int) -> float:
    """Center of level `index` when there are `levels` levels across the width."""
    return AXIS_X0 + (index + 0.5) / levels * (AXIS_X1 - AXIS_X0)


def draw_strip(draw: ImageDraw.ImageDraw) -> None:
    """The INT4 strip: 1 sign bit and 3 value bits, with their bit number."""
    fields = (
        ("sign", 1, AMBER, CELL_TEXT_AMBER),
        ("value (3 bits)", 3, TEAL, CELL_TEXT_TEAL),
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
        draw.text((x + group_w / 2, STRIP_Y - 26), name,
                  font=font(28), fill=rgb(color), anchor="mm")
        x += group_w + GAP


def draw_scale_card(draw: ImageDraw.ImageDraw) -> None:
    """Card for the per-block scale that INT4 uses."""
    box = (1400, 306, W - MARGIN, 486)
    draw.rounded_rectangle(box, radius=22, fill=rgb(CARD), outline=rgb(HAIR), width=2)
    draw.text((box[0] + 34, box[1] + 50), "per-block scale", font=font(30, bold=True),
              fill=rgb(TEXT), anchor="lm")
    draw.text((box[0] + 34, box[1] + 106), "64 / 128 elements", font=font(26),
              fill=rgb(MUTED), anchor="lm")


def draw_axis(draw: ImageDraw.ImageDraw) -> None:
    """INT8 grid (reference, behind) and INT4 grid (in front)."""
    # INT8 reference: 256 levels in faint grey, behind
    for index in range(256):
        x = level_x(index, 256)
        draw.line((x, INT8_TICK_TOP, x, AXIS_Y), fill=rgb(REF_GREY), width=2)

    # The INT4 step highlighted in amber
    left, right = level_x(STEP_INDEX, 16), level_x(STEP_INDEX + 1, 16)

    # The line and the 16 INT4 levels
    draw.line((AXIS_X0, AXIS_Y, AXIS_X1, AXIS_Y), fill=rgb(AXIS), width=3)
    for index in range(16):
        x = level_x(index, 16)
        color = AMBER if index in (STEP_INDEX, STEP_INDEX + 1) else TEAL
        draw.line((x, INT4_TICK_TOP, x, AXIS_Y), fill=rgb(color), width=10 if color == AMBER else 8)

    # Dimension of the step: the stretch of line between its two levels, in amber
    draw.line((left, AXIS_Y, right, AXIS_Y), fill=rgb(AMBER), width=12)

    draw.text((AXIS_X0, 552), "−8 … +7", font=font(28), fill=rgb(MUTED), anchor="lm")
    rich_right(draw, AXIS_X1, 552, [
        ("INT8 reference (256 levels)", REF_GREY, False, False),
    ], size=26)


def draw_comparisons(draw: ImageDraw.ImageDraw) -> None:
    """The two comparisons, at the foot of the line."""
    rich(draw, MARGIN, 760, [
        ("16", TEXT, True, True),
        (" codes", MUTED, False, False),
    ], size=30)
    rich_center(draw, (level_x(STEP_INDEX, 16) + level_x(STEP_INDEX + 1, 16)) / 2, 760, [
        ("the step is ", MUTED, False, False),
        ("16", TEXT, True, True),
        (" times thicker", MUTED, False, False),
    ], size=30)


def draw_note(draw: ImageDraw.ImageDraw) -> None:
    """Note about two's complement, at the foot."""
    box = (MARGIN, 930, W - MARGIN, 1060)
    draw.rounded_rectangle(box, radius=22, fill=rgb(CARD), outline=rgb(HAIR), width=2)
    rich_center(draw, W / 2, (box[1] + box[3]) / 2, [
        ("−8 has no positive counterpart: ", MUTED, False, False),
        ("two's complement", TEXT, False, False),
    ], size=32)


# ---------------------------------------------------------------------------
# 4. Composition
# ---------------------------------------------------------------------------
def draw() -> Image.Image:
    """Compose the diagram and return the final image."""
    image, canvas = new_canvas()

    canvas.text((MARGIN, TITLE_Y), "INT4: 4 bits and 16 levels",
                font=font(60, bold=True), fill=rgb(TEXT), anchor="lm")
    canvas.text((MARGIN, SUB_Y), "the same split with half the boxes",
                font=font(34), fill=rgb(MUTED), anchor="lm")

    draw_strip(canvas)
    draw_scale_card(canvas)
    draw_axis(canvas)
    draw_comparisons(canvas)
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

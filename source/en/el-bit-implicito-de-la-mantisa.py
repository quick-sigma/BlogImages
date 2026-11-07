"""The implicit bit of the mantissa

Diagram proposed by the diagram studio from a blog recommendation: the mantissa
of a normalized number always starts with 1, so that bit is not stored. The
strip shows the 23 cells that are actually stored and, on its left, the ghost
cell of the implicit bit: 23 stored plus 1 borrowed make 24 bits of precision.

Self-contained: Pillow only. `python3 source.py` writes out.png and
`DIAGRAM_OUT=versions/v1.png python3 source.py` writes wherever the studio says.
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

# Composition geometry
TITLE_Y, SUBTITLE_Y = 140, 218
LABEL_Y = 396
CELL_TOP, CELL_BOT = 424, 714
CELL_W, CELL_GAP, GHOST_GAP = 56, 8, 20
GHOST_W = 76
GHOST_X = 120
STRIP_X = GHOST_X + GHOST_W + GHOST_GAP
BIT_LABEL_Y = 800
CARD_BOX = (90, 930, 1710, 1062)
EQUATION_Y = 996


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
    """Dark canvas without a frame (the blog CSS rounds the corners)."""
    image = Image.new("RGB", (W, H), rgb(BG))
    return image, ImageDraw.Draw(image)


Part = tuple[str, str, bool, bool]  # text, color, bold, monospaced


def rich_center(draw: ImageDraw.ImageDraw, cx: float, cy: int, parts: list[Part],
                size: int) -> None:
    """Text in runs with their own color, weight and font, centered on `cx`."""
    total = sum(draw.textlength(text, font=font(size, bold=bold, mono=mono))
                for text, _, bold, mono in parts)
    cursor = cx - total / 2
    for text, color, bold, mono in parts:
        face = font(size, bold=bold, mono=mono)
        draw.text((cursor, cy), text, font=face, fill=rgb(color), anchor="lm")
        cursor += draw.textlength(text, font=face)


# ---------------------------------------------------------------------------
# 3. Diagram pieces
# ---------------------------------------------------------------------------
def dashed_rect(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], radius: int,
                color: str, width: int = 3, dash: int = 16, gap: int = 10) -> None:
    """Dashed border with rounded corners (the corners are solid)."""
    x0, y0, x1, y1 = box
    for y in (y0, y1):
        x = x0 + radius
        while x < x1 - radius:
            x2 = min(x + dash, x1 - radius)
            draw.line((x, y, x2, y), fill=rgb(color), width=width)
            x = x2 + gap
    for x in (x0, x1):
        y = y0 + radius
        while y < y1 - radius:
            y2 = min(y + dash, y1 - radius)
            draw.line((x, y, x, y2), fill=rgb(color), width=width)
            y = y2 + gap
    d = radius * 2
    draw.arc((x0, y0, x0 + d, y0 + d), 180, 270, fill=rgb(color), width=width)
    draw.arc((x1 - d, y0, x1, y0 + d), 270, 360, fill=rgb(color), width=width)
    draw.arc((x0, y1 - d, x0 + d, y1), 90, 180, fill=rgb(color), width=width)
    draw.arc((x1 - d, y1 - d, x1, y1), 0, 90, fill=rgb(color), width=width)


def draw_strip(draw: ImageDraw.ImageDraw) -> None:
    """The ghost cell of the implicit 1 and the 23 stored mantissa cells."""
    cell_h = CELL_BOT - CELL_TOP
    teal_fill = mix(TEAL, BG, 0.85)
    amber_fill = mix(AMBER, BG, 0.85)

    # The bit that is not stored: dashed cell with the 1 as an outline.
    ghost = (GHOST_X, CELL_TOP, GHOST_X + GHOST_W, CELL_BOT)
    draw.rounded_rectangle(ghost, radius=12, fill=amber_fill)
    dashed_rect(draw, ghost, radius=12, color=AMBER, width=3)
    draw.text((GHOST_X + GHOST_W / 2, CELL_TOP + cell_h / 2), "1",
              font=font(124, bold=True, mono=True), fill=amber_fill,
              stroke_width=4, stroke_fill=rgb(AMBER), anchor="mm")

    # The 23 cells that do take up space.
    for index in range(23):
        x = STRIP_X + index * (CELL_W + CELL_GAP)
        draw.rounded_rectangle((x, CELL_TOP, x + CELL_W, CELL_BOT), radius=12,
                               fill=teal_fill, outline=rgb(TEAL), width=2)


def strip_right() -> int:
    """Right edge of the mantissa strip."""
    return STRIP_X + 23 * CELL_W + 22 * CELL_GAP


def draw_labels(draw: ImageDraw.ImageDraw) -> None:
    """Labels: the ghost cell and the mantissa, plus the 23-bit bracket."""
    draw.text((GHOST_X + GHOST_W / 2 + 7, LABEL_Y), "1 implicit", font=font(30),
              fill=rgb(AMBER), anchor="ms")
    right = strip_right()
    draw.text(((STRIP_X + right) / 2, LABEL_Y), "mantissa", font=font(30),
              fill=rgb(TEAL), anchor="ms")

    # Bracket for the 23 stored bits.
    bracket_y = CELL_BOT + 26
    draw.line((STRIP_X, bracket_y, right, bracket_y), fill=rgb(FAINT), width=2)
    for x in (STRIP_X, right):
        draw.line((x, bracket_y, x, bracket_y - 10), fill=rgb(FAINT), width=2)
    draw.text(((STRIP_X + right) / 2, BIT_LABEL_Y), "23 bits", font=font(28),
              fill=rgb(MUTED), anchor="ms")


PARTS: list[Part] = [
        ("23", TEXT, True, True),
        (" stored", MUTED, False, False),
        ("   +   ", MUTED, False, False),
        ("1 implicit", AMBER, True, False),
        ("   =   ", MUTED, False, False),
        ("24 bits of precision", TEAL, True, False),
]
EQ_SIZE = 40


def draw_equation(draw: ImageDraw.ImageDraw) -> None:
    """The sum at the bottom: 23 stored plus the implicit one, 24 of precision."""
    draw.rounded_rectangle(CARD_BOX, radius=22, fill=rgb(CARD), outline=rgb(HAIR), width=2)
    rich_center(draw, W / 2, EQUATION_Y, PARTS, size=EQ_SIZE)


# ---------------------------------------------------------------------------
# 4. Composition
# ---------------------------------------------------------------------------
def draw() -> Image.Image:
    """Compose the diagram and return the final image."""
    image, canvas = new_canvas()

    canvas.text((MARGIN, TITLE_Y), "The free bit", font=font(60, bold=True),
                fill=rgb(TEXT), anchor="lm")
    canvas.text((MARGIN, SUBTITLE_Y), "it is always 1, so it is not stored",
                font=font(32), fill=rgb(MUTED), anchor="lm")

    draw_strip(canvas)
    draw_labels(canvas)
    draw_equation(canvas)

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

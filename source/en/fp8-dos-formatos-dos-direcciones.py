""""FP8: two formats, two directions"

Diagram proposed by the diagram studio from the recommendation
«FP8 with two formats and two directions»: the same 8-bit byte is split in two
ways (E4M3: 1/4/3; E5M2: 1/5/2) and each split is used in a different direction
of the network (E4M3 forward with weights and activations; E5M2 backward with
the gradients).

Self-contained: Pillow only. `python3 source.py` writes out.png and
`DIAGRAM_OUT=versions/v1.png python3 source.py` writes where the studio says.
"""

from __future__ import annotations

import math
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# 1. Palette and typography (PyramidSpace dark theme)
# ---------------------------------------------------------------------------
BG = "#090B0D"          # --bg
CARD = "#111519"        # --surface
ELEV = "#20262D"        # --surface-3
LINE_CARD = "#262A2E"   # 1 px border over card
LINE_STRONG = "#3F4142" # strong border
TEXT = "#F8FAFC"
MUTED = "#94A3B8"
TEAL = "#2DD4BF"        # primary accent (mantissa)
AMBER = "#F59E0B"       # secondary accent (backpropagation)
GREEN = "#4ADE80"       # success (forward propagation)
RED = "#F87171"         # sign

SIGN = RED
EXP = "#94A3B8"
MANT = TEAL

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
    """Load Liberation Sans (the blog sans) or DejaVu Sans Mono."""
    if mono:
        path = DEJAVU / ("DejaVuSansMono-Bold.ttf" if bold else "DejaVuSansMono.ttf")
    else:
        path = LIBERATION / ("LiberationSans-Bold.ttf" if bold else "LiberationSans-Regular.ttf")
    try:
        return ImageFont.truetype(str(path), size)
    except OSError:
        try:
            fallback = DEJAVU / ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf")
            return ImageFont.truetype(str(fallback), size)
        except OSError:
            return ImageFont.load_default()


def new_canvas() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    """Dark canvas without frame (the blog CSS rounds the corners)."""
    image = Image.new("RGB", (W, H), rgb(BG))
    return image, ImageDraw.Draw(image)


def card(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, lane: str) -> None:
    """Card with the edge in its direction color."""
    draw.rounded_rectangle((x, y, x + w, y + h), radius=24, fill=rgb(CARD),
                           outline=rgb(LINE_CARD), width=2)
    draw.rounded_rectangle((x + 2, y + 22, x + 9, y + h - 22), radius=3, fill=rgb(lane))


def arrow(draw: ImageDraw.ImageDraw, start, end, color: str, width: int = 7, head: int = 28) -> None:
    """Straight arrow with a triangular head."""
    draw.line((start, end), fill=rgb(color), width=width)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    left = (end[0] - head * math.cos(angle - math.pi / 7), end[1] - head * math.sin(angle - math.pi / 7))
    right = (end[0] - head * math.cos(angle + math.pi / 7), end[1] - head * math.sin(angle + math.pi / 7))
    draw.polygon([end, left, right], fill=rgb(color))


def pill(draw: ImageDraw.ImageDraw, x: int, cy: int, text: str, color: str,
         base: str = BG, size: int = 28) -> int:
    """Compact pill with a faint fill of the color and text in the full color."""
    face = font(size, bold=True)
    width = int(draw.textlength(text, font=face) + 44)
    height = size + 26
    draw.rounded_rectangle((x, cy - height / 2, x + width, cy + height / 2), radius=height / 2,
                           fill=mix(color, base, 0.86), outline=mix(color, base, 0.52), width=2)
    draw.text((x + width / 2, cy), text, font=face, fill=rgb(color), anchor="mm")
    return width


def rich_text(draw: ImageDraw.ImageDraw, x: int, cy: int,
              parts: list[tuple[str, str, bool]], size: int) -> None:
    """Text in several runs with their own color and weight, left-aligned."""
    cursor = x
    for text, color, bold in parts:
        face = font(size, bold=bold)
        draw.text((cursor, cy), text, font=face, fill=rgb(color), anchor="lm")
        cursor += draw.textlength(text, font=face)


# ---------------------------------------------------------------------------
# 3. Diagram pieces
# ---------------------------------------------------------------------------
CELL_W, CELL_H, CELL_GAP = 62, 68, 6
HEADER_OFF = 52
STRIP_OFF = 112
BALANCE_OFF = 300


def bit_strip(draw: ImageDraw.ImageDraw, x: int, y: int,
              fields: list[tuple[str, int, str]]) -> None:
    """Eight bit boxes grouped by field, with their bracket and name."""
    cursor = x
    groups: list[tuple[str, int, int, str]] = []
    bit = 7
    for name, count, color in fields:
        group_x = cursor
        group_w = count * CELL_W + (count - 1) * CELL_GAP
        for index in range(count):
            cell_x = cursor + index * (CELL_W + CELL_GAP)
            draw.rounded_rectangle((cell_x, y, cell_x + CELL_W, y + CELL_H), radius=12,
                                   fill=rgb(color))
            draw.text((cell_x + CELL_W / 2, y + CELL_H / 2), str(bit),
                      font=font(30, bold=True, mono=True), fill=rgb(BG), anchor="mm")
            bit -= 1
        cursor = group_x + group_w + CELL_GAP
        groups.append((name, group_x, group_w, color))

    bracket_y = y + CELL_H + 16
    for name, group_x, group_w, color in groups:
        draw.line((group_x, bracket_y, group_x + group_w, bracket_y), fill=rgb(color), width=3)
        draw.line((group_x, bracket_y, group_x, bracket_y + 9), fill=rgb(color), width=3)
        draw.line((group_x + group_w, bracket_y, group_x + group_w, bracket_y + 9),
                  fill=rgb(color), width=3)
        draw.text((group_x + group_w / 2, bracket_y + 24), name,
                  font=font(28), fill=rgb(color), anchor="mm")


def format_card(draw: ImageDraw.ImageDraw, y0: int, name: str, max_text: str,
                fields: list[tuple[str, int, str]], pill_text: str, pill_color: str,
                note_parts: list[tuple[str, str, bool]]) -> None:
    """Format card: name, max, bit strip and balance on one line."""
    x0, w, h = MARGIN, CARD_W, CARD_H
    lane = GREEN if pill_color == GREEN else AMBER
    card(draw, x0, y0, w, h, lane)

    draw.text((x0 + 40, y0 + HEADER_OFF), name, font=font(46, bold=True), fill=rgb(TEXT), anchor="lm")
    draw.text((x0 + w - 40, y0 + HEADER_OFF + 2), max_text, font=font(36, bold=True),
              fill=rgb(TEXT), anchor="rm")

    bit_strip(draw, x0 + 40, y0 + STRIP_OFF, fields)

    pill(draw, x0 + 40, y0 + BALANCE_OFF, pill_text, pill_color, base=CARD, size=30)

    # Right-aligned note, with the numbers in white.
    x_right = x0 + w - 40
    cursor = x_right
    for text, color, bold in reversed(note_parts):
        face = font(28, bold=bold)
        cursor -= draw.textlength(text, font=face)
        draw.text((cursor, y0 + BALANCE_OFF), text, font=face, fill=rgb(color), anchor="lm")


# ---------------------------------------------------------------------------
# 4. Composition
# ---------------------------------------------------------------------------
CARD_W, CARD_H = 620, 360
CARD_Y = (320, 730)
FWD_Y = CARD_Y[0] + CARD_H // 2      # 500
BWD_Y = CARD_Y[1] + CARD_H // 2      # 910
FLOW_X0, FLOW_X1 = 724, 1710
BLOCK = (1120, 450, 1420, 960)


def draw() -> Image.Image:
    """Compose the diagram and return the final image."""
    image, canvas = new_canvas()

    # Header
    canvas.text((MARGIN, 124), "FP8: two formats, two directions",
                font=font(62, bold=True), fill=rgb(TEXT), anchor="lm")
    rich_text(canvas, MARGIN, 200, [
        ("E4M3", GREEN, True),
        (" forward · ", MUTED, False),
        ("E5M2", AMBER, True),
        (" backward", MUTED, False),
    ], size=32)

    # Format cards (left)
    format_card(
        canvas, CARD_Y[0], "E4M3", "max 448",
        [("sign", 1, SIGN), ("exponent", 4, EXP), ("mantissa", 3, MANT)],
        "+ precision", GREEN,
        [("no inf · ", MUTED, False), ("1 NaN", TEXT, True)],
    )
    format_card(
        canvas, CARD_Y[1], "E5M2", "max 57,344",
        [("sign", 1, SIGN), ("exponent", 5, EXP), ("mantissa", 2, MANT)],
        "+ range", AMBER,
        [("steps of ", MUTED, False), ("25%", TEXT, True)],
    )

    # Flows: forward to the right, backward to the left
    arrow(canvas, (FLOW_X0, FWD_Y), (FLOW_X1, FWD_Y), GREEN)
    arrow(canvas, (FLOW_X1, BWD_Y), (FLOW_X0, BWD_Y), AMBER)

    # Central block crossed by the two flows
    canvas.rounded_rectangle(BLOCK, radius=32, fill=rgb(ELEV), outline=rgb(LINE_STRONG), width=2)
    canvas.text(((BLOCK[0] + BLOCK[2]) / 2, (BLOCK[1] + BLOCK[3]) / 2), "block",
                font=font(44), fill=rgb(MUTED), anchor="mm")

    # Which tensors go in each direction
    pill(canvas, 738, FWD_Y - 50, "weights and activations", GREEN, base=BG, size=30)
    pill(canvas, 1452, BWD_Y + 50, "gradients", AMBER, base=BG, size=30)

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

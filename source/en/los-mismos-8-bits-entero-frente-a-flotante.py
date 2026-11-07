"""The same 8 bits: integer vs floating point

Diagram proposed by the diagram studio from the recommendation
«The same eight bits: integer vs floating point»: two ways of dividing the same
byte. The integer spends 1 bit on the sign and 7 on the value and splits the
range into equal steps; floating point reserves 1 bit for the sign, 4 for the
exponent and 3 for the mantissa, and its steps grow with the exponent.

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
AMBER = "#F59E0B"
TEAL = "#2DD4BF"
TEAL_LIGHT = "#5EEAD4"

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
    """Liberation Sans for labels and DejaVu Sans Mono for the bits."""
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


def rich_text(draw: ImageDraw.ImageDraw, x: int, cy: int,
              parts: list[tuple[str, str, bool]], size: int) -> None:
    """Text in runs with their own color and weight, left-aligned."""
    cursor = x
    for text, color, bold in parts:
        face = font(size, bold=bold)
        draw.text((cursor, cy), text, font=face, fill=rgb(color), anchor="lm")
        cursor += draw.textlength(text, font=face)


def rich_center(draw: ImageDraw.ImageDraw, cx: float, cy: int,
                parts: list[tuple[str, str, bool]], size: int) -> None:
    """Like `rich_text`, but centered on `cx`."""
    total = sum(draw.textlength(text, font=font(size, bold=bold)) for text, _, bold in parts)
    rich_text(draw, round(cx - total / 2), cy, parts, size)


# ---------------------------------------------------------------------------
# 3. Diagram pieces
# ---------------------------------------------------------------------------
CELL, GAP, NBITS = 96, 6, 8
CARD_X, CARD_W, CARD_H = MARGIN, 1620, 340
CARD_YS = (260, 650)
STRIP_X = CARD_X + 34
STRIP_W = NBITS * CELL + (NBITS - 1) * GAP      # 810
STRIP_CX = STRIP_X + STRIP_W / 2                # 529

TITLE_Y, SUB_Y = 118, 194
CLOSING_CY = 1070

ROWS = (
    {   # INT8: 1 sign bit + 7 value bits
        "label": "INT8",
        "fields": (
            {"name": "sign", "count": 1, "color": AMBER, "text": CELL_TEXT_AMBER},
            {"name": "value (7 bits)", "count": 7, "color": TEAL, "text": CELL_TEXT_TEAL},
        ),
        "grid_color": TEAL,
        "positions": [STRIP_W * i / 5 for i in range(6)],
        "phrase": (("256 codes", TEXT, True), (" evenly spaced", MUTED, False)),
        "caption": ("the integer spends the whole byte", "on the value"),
        "caption_color": TEAL,
    },
    {   # FP8 E4M3: 1 sign, 4 exponent and 3 mantissa bits
        "label": "FP8 E4M3",
        "fields": (
            {"name": "sign", "count": 1, "color": AMBER, "text": CELL_TEXT_AMBER},
            {"name": "exponent (4 bits)", "count": 4, "color": TEAL_LIGHT, "text": CELL_TEXT_TEAL},
            {"name": "mantissa (3 bits)", "count": 3, "color": TEAL, "text": CELL_TEXT_TEAL},
        ),
        "grid_color": TEAL_LIGHT,
        "positions": [0, 26, 78, 182, 390, 802],
        "phrase": (("steps that grow", TEXT, False), (" with the exponent", MUTED, False)),
        "caption": ("floating point reserves bits", "for the scale"),
        "caption_color": TEAL_LIGHT,
    },
)


def draw_strip(draw: ImageDraw.ImageDraw, row: dict, y: int) -> None:
    """Eight little bit boxes and, above them, each field name in its color."""
    x = STRIP_X
    bit = NBITS - 1
    for field in row["fields"]:
        group_w = field["count"] * CELL + (field["count"] - 1) * GAP
        for index in range(field["count"]):
            cell_x = x + index * (CELL + GAP)
            draw.rounded_rectangle((cell_x, y, cell_x + CELL, y + CELL), radius=14,
                                   fill=rgb(field["color"]))
            draw.text((cell_x + CELL / 2, y + CELL / 2), str(bit),
                      font=font(24, bold=True, mono=True), fill=rgb(field["text"]), anchor="mm")
            bit -= 1
        draw.text((x + group_w / 2, y - 26), field["name"],
                  font=font(26), fill=rgb(field["color"]), anchor="mm")
        x += group_w + GAP


def draw_ruler(draw: ImageDraw.ImageDraw, row: dict, y: int) -> None:
    """Brace under the strip with the sample marks: equal or ever more spread out."""
    draw.line((STRIP_X, y, STRIP_X + STRIP_W, y), fill=rgb(AXIS), width=3)
    for position in row["positions"]:
        x = STRIP_X + position
        draw.ellipse((x - 8, y - 8, x + 8, y + 8), fill=rgb(row["grid_color"]))
    for x in (STRIP_X, STRIP_X + STRIP_W):
        draw.line((x, y, x, y + 9), fill=rgb(AXIS), width=2)


def pill(draw: ImageDraw.ImageDraw, right: int, cy: int, text: str, color: str,
         base: str = BG, size: int = 30) -> None:
    """Compact label aligned to the right."""
    face = font(size, bold=True)
    width = int(draw.textlength(text, font=face) + 44)
    height = size + 26
    left = right - width
    draw.rounded_rectangle((left, cy - height / 2, right, cy + height / 2), radius=height / 2,
                           fill=mix(color, base, 0.86), outline=mix(color, base, 0.52), width=2)
    draw.text((left + width / 2, cy), text, font=face, fill=rgb(color), anchor="mm")


# ---------------------------------------------------------------------------
# 4. Composition
# ---------------------------------------------------------------------------
def draw() -> Image.Image:
    """Compose the diagram and return the final image."""
    image, canvas = new_canvas()

    canvas.text((MARGIN, TITLE_Y), "The same 8 bits: integer vs floating point",
                font=font(62, bold=True), fill=rgb(TEXT), anchor="lm")
    canvas.text((MARGIN, SUB_Y), "Two ways to split a byte",
                font=font(30), fill=rgb(MUTED), anchor="lm")

    for row, card_y in zip(ROWS, CARD_YS):
        canvas.rounded_rectangle((CARD_X, card_y, CARD_X + CARD_W, card_y + CARD_H),
                                 radius=24, fill=rgb(CARD), outline=rgb(HAIR), width=2)

        canvas.text((CARD_X + 34, card_y + 52), row["label"],
                    font=font(44, bold=True), fill=rgb(TEXT), anchor="lm")

        draw_strip(canvas, row, card_y + 128)
        draw_ruler(canvas, row, card_y + 270)

        rich_center(canvas, STRIP_CX, card_y + 304, list(row["phrase"]), size=28)

        # Each philosophy's sentence, on the right and centered on the strip
        strip_center = card_y + 128 + CELL / 2
        caption_x = CARD_X + 910
        canvas.rounded_rectangle((caption_x, strip_center - 48, caption_x + 4, strip_center + 48),
                                 radius=2, fill=rgb(row["caption_color"]))
        for line_index, line in enumerate(row["caption"]):
            canvas.text((caption_x + 28, strip_center - 24 + line_index * 48), line,
                        font=font(40), fill=rgb(MUTED), anchor="lm")

    pill(canvas, W - MARGIN, CLOSING_CY, "same byte, two philosophies", TEAL)

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

"""Bit map of the numeric formats.

Blog figure for PyramidSpace: the five formats from the table (FP32, FP16,
BF16, FP8 E4M3, FP8 E5M2) on the same bit ruler, to see at a glance how each
one splits its budget between sign, exponent and mantissa.

Style decisions (user style memory):
- Blog dark theme palette, not the studio's inherited palette.
- Minimal text: title, short names, bit trios and legend. The numeric ranges
  are already in the table that precedes the figure in the post.

Recommended location: "After the table that starts with «|Format|Sign / Exp. / Mantissa|Max normal|Min normal|»"
"""

from __future__ import annotations

import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# 1. Blog dark theme palette and typography
# ---------------------------------------------------------------------------
BG = "#090B0D"            # dark theme --bg
TEXT = "#F8FAFC"          # --text
MUTED = "#94A3B8"         # --muted
FAINT = "#64748B"         # third text level
TEAL = "#2DD4BF"          # --accent (range)
AMBER = "#F59E0B"         # --accent-2 (precision)
BORDER = "#1F2123"        # --border composited over the background
BORDER_SOFT = "#262A2E"   # --border composited over surface
BORDER_STRONG = "#3F4142" # strong border

SIGN_FILL = "#94A3B8"     # the bit that never changes, deliberately muted
FIELD_FILL = (SIGN_FILL, TEAL, AMBER)

W, H = 1800, 1200
MARGIN = 90

FONT_SANS = [
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]
FONT_SANS_BOLD = [
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]
FONT_MONO = [
    "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationMono-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
]

# Metadata filled in by the studio; kept for traceability.
TITLE = "Bit map of the numeric formats"
LOCATION = "After the table that starts with «|Format|Sign / Exp. / Mantissa|Max normal|Min normal|»"
CONTENT = (
    "Puts the five formats from the table on a single bit ruler so you can see how "
    "each one divides its budget between sign, exponent and mantissa."
)
SOURCE = "diagram-studio"


def rgb(value: str) -> tuple[int, int, int]:
    """Convert `#RRGGBB` to an RGB tuple."""
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def _first_available(paths: list[str]) -> str:
    for path in paths:
        if Path(path).is_file():
            return path
    return paths[-1]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Load the neutral sans (Liberation Sans, DejaVu fallback)."""
    path = _first_available(FONT_SANS_BOLD if bold else FONT_SANS)
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def mono(size: int) -> ImageFont.FreeTypeFont:
    """Load a monospaced face for the bit counters."""
    path = _first_available(FONT_MONO)
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


# ---------------------------------------------------------------------------
# 2. Canvas and shapes
# ---------------------------------------------------------------------------
def new_canvas(width: int = W, height: int = H) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    """Create the dark canvas with its `ImageDraw`."""
    image = Image.new("RGB", (width, height), rgb(BG))
    return image, ImageDraw.Draw(image)


# ---------------------------------------------------------------------------
# 3. Diagram data and geometry
# ---------------------------------------------------------------------------
FORMATS = (
    ("FP32", (1, 8, 23)),
    ("FP16", (1, 5, 10)),
    ("BF16", (1, 8, 7)),
    ("E4M3", (1, 4, 3)),
    ("E5M2", (1, 5, 2)),
)

STRIP_X = 360        # common left axis of all strips
ROW_Y0 = 352         # first strip
ROW_PITCH = 124      # gap between strips
CELL_W = 36          # width of one bit cell
CELL_H = 72          # cell height
CELL_PITCH = 40      # horizontal pitch: cell + gap
CELL_RADIUS = 8
COUNT_X = 210        # column of the bit trios
COUNT_SIZE = 30

RULER_BASELINE = 232
RULER_AXIS_Y = 244
RULER_TICK = 12
LEGEND_Y = 1044


def draw_ruler(canvas: ImageDraw.ImageDraw) -> None:
    """Shared bit ruler: ticks every 8 bits from the common axis."""
    end_x = STRIP_X + 32 * CELL_PITCH - (CELL_PITCH - CELL_W)
    canvas.text((MARGIN, RULER_BASELINE), "bits", font=font(24), fill=rgb(FAINT), anchor="ls")
    canvas.line((MARGIN, RULER_AXIS_Y, end_x, RULER_AXIS_Y), fill=rgb(BORDER), width=2)
    for mark in range(0, 33, 8):
        x = STRIP_X + mark * CELL_PITCH
        if mark == 32:
            x = end_x
        canvas.line((x, RULER_AXIS_Y, x, RULER_AXIS_Y + RULER_TICK), fill=rgb(BORDER_STRONG), width=2)
        canvas.text((x, RULER_BASELINE), str(mark), font=font(26), fill=rgb(MUTED), anchor="ms")


def draw_counts(canvas: ImageDraw.ImageDraw, x: int, y: int, counts: tuple[int, int, int]) -> None:
    """Trio 1·8·23 with each figure in its field color."""
    face = mono(COUNT_SIZE)
    cursor = float(x)
    for index, count in enumerate(counts):
        piece = str(count)
        canvas.text((cursor, y), piece, font=face, fill=rgb(FIELD_FILL[index]), anchor="lm")
        cursor += canvas.textlength(piece, font=face)
        if index < len(counts) - 1:
            canvas.text((cursor + 7, y), "·", font=face, fill=rgb(FAINT), anchor="lm")
            cursor += 7 + canvas.textlength("·", font=face) + 7


def draw_strip(canvas: ImageDraw.ImageDraw, top: int, counts: tuple[int, int, int]) -> None:
    """One bit per cell strip, colored by field."""
    bit = 0
    for field_index, count in enumerate(counts):
        for _ in range(count):
            left = STRIP_X + bit * CELL_PITCH
            canvas.rounded_rectangle(
                (left, top, left + CELL_W, top + CELL_H),
                radius=CELL_RADIUS,
                fill=rgb(FIELD_FILL[field_index]),
            )
            bit += 1


def draw_legend(canvas: ImageDraw.ImageDraw) -> None:
    """Legend of the fields and what each one means."""
    entries = (
        ("sign", SIGN_FILL),
        ("exponent = range", TEAL),
        ("mantissa = precision", AMBER),
    )
    x = MARGIN
    for label, color in entries:
        canvas.rounded_rectangle((x, LEGEND_Y - 14, x + 28, LEGEND_Y + 14), radius=7, fill=rgb(color))
        canvas.text((x + 40, LEGEND_Y), label, font=font(32), fill=rgb(MUTED), anchor="lm")
        x += 40 + canvas.textlength(label, font=font(32)) + 64


# ---------------------------------------------------------------------------
# 4. Diagram composition
# ---------------------------------------------------------------------------
def draw() -> Image.Image:
    """Compose the diagram. Returns the final image."""
    image, canvas = new_canvas()

    # Header
    canvas.text((MARGIN, 70), "The bit budget: from FP32 to FP8",
                font=font(58, bold=True), fill=rgb(TEXT))

    draw_ruler(canvas)

    # Five strips on the same axis
    for index, (name, counts) in enumerate(FORMATS):
        top = ROW_Y0 + index * ROW_PITCH
        middle = top + CELL_H // 2
        canvas.text((MARGIN, middle), name, font=font(36, bold=True), fill=rgb(TEXT), anchor="lm")
        draw_counts(canvas, COUNT_X, middle, counts)
        draw_strip(canvas, top, counts)

    draw_legend(canvas)

    return image


def save(image: Image.Image, path: str | Path | None = None) -> Path:
    """Save the PNG to `DIAGRAM_OUT` (or `out.png` when run by hand)."""
    target = Path(path or os.environ.get("DIAGRAM_OUT", "out.png"))
    target.parent.mkdir(parents=True, exist_ok=True)
    image.save(target, format="PNG")
    return target


if __name__ == "__main__":
    destination = save(draw())
    print(f"diagram written to {destination}")

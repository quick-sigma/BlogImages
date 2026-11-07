"""Memory budget of an LLM

Diagram proposed by the diagram studio from a blog recommendation. This file is
self-contained: it is copied into the job folder, the agent edits `draw()` and
`diagram_render` runs it. The image is published next to the AVIF in `source/`
of the BlogImages repository, so it must run with Pillow alone:

    python3 source.py            # writes out.png
    DIAGRAM_OUT=versions/v1.png python3 source.py

Recommended location: "Below the text «a 4B-parameter model needs about 8 GB just for its weights, not counting context or the system»"
Recommended content: "Compares how much memory the weights of a model take depending on the parameters and the bytes per parameter, and shows why loading a large model in 16 bits is unviable."

Style: blog dark theme palette (PyramidSpace). Background #090B0D, cards
#111519, borders #1F2123, text #F8FAFC, secondary #94A3B8, teal accent #2DD4BF,
amber #F59E0B and green #4ADE80. Neutral sans (Liberation Sans, DejaVu fallback),
large text for the 720 px reading column. Canvas 1800 x 1200.
"""

from __future__ import annotations

import math
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# 1. Blog dark theme palette and typography
# ---------------------------------------------------------------------------
BG = "#090B0D"          # --bg of the dark theme
CARD = "#111519"        # --surface
CARD_RAISED = "#171C21" # --surface-2
BORDER = "#1F2123"      # --border (white 9%) composited over --bg
BORDER_SOFT = "#262A2E" # --border composited over --surface
BORDER_STRONG = "#3F4142"
TEXT = "#F8FAFC"        # --text
MUTED = "#94A3B8"       # --muted
FAINT = "#64748B"
TEAL = "#2DD4BF"        # --accent
AMBER = "#F59E0B"       # --accent-2
GREEN = "#4ADE80"       # --success
RED = "#F87171"         # --danger
ON_TEAL = "#06201C"     # text over teal fill

# Legacy house-skeleton aliases, kept for compatibility.
CYAN = TEAL
CYAN_SOFT = "#5EEAD4"
AMBER_SOFT = "#D97706"
LINE = BORDER

W, H = 1800, 1200
MARGIN = 90

FONT_CANDIDATES = {
    False: (
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ),
    True: (
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ),
}

# Metadata filled in by the studio; kept for traceability.
TITLE = "Memory budget of an LLM"
LOCATION = "Below the text «a 4B-parameter model needs about 8 GB just for its weights, not counting context or the system»"
CONTENT = "Compares how much memory the weights of a model take depending on the parameters and the bytes per parameter, and shows why loading a large model in 16 bits is unviable.\n\nComponents: two groups of comparable horizontal bars, one «4B parameters» and one «671B parameters (DeepSeek-V3)»; in each group, three bars per format (FP16, FP8, INT4/FP4) with their size; a horizontal gigabyte axis on a logarithmic scale; an empty card «+ context + system» that recalls what is not counted; a callout label «quantize = fewer bits per number».\nStyle: blog dark theme palette; FP16 in teal #2DD4BF, FP8 in amber #F59E0B, INT4/FP4 in green #4ADE80; neutral sans, 58 px title and labels of 22 px or more; bars with 10 px radius and a faint grid, no shadows.\nPositioning: title and subtitle at the top; the «4B» group above and the «671B» group below, both aligned to the same horizontal gigabyte axis on the left; the «+ context + system» card at the bottom right, in faint gray; color legend under the header.\nTexts in the image: title «The memory budget of a model»; subtitle «Model weights only, not counting context or the system»; labels «4B parameters», «671B parameters · DeepSeek-V3», «FP16», «FP8», «INT4/FP4», «8 GB», «4 GB», «2 GB», «≈ 1.3 TB», «≈ 0.67 TB», «≈ 0.34 TB»; callout «quantize = fewer bits per number»; box «+ context + system / not included in these figures»; footnotes about the logarithmic scale and bytes per parameter."
SOURCE = "diagram-studio"


def rgb(value: str) -> tuple[int, int, int]:
    """Convert `#RRGGBB` to an RGB tuple."""
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


_FONT_CACHE: dict[tuple[int, bool], ImageFont.FreeTypeFont] = {}


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Load Liberation Sans (DejaVu as fallback) with cache."""
    key = (size, bold)
    if key not in _FONT_CACHE:
        face = None
        for path in FONT_CANDIDATES[bold]:
            try:
                face = ImageFont.truetype(path, size)
                break
            except OSError:
                continue
        _FONT_CACHE[key] = face or ImageFont.load_default()
    return _FONT_CACHE[key]


def mix(c1: str, c2: str, t: float) -> tuple[int, int, int]:
    """Interpolate two hex colors; `t=0` returns `c1`."""
    t = max(0.0, min(1.0, t))
    a, b = rgb(c1), rgb(c2)
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


# ---------------------------------------------------------------------------
# 2. Canvas and shapes
# ---------------------------------------------------------------------------
def new_canvas(width: int = W, height: int = H) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    """Create the dark canvas with its `ImageDraw`."""
    image = Image.new("RGB", (width, height), rgb(BG))
    return image, ImageDraw.Draw(image)


def rounded_box(draw: ImageDraw.ImageDraw, xy, radius: int = 24, fill: str = CARD,
                outline: str = BORDER, width: int = 2) -> None:
    """Draw a rounded card."""
    draw.rounded_rectangle(xy, radius=radius, fill=rgb(fill), outline=rgb(outline), width=width)


def _round_rect_points(x0, y0, x1, y1, radius: int, step: float = 3.0):
    """Sample the perimeter of a rounded rectangle, in order."""
    r = radius
    points: list[tuple[float, float]] = []

    def add_line(a, b):
        length = math.hypot(b[0] - a[0], b[1] - a[1])
        count = max(1, int(length / step))
        for i in range(count + 1):
            t = i / count
            points.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))

    def add_arc(cx, cy, start, end):
        count = max(8, int(abs(end - start) * r / 180 / step) + 2)
        for i in range(count + 1):
            angle = math.radians(start + (end - start) * i / count)
            points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))

    add_line((x0 + r, y0), (x1 - r, y0))
    add_arc(x1 - r, y0 + r, -90, 0)
    add_line((x1, y0 + r), (x1, y1 - r))
    add_arc(x1 - r, y1 - r, 0, 90)
    add_line((x1 - r, y1), (x0 + r, y1))
    add_arc(x0 + r, y1 - r, 90, 180)
    add_line((x0, y1 - r), (x0, y0 + r))
    add_arc(x0 + r, y0 + r, 180, 270)
    return points


def dashed_box(draw: ImageDraw.ImageDraw, xy, radius: int = 20,
               outline: str = BORDER_STRONG, width: int = 2,
               dash: int = 16, gap: int = 12) -> None:
    """Rounded rectangle with a dashed outline (for the empty box)."""
    x0, y0, x1, y1 = xy
    points = _round_rect_points(x0, y0, x1, y1, radius)
    cumulative = [0.0]
    for index in range(1, len(points)):
        cumulative.append(cumulative[-1] + math.hypot(
            points[index][0] - points[index - 1][0],
            points[index][1] - points[index - 1][1],
        ))
    total = cumulative[-1]
    period = dash + gap

    start = 0.0
    while start < total:
        end = min(start + dash, total)
        index = 0
        while index < len(points) - 1 and cumulative[index + 1] <= start:
            index += 1
        position = start
        while position < end - 0.01 and index < len(points) - 1:
            segment = cumulative[index + 1] - cumulative[index]
            if segment <= 0:
                index += 1
                continue
            stop = min(end, cumulative[index + 1])
            t0 = (position - cumulative[index]) / segment
            t1 = (stop - cumulative[index]) / segment
            draw.line(
                (points[index][0] + (points[index + 1][0] - points[index][0]) * t0,
                 points[index][1] + (points[index + 1][1] - points[index][1]) * t0,
                 points[index][0] + (points[index + 1][0] - points[index][0]) * t1,
                 points[index][1] + (points[index + 1][1] - points[index][1]) * t1),
                fill=rgb(outline), width=width,
            )
            position = stop
            index += 1
        start += period


def draw_text_block(draw: ImageDraw.ImageDraw, x: int, y: int, text: str,
                    face, color: str, max_width: int, spacing: int = 8) -> int:
    """Draw word-wrapped text and return the final Y."""
    for paragraph in text.split("\n"):
        words = paragraph.split()
        line = ""
        for word in words:
            candidate = f"{line} {word}".strip()
            if draw.textlength(candidate, font=face) <= max_width or not line:
                line = candidate
            else:
                draw.text((x, y), line, font=face, fill=rgb(color))
                y += face.size + spacing
                line = word
        if line:
            draw.text((x, y), line, font=face, fill=rgb(color))
            y += face.size + spacing
    return y


def arrow(draw: ImageDraw.ImageDraw, start: tuple[float, float], end: tuple[float, float],
          color: str = AMBER, width: int = 4, head: int = 18) -> None:
    """Straight arrow with a triangular head."""
    draw.line((start, end), fill=rgb(color), width=width)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    left = (end[0] - head * math.cos(angle - math.pi / 7), end[1] - head * math.sin(angle - math.pi / 7))
    right = (end[0] - head * math.cos(angle + math.pi / 7), end[1] - head * math.sin(angle + math.pi / 7))
    draw.polygon([end, left, right], fill=rgb(color))


def badge(draw: ImageDraw.ImageDraw, x: int, y: int, text: str, fill: str = TEAL,
          text_color: str = ON_TEAL, size: int = 22) -> int:
    """Compact one-line label; returns its width."""
    face = font(size, bold=True)
    width = draw.textlength(text, font=face) + 36
    draw.rounded_rectangle((x, y, x + width, y + size + 16), radius=(size + 16) // 2,
                           fill=rgb(fill))
    draw.text((x + 18, y + (size + 16) / 2), text, font=face, fill=rgb(text_color), anchor="lm")
    return int(width)


# ---------------------------------------------------------------------------
# 3. Chart geometry
# ---------------------------------------------------------------------------
AXIS_X0 = 310               # 1 GB
AXIS_X1 = 1620              # 3000 GB
AXIS_MIN_GB = 1
AXIS_MAX_GB = 3000
CARD_X0, CARD_X1 = 90, 1710
CARD_Y0, CARD_Y1 = 296, 1000
GRID_BOTTOM = 938

TICKS = ((1, "1 GB"), (10, "10 GB"), (100, "100 GB"), (1000, "1 TB"))

GROUPS = (
    {
        "label": "4B parameters",
        "y": 368,
        "bars": (
            ("FP16", 8, "8 GB", TEAL),
            ("FP8", 4, "4 GB", AMBER),
            ("INT4/FP4", 2, "2 GB", GREEN),
        ),
    },
    {
        "label": "671B parameters · DeepSeek-V3",
        "y": 690,
        "bars": (
            ("FP16", 1342, "≈ 1.3 TB", TEAL),
            ("FP8", 671, "≈ 0.67 TB", AMBER),
            ("INT4/FP4", 335.5, "≈ 0.34 TB", GREEN),
        ),
    },
)


def gb_to_x(value_gb: float) -> float:
    """Project a size in GB onto the logarithmic axis."""
    lo, hi = math.log10(AXIS_MIN_GB), math.log10(AXIS_MAX_GB)
    return AXIS_X0 + (math.log10(value_gb) - lo) / (hi - lo) * (AXIS_X1 - AXIS_X0)


# ---------------------------------------------------------------------------
# 4. Diagram composition
# ---------------------------------------------------------------------------
def draw() -> Image.Image:
    """Compose the diagram. Returns the final image."""
    image, canvas = new_canvas()

    # Header
    canvas.text((MARGIN, 54), "The memory budget of a model",
                font=font(58, bold=True), fill=rgb(TEXT))
    canvas.text((MARGIN, 136), "Model weights only, not counting context or the system",
                font=font(30), fill=rgb(MUTED))
    deck = (
        ("With the same bytes per parameter, 671B needs ", MUTED, False),
        ("≈168×", TEAL, True),
        (" the memory of 4B.", MUTED, False),
    )
    dx = MARGIN
    for text, color, bold in deck:
        face = font(24, bold=bold)
        canvas.text((dx, 178), text, font=face, fill=rgb(color))
        dx += canvas.textlength(text, font=face)
    canvas.line((MARGIN, 222, W - MARGIN, 222), fill=rgb(BORDER), width=2)

    # Format legend
    legend = (("FP16 · 2 B", TEAL), ("FP8 · 1 B", AMBER), ("INT4/FP4 · 0.5 B", GREEN))
    legend_face = font(24)
    lx = MARGIN
    for label, color in legend:
        canvas.rounded_rectangle((lx, 244, lx + 26, 270), radius=7, fill=rgb(color))
        canvas.text((lx + 38, 257), label, font=legend_face, fill=rgb(MUTED), anchor="lm")
        lx += 38 + canvas.textlength(label, font=legend_face) + 48

    # Callout
    badge(canvas, W - MARGIN - (canvas.textlength("quantize = fewer bits per number",
                                                   font=font(22, bold=True)) + 36), 238,
          "quantize = fewer bits per number")

    # Chart card
    rounded_box(canvas, (CARD_X0, CARD_Y0, CARD_X1, CARD_Y1), radius=28, fill=CARD,
                outline=BORDER, width=2)

    # Vertical grid
    for value, _ in TICKS:
        gx = gb_to_x(value)
        canvas.line((gx, CARD_Y0 + 40, gx, GRID_BOTTOM), fill=rgb(BORDER_SOFT), width=2)

    # Groups and bars
    for group in GROUPS:
        canvas.text((CARD_X0 + 20, group["y"] - 46), group["label"],
                    font=font(30, bold=True), fill=rgb(TEXT))
        for index, (fmt, gb, value_label, color) in enumerate(group["bars"]):
            top = group["y"] + index * 86
            end = gb_to_x(gb)
            canvas.rounded_rectangle((AXIS_X0, top, end, top + 64), radius=10, fill=rgb(color))
            canvas.text((AXIS_X0 - 22, top + 32), fmt, font=font(24), fill=rgb(MUTED), anchor="rm")
            canvas.text((end + 18, top + 32), value_label, font=font(28, bold=True),
                        fill=rgb(TEXT), anchor="lm")

    # Axis and labels
    for value, label in TICKS:
        canvas.text((gb_to_x(value), 952), label, font=font(24), fill=rgb(MUTED), anchor="ma")

    # Footnotes
    canvas.text((MARGIN, 1016), "Log scale · bars start at 1 GB.",
                font=font(22), fill=rgb(MUTED))
    canvas.text((MARGIN, 1058),
                "Size ≈ parameters × bytes per parameter: FP8 and INT4/FP4 use 1 and 0.5 bytes.",
                font=font(22), fill=rgb(MUTED))

    # Box for what is not counted
    dashed_box(canvas, (1120, 1012, 1710, 1100), radius=20, outline=BORDER_STRONG, width=2)
    canvas.text((1150, 1026), "+ context + system", font=font(26, bold=True), fill=rgb(MUTED))
    canvas.text((1150, 1064), "not included in these figures", font=font(22), fill=rgb(MUTED))

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

"""The loss scaling sound console.

Figure for the PyramidSpace blog with the audio metaphor (gain staging): three
channels of a mixing desk.

1. FP16 unscaled: the whisper of the gradients falls into the red zone of the
   VU meter (below the representable floor) and turns into 0.
2. FP16 with gain ×1024: the knob raises the signal up to the green zone,
   without hitting the clip.
3. BF16: the green zone takes up almost the whole VU meter, so no knob is
   needed; the same whisper is already representable.

Style: blog dark-theme palette and minimal text (style memory).

Recommended location: "Below the text «multiply the loss by a large constant (for example 1024) before backpropagation»"
"""

from __future__ import annotations

import math
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# 1. Blog dark theme palette and typography
# ---------------------------------------------------------------------------
BG = "#090B0D"
CARD = "#111519"
CARD_RAISED = "#171C21"
BORDER = "#1F2123"
BORDER_SOFT = "#262A2E"
BORDER_STRONG = "#3F4142"
TEXT = "#F8FAFC"
MUTED = "#94A3B8"
FAINT = "#64748B"
TEAL = "#2DD4BF"
AMBER = "#F59E0B"
GREEN = "#4ADE80"
RED = "#F87171"

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

# Metadata filled in by the studio; kept for traceability.
TITLE = "Dynamic range and loss scaling"
LOCATION = "Below the text «multiply the loss by a large constant (for example 1024) before backpropagation»"
CONTENT = (
    "The mixing desk metaphor (gain staging): the gradient is a whisper; in "
    "FP16 it falls below the VU meter floor and turns into 0, the gain knob "
    "×1024 raises it into the green zone, and in BF16 the green zone takes up almost the whole "
    "VU meter, so the knob is unnecessary."
)
SOURCE = "diagram-studio"


def rgb(value: str) -> tuple[int, int, int]:
    """Convert `#RRGGBB` into an RGB tuple."""
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def mix(base: str, color: str, amount: float) -> tuple[int, int, int]:
    """Mix `color` over `base` with the weight `amount` (0..1)."""
    a, b = rgb(base), rgb(color)
    return tuple(round(a[i] + (b[i] - a[i]) * amount) for i in range(3))


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


# ---------------------------------------------------------------------------
# 2. Canvas and console pieces
# ---------------------------------------------------------------------------
def new_canvas(width: int = W, height: int = H) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    """Create the dark canvas with its `ImageDraw`."""
    image = Image.new("RGB", (width, height), rgb(BG))
    return image, ImageDraw.Draw(image)


def draw_knob(canvas: ImageDraw.ImageDraw, cx: int, cy: int, *, fill: str, outline: str,
              pointer: str | None = None, angle: float | None = None, crossed: bool = False) -> None:
    """Gain knob: circle, needle and, when crossed out, no scale."""
    radius = 54
    canvas.ellipse((cx - radius, cy - radius, cx + radius, cy + radius),
                   fill=rgb(fill), outline=rgb(outline), width=2)
    if crossed:
        canvas.line((cx - radius * 0.62, cy + radius * 0.62, cx + radius * 0.62, cy - radius * 0.62),
                    fill=rgb(FAINT), width=4)
        return
    if pointer is not None and angle is not None:
        radians = math.radians(angle)
        ex = cx + radius * 0.74 * math.cos(radians)
        ey = cy - radius * 0.74 * math.sin(radians)
        canvas.line((cx, cy, ex, ey), fill=rgb(pointer), width=5)
        canvas.ellipse((cx - 5, cy - 5, cx + 5, cy + 5), fill=rgb(pointer))


def draw_arc(canvas: ImageDraw.ImageDraw, cx: int, cy: int, radius: int, start: int, end: int,
             color: str) -> None:
    """Turn arc with an arrowhead (clockwise on screen)."""
    box = (cx - radius, cy - radius, cx + radius, cy + radius)
    canvas.arc(box, start=start, end=end, fill=rgb(color), width=3)
    radians = math.radians(end)
    px, py = cx + radius * math.cos(radians), cy + radius * math.sin(radians)
    tx, ty = -math.sin(radians), math.cos(radians)
    head = 10
    nx, ny = -ty, tx
    canvas.polygon(
        [
            (px + tx * head * 0.4, py + ty * head * 0.4),
            (px - tx * head * 0.6 + nx * head * 0.55, py - ty * head * 0.6 + ny * head * 0.55),
            (px - tx * head * 0.6 - nx * head * 0.55, py - ty * head * 0.6 - ny * head * 0.55),
        ],
        fill=rgb(color),
    )


def draw_meter(canvas: ImageDraw.ImageDraw, x0: int, y_top: int, y_bottom: int,
               zones: list[tuple[float, float, str]]) -> None:
    """Vertical VU meter with color zones inside a frame."""
    width = 96
    x1 = x0 + width
    for from_fraction, to_fraction, color in zones:
        top = y_top + (y_bottom - y_top) * from_fraction
        bottom = y_top + (y_bottom - y_top) * to_fraction
        canvas.rectangle((x0, top, x1, bottom), fill=color)
    canvas.rectangle((x0, y_top, x1, y_bottom), outline=rgb(BORDER_STRONG), width=2)


def draw_needle(canvas: ImageDraw.ImageDraw, x0: int, level: int) -> None:
    """VU meter needle: horizontal bar sticking out of the frame."""
    width = 96
    canvas.rounded_rectangle((x0 - 8, level - 4, x0 + width + 8, level + 4), radius=4, fill=rgb(TEXT))


def draw_wave(canvas: ImageDraw.ImageDraw, x0: int, cy: int, width: int, amplitude: float,
              color: str) -> None:
    """Small waveform: the whisper of the gradients."""
    points = []
    steps = 90
    for index in range(steps + 1):
        t = index / steps
        envelope = 0.45 + 0.55 * math.sin(t * math.pi)
        y = cy - amplitude * envelope * math.sin(t * 2.7 * 2 * math.pi)
        points.append((x0 + t * width, y))
    canvas.line(points, fill=rgb(color), width=2, joint="curve")


# ---------------------------------------------------------------------------
# 3. Geometry of the three channels
# ---------------------------------------------------------------------------
CARD_XS = (90, 660, 1230)
CARD_W = 480
CARD_Y0, CARD_Y1 = 250, 980
KNOB_Y = 342
LABEL_Y = 434
METER_Y0, METER_Y1 = 480, 920
NAME_Y = 962
METER_OFFSET = 48          # half width of the VU meter from the channel center
WAVE_OFFSET = -176         # waveform start from the channel center
WAVE_WIDTH = 112

RED_ZONE = mix(BG, RED, 0.30)
GREEN_ZONE = mix(BG, GREEN, 0.34)

FP16_ZONES = [(0.00, 0.15, RED_ZONE), (0.15, 0.60, GREEN_ZONE), (0.60, 1.00, RED_ZONE)]
BF16_ZONES = [(0.00, 0.04, RED_ZONE), (0.04, 0.96, GREEN_ZONE), (0.96, 1.00, RED_ZONE)]


def draw_channel(canvas: ImageDraw.ImageDraw, x0: int, name: str, name_color: str,
                 state: str, meter_zones: list[tuple[float, float, str]], needle_y: int,
                 wave_amplitude: float, knob: dict[str, object], lost: bool) -> None:
    """One desk channel: knob, state, VU meter with needle, waveform and name."""
    cx = x0 + CARD_W // 2
    canvas.rounded_rectangle((x0, CARD_Y0, x0 + CARD_W, CARD_Y1), radius=28,
                             fill=rgb(CARD), outline=rgb(BORDER), width=2)

    knob_options = dict(knob)
    arc = knob_options.pop("arc", None)
    draw_knob(canvas, cx, KNOB_Y, **knob_options)
    if arc is not None:
        start, end = arc
        draw_arc(canvas, cx, KNOB_Y, 78, start, end, TEAL)

    canvas.text((cx, LABEL_Y), state, font=font(26), fill=rgb(MUTED), anchor="mm")

    meter_x0 = cx - METER_OFFSET
    draw_meter(canvas, meter_x0, METER_Y0, METER_Y1, meter_zones)
    draw_needle(canvas, meter_x0, needle_y)

    draw_wave(canvas, cx + WAVE_OFFSET, needle_y, WAVE_WIDTH, wave_amplitude, AMBER)

    if lost:
        canvas.text((cx + METER_OFFSET + 30, needle_y), "0", font=font(34, bold=True),
                    fill=rgb(RED), anchor="lm")

    canvas.text((cx, NAME_Y), name, font=font(28, bold=True), fill=rgb(name_color), anchor="mm")


def draw() -> Image.Image:
    """Compose the diagram. Return the final image."""
    image, canvas = new_canvas()

    # Header
    canvas.text((MARGIN, 84), "Range, not precision",
                font=font(58, bold=True), fill=rgb(TEXT))
    canvas.text((MARGIN, 162), "loss scaling = gain staging", font=font(30), fill=rgb(MUTED))

    # Channel 1: FP16 unscaled, the whisper falls below the floor and becomes 0
    draw_channel(
        canvas, CARD_XS[0], "FP16", TEAL, "unscaled", FP16_ZONES,
        needle_y=868, wave_amplitude=12,
        knob={"fill": CARD_RAISED, "outline": BORDER_STRONG, "pointer": MUTED, "angle": 90},
        lost=True,
    )

    # Channel 2: FP16 with the ×1024 knob, the whisper enters the green zone
    draw_channel(
        canvas, CARD_XS[1], "FP16", TEAL, "×1024", FP16_ZONES,
        needle_y=700, wave_amplitude=36,
        knob={"fill": CARD_RAISED, "outline": BORDER_STRONG, "pointer": TEXT, "angle": 30,
              "arc": (270, 336)},
        lost=False,
    )

    # Channel 3: BF16, the green zone takes up almost everything and no knob is needed
    draw_channel(
        canvas, CARD_XS[2], "BF16", GREEN, "no knob", BF16_ZONES,
        needle_y=868, wave_amplitude=12,
        knob={"fill": CARD, "outline": BORDER_SOFT, "crossed": True},
        lost=False,
    )

    # Closing
    canvas.text((MARGIN, 1062), "the same signal, three channels", font=font(24), fill=rgb(MUTED))

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

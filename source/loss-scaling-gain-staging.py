"""La consola de sonido del loss scaling.

Figura para el blog PyramidSpace con la metáfora del audio (gain staging): tres
canales de una mesa de mezclas.

1. FP16 sin escalar: el susurro de los gradientes cae en la zona roja del
   vúmetro (por debajo del suelo representable) y se convierte en 0.
2. FP16 con ganancia ×1024: la perilla sube la señal hasta la zona verde, sin
   llegar al clip.
3. BF16: la zona verde ocupa casi todo el vúmetro, así que no hace falta
   perilla; el mismo susurro ya es representable.

Estilo: paleta del tema oscuro del blog y texto mínimo (memoria de estilo).

Ubicación recomendada: "Abajo del texto «multiplicar la pérdida por una constante grande (por ejemplo 1024) antes de la retropropagación»"
"""

from __future__ import annotations

import math
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# 1. Paleta del tema oscuro del blog y tipografía
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

# Metadatos rellenados por el estudio; se conservan para trazabilidad.
TITLE = "Rango dinámico y loss scaling"
LOCATION = "Abajo del texto «multiplicar la pérdida por una constante grande (por ejemplo 1024) antes de la retropropagación»"
CONTENT = (
    "La metáfora de la mesa de sonido (gain staging): el gradiente es un susurro; en "
    "FP16 cae bajo el suelo del vúmetro y se convierte en 0, la perilla de ganancia "
    "×1024 lo sube a la zona verde, y en BF16 la zona verde ocupa casi todo el "
    "vúmetro, así que la perilla sobra."
)
SOURCE = "diagram-studio"


def rgb(value: str) -> tuple[int, int, int]:
    """Convierte `#RRGGBB` en una tupla RGB."""
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def mix(base: str, color: str, amount: float) -> tuple[int, int, int]:
    """Mezcla `color` sobre `base` con el peso `amount` (0..1)."""
    a, b = rgb(base), rgb(color)
    return tuple(round(a[i] + (b[i] - a[i]) * amount) for i in range(3))


def _first_available(paths: list[str]) -> str:
    for path in paths:
        if Path(path).is_file():
            return path
    return paths[-1]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Carga la sans neutra (Liberation Sans, DejaVu de respaldo)."""
    path = _first_available(FONT_SANS_BOLD if bold else FONT_SANS)
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


# ---------------------------------------------------------------------------
# 2. Lienzo y piezas de la consola
# ---------------------------------------------------------------------------
def new_canvas(width: int = W, height: int = H) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    """Crea el lienzo oscuro con su `ImageDraw`."""
    image = Image.new("RGB", (width, height), rgb(BG))
    return image, ImageDraw.Draw(image)


def draw_knob(canvas: ImageDraw.ImageDraw, cx: int, cy: int, *, fill: str, outline: str,
              pointer: str | None = None, angle: float | None = None, crossed: bool = False) -> None:
    """Perilla de ganancia: círculo, aguja y, si se cruza, sin escala."""
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
    """Arco de giro con punta de flecha (sentido horario en pantalla)."""
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
    """Vúmetro vertical con zonas de color dentro de un marco."""
    width = 96
    x1 = x0 + width
    for from_fraction, to_fraction, color in zones:
        top = y_top + (y_bottom - y_top) * from_fraction
        bottom = y_top + (y_bottom - y_top) * to_fraction
        canvas.rectangle((x0, top, x1, bottom), fill=color)
    canvas.rectangle((x0, y_top, x1, y_bottom), outline=rgb(BORDER_STRONG), width=2)


def draw_needle(canvas: ImageDraw.ImageDraw, x0: int, level: int) -> None:
    """Aguja del vúmetro: barra horizontal que sobresale del marco."""
    width = 96
    canvas.rounded_rectangle((x0 - 8, level - 4, x0 + width + 8, level + 4), radius=4, fill=rgb(TEXT))


def draw_wave(canvas: ImageDraw.ImageDraw, x0: int, cy: int, width: int, amplitude: float,
              color: str) -> None:
    """Pequeña forma de onda: el susurro de los gradientes."""
    points = []
    steps = 90
    for index in range(steps + 1):
        t = index / steps
        envelope = 0.45 + 0.55 * math.sin(t * math.pi)
        y = cy - amplitude * envelope * math.sin(t * 2.7 * 2 * math.pi)
        points.append((x0 + t * width, y))
    canvas.line(points, fill=rgb(color), width=2, joint="curve")


# ---------------------------------------------------------------------------
# 3. Geometría de los tres canales
# ---------------------------------------------------------------------------
CARD_XS = (90, 660, 1230)
CARD_W = 480
CARD_Y0, CARD_Y1 = 250, 980
KNOB_Y = 342
LABEL_Y = 434
METER_Y0, METER_Y1 = 480, 920
NAME_Y = 962
METER_OFFSET = 48          # medio ancho del vúmetro respecto al centro del canal
WAVE_OFFSET = -176         # inicio de la onda respecto al centro del canal
WAVE_WIDTH = 112

RED_ZONE = mix(BG, RED, 0.30)
GREEN_ZONE = mix(BG, GREEN, 0.34)

FP16_ZONES = [(0.00, 0.15, RED_ZONE), (0.15, 0.60, GREEN_ZONE), (0.60, 1.00, RED_ZONE)]
BF16_ZONES = [(0.00, 0.04, RED_ZONE), (0.04, 0.96, GREEN_ZONE), (0.96, 1.00, RED_ZONE)]


def draw_channel(canvas: ImageDraw.ImageDraw, x0: int, name: str, name_color: str,
                 state: str, meter_zones: list[tuple[float, float, str]], needle_y: int,
                 wave_amplitude: float, knob: dict[str, object], lost: bool) -> None:
    """Un canal de la mesa: perilla, estado, vúmetro con aguja, onda y nombre."""
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
    """Compón el diagrama. Devuelve la imagen final."""
    image, canvas = new_canvas()

    # Cabecera
    canvas.text((MARGIN, 84), "El rango, no la precisión",
                font=font(58, bold=True), fill=rgb(TEXT))
    canvas.text((MARGIN, 162), "loss scaling = gain staging", font=font(30), fill=rgb(MUTED))

    # Canal 1: FP16 sin escalar, el susurro cae bajo el suelo y vale 0
    draw_channel(
        canvas, CARD_XS[0], "FP16", TEAL, "sin escalar", FP16_ZONES,
        needle_y=868, wave_amplitude=12,
        knob={"fill": CARD_RAISED, "outline": BORDER_STRONG, "pointer": MUTED, "angle": 90},
        lost=True,
    )

    # Canal 2: FP16 con la perilla ×1024, el susurro entra en la zona verde
    draw_channel(
        canvas, CARD_XS[1], "FP16", TEAL, "×1024", FP16_ZONES,
        needle_y=700, wave_amplitude=36,
        knob={"fill": CARD_RAISED, "outline": BORDER_STRONG, "pointer": TEXT, "angle": 30,
              "arc": (270, 336)},
        lost=False,
    )

    # Canal 3: BF16, la zona verde ocupa casi todo y la perilla no hace falta
    draw_channel(
        canvas, CARD_XS[2], "BF16", GREEN, "sin perilla", BF16_ZONES,
        needle_y=868, wave_amplitude=12,
        knob={"fill": CARD, "outline": BORDER_SOFT, "crossed": True},
        lost=False,
    )

    # Cierre
    canvas.text((MARGIN, 1062), "la misma señal, tres canales", font=font(24), fill=rgb(MUTED))

    return image


def save(image: Image.Image, path: str | Path | None = None) -> Path:
    """Guarda el PNG en `DIAGRAM_OUT` (o en `out.png` si se ejecuta a mano)."""
    target = Path(path or os.environ.get("DIAGRAM_OUT", "out.png"))
    target.parent.mkdir(parents=True, exist_ok=True)
    image.save(target, format="PNG")
    return target


if __name__ == "__main__":
    destination = save(draw())
    print(f"diagrama escrito en {destination}")

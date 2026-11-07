"""«Destilación capa a capa (LKD)»

Diagrama propuesto por el estudio de diagramas a partir de la recomendación
«Destilación capa a capa (LKD)»: ZeroQuant baja a INT4 sin un QAT completo
congelando el modelo y ajustando cada capa cuantizada para que reproduzca la
salida de su gemela en FP16, en minutos por capa.

Autocontenido: solo Pillow. `python3 source.py` escribe out.png y
`DIAGRAM_OUT=versions/v1.png python3 source.py` escribe donde diga el estudio.
"""

from __future__ import annotations

import math
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# 1. Paleta y tipografía (tema oscuro de PyramidSpace)
# ---------------------------------------------------------------------------
BG = "#090B0D"
CARD = "#111519"
HAIR = "#1F2123"
AXIS = "#3F4142"
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


# ---------------------------------------------------------------------------
# 2. Utilidades
# ---------------------------------------------------------------------------
def rgb(value: str) -> tuple[int, int, int]:
    """Convierte `#RRGGBB` en una tupla RGB."""
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def mix(c1: str, c2: str, t: float) -> tuple[int, int, int]:
    """Interpola dos colores hex; `t` es el peso de `c2` (0..1)."""
    t = max(0.0, min(1.0, t))
    a, b = rgb(c1), rgb(c2)
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def font(size: int, bold: bool = False, mono: bool = False) -> ImageFont.FreeTypeFont:
    """Liberation Sans para rótulos y DejaVu Sans Mono para cifras."""
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
    """Lienzo oscuro sin marco (el CSS del blog pone las esquinas)."""
    image = Image.new("RGB", (W, H), rgb(BG))
    return image, ImageDraw.Draw(image)


def arrow(draw: ImageDraw.ImageDraw, x0: int, y: int, x1: int, color: str,
          width: int = 4, head: int = 16) -> None:
    """Flecha horizontal con punta triangular."""
    draw.line((x0, y, x1, y), fill=rgb(color), width=width)
    draw.polygon([(x1, y), (x1 - head, y - head * 0.55), (x1 - head, y + head * 0.55)],
                 fill=rgb(color))


# ---------------------------------------------------------------------------
# 3. Piezas del diagrama
# ---------------------------------------------------------------------------
FP16_X0, FP16_X1 = 320, 760
INT4_X0, INT4_X1 = 1040, 1480
ROWS = (380, 520, 660, 800)
ROW_H = 100


def draw_padlock(draw: ImageDraw.ImageDraw, x: int, y: int) -> None:
    """Candado pequeño: cuerpo y arco."""
    draw.arc((x + 6, y - 2, x + 30, y + 24), start=180, end=360, fill=rgb(MUTED), width=5)
    draw.rounded_rectangle((x, y + 12, x + 36, y + 40), radius=7, fill=mix(MUTED, BG, 0.72))


def draw_columns(draw: ImageDraw.ImageDraw) -> None:
    """Dos columnas de capas: la referencia FP16 y la copia INT4."""
    draw.rounded_rectangle((FP16_X0, 260, FP16_X1, 940), radius=20, fill=rgb(CARD),
                           outline=rgb(HAIR), width=2)
    draw.rounded_rectangle((INT4_X0, 260, INT4_X1, 940), radius=20, fill=rgb(CARD),
                           outline=rgb(HAIR), width=2)
    draw.text((FP16_X0 + 30, 320), "FP16", font=font(30, bold=True), fill=rgb(MUTED), anchor="lm")
    draw_padlock(draw, FP16_X1 - 66, 300)
    draw.text((INT4_X0 + 30, 320), "INT4", font=font(30, bold=True), fill=rgb(TEAL), anchor="lm")
    for index, y in enumerate(ROWS, start=1):
        draw.rounded_rectangle((FP16_X0 + 30, y, FP16_X1 - 30, y + ROW_H), radius=12,
                               fill=mix(MUTED, BG, 0.86), outline=mix(MUTED, BG, 0.45), width=2)
        draw.text((FP16_X0 + 56, y + ROW_H / 2), str(index), font=font(26, mono=True),
                  fill=rgb(MUTED), anchor="lm")
        draw.rounded_rectangle((INT4_X0 + 30, y, INT4_X1 - 30, y + ROW_H), radius=12,
                               fill=mix(TEAL, BG, 0.86), outline=mix(TEAL, BG, 0.45), width=2)
        draw.text((INT4_X0 + 56, y + ROW_H / 2), str(index), font=font(26, mono=True),
                  fill=rgb(TEAL), anchor="lm")


def draw_imitations(draw: ImageDraw.ImageDraw) -> None:
    """Una flecha por par: la capa INT4 imita la salida de la FP16."""
    for i, y in enumerate(ROWS):
        cy = y + ROW_H / 2
        arrow(draw, FP16_X1 + 8, cy, INT4_X0 - 8, AMBER)
        if i == 0:
            draw.text(((FP16_X1 + INT4_X0) / 2, cy - 34), "imita la salida",
                      font=font(26), fill=rgb(AMBER), anchor="mm")


def draw_clock(draw: ImageDraw.ImageDraw, cx: int, cy: int, radius: int) -> None:
    """Reloj de minutos por capa."""
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius),
                 outline=mix(MUTED, BG, 0.4), width=4)
    for step in range(12):
        theta = math.radians(step * 30)
        x0 = cx + (radius - 10) * math.cos(theta)
        y0 = cy + (radius - 10) * math.sin(theta)
        x1 = cx + (radius - 4) * math.cos(theta)
        y1 = cy + (radius - 4) * math.sin(theta)
        draw.line((x0, y0, x1, y1), fill=mix(MUTED, BG, 0.4), width=3)
    draw.line((cx, cy, cx, cy - radius * 0.55), fill=rgb(MUTED), width=5)
    draw.line((cx, cy, cx + radius * 0.4, cy), fill=rgb(MUTED), width=5)


# ---------------------------------------------------------------------------
# 4. Composición
# ---------------------------------------------------------------------------
def draw() -> Image.Image:
    """Compón el diagrama y devuelve la imagen final."""
    image, canvas = new_canvas()

    canvas.text((MARGIN, 140), "Destilación capa a capa",
                font=font(58, bold=True), fill=rgb(TEXT), anchor="lm")

    draw_columns(canvas)
    draw_imitations(canvas)

    # El reloj y la nota al pie
    draw_clock(canvas, 370, 1020, 44)
    canvas.text((440, 1020), "minutos por capa", font=font(28), fill=rgb(MUTED), anchor="lm")

    canvas.rounded_rectangle((1040, 984, 1260, 1046), radius=31, fill=mix(TEAL, BG, 0.9),
                             outline=mix(TEAL, BG, 0.55), width=2)
    canvas.text((1150, 1015), "sin QAT", font=font(26, bold=True), fill=rgb(TEAL), anchor="mm")

    return image


def save(image: Image.Image, path: str | Path | None = None) -> Path:
    """Guarda el PNG en `DIAGRAM_OUT` (o en out.png si se ejecuta a mano)."""
    target = Path(path or os.environ.get("DIAGRAM_OUT", "out.png"))
    target.parent.mkdir(parents=True, exist_ok=True)
    image.save(target, format="PNG")
    return target


if __name__ == "__main__":
    destination = save(draw())
    print(f"diagrama escrito en {destination}")

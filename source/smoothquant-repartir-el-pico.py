"""«SmoothQuant: repartir el pico»

Diagrama propuesto por el estudio de diagramas a partir de la recomendación
«SmoothQuant reparte la dificultad»: la transformación equivalente que divide
las activaciones por s y multiplica los pesos por s, y cómo el pico se reparte
hasta que ambos tensores caben en INT8 sin coste en inferencia.

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
RED = "#F87171"

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
    """Liberation Sans para rótulos y DejaVu Sans Mono para la fórmula."""
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


Part = tuple[str, str, bool, bool]  # texto, color, negrita, monoespaciada


def rich(draw: ImageDraw.ImageDraw, x: int, cy: int, parts: list[Part], size: int) -> int:
    """Texto en tramos con color, peso y fuente propios; devuelve el ancho."""
    cursor = x
    for text, color, bold, mono in parts:
        face = font(size, bold=bold, mono=mono)
        draw.text((cursor, cy), text, font=face, fill=rgb(color), anchor="lm")
        cursor += draw.textlength(text, font=face)
    return round(cursor - x)


def rich_center(draw: ImageDraw.ImageDraw, cx: float, cy: int, parts: list[Part], size: int) -> None:
    """Como `rich`, pero centrado en `cx`."""
    total = sum(draw.textlength(text, font=font(size, bold=bold, mono=mono))
                for text, _, bold, mono in parts)
    rich(draw, round(cx - total / 2), cy, parts, size)


def arrow(draw: ImageDraw.ImageDraw, x0: int, y0: int, x1: int, y1: int,
          color: str = AMBER, width: int = 10, head: int = 26) -> None:
    """Flecha recta con punta triangular."""
    draw.line((x0, y0, x1, y1), fill=rgb(color), width=width)
    ang = math.atan2(y1 - y0, x1 - x0)
    left = (x1 - head * math.cos(ang - 0.42), y1 - head * math.sin(ang - 0.42))
    right = (x1 - head * math.cos(ang + 0.42), y1 - head * math.sin(ang + 0.42))
    draw.polygon([(x1, y1), left, right], fill=rgb(color))


# ---------------------------------------------------------------------------
# 3. Piezas del diagrama
# ---------------------------------------------------------------------------
NBARS, BAR_W, BAR_GAP = 18, 24, 6
PANEL_TOP, PANEL_BOTTOM = 340, 740
LEFT_PANEL = (MARGIN, PANEL_TOP, 760, PANEL_BOTTOM)
RIGHT_PANEL = (1040, PANEL_TOP, 1710, PANEL_BOTTOM)
FORMULA_BOX = (MARGIN, 240, W - MARGIN, 306)
SLIDER_Y = 820
CLOSE_BOX = (MARGIN, 920, 1250, 1000)


def gauss(mu: float, sigma: float, peak: float) -> list[float]:
    """Alturas de una campana muestreada en las barras del histograma."""
    return [peak * math.exp(-(((i - mu) / sigma) ** 2)) for i in range(NBARS)]


def draw_hist(draw: ImageDraw.ImageDraw, x0: int, y_base: int, heights: list[float],
              color: str, outliers: dict[int, float] | None = None) -> None:
    """Histograma de barras con los picos atípicos en rojo."""
    outliers = outliers or {}
    for i, h in enumerate(heights):
        bx = x0 + i * (BAR_W + BAR_GAP)
        h = outliers.get(i, h)
        fill = RED if i in outliers else color
        draw.rectangle((bx, y_base - h, bx + BAR_W, y_base), fill=rgb(fill))
    draw.line((x0, y_base + 2, x0 + NBARS * (BAR_W + BAR_GAP) - BAR_GAP, y_base + 2),
              fill=rgb(AXIS), width=2)


def draw_panel(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], title: str,
               charts: list[dict]) -> None:
    """Panel de una situación: título y dos distribuciones con su máximo."""
    x0, y0, x1, y1 = box
    draw.rounded_rectangle((x0, y0, x1, y1), radius=20, fill=rgb(CARD),
                           outline=rgb(HAIR), width=2)
    draw.text((x0 + 26, y0 + 30), title, font=font(24, bold=True), fill=rgb(MUTED), anchor="lm")
    chart_x = x0 + 40
    for index, chart in enumerate(charts):
        label_y = y0 + 62 + index * 176
        base_y = y0 + 190 + index * 176
        draw.text((x0 + 26, label_y), chart["label"], font=font(22), fill=rgb(MUTED), anchor="lm")
        draw.text((x1 - 26, label_y), chart["max_txt"], font=font(20), fill=rgb(FAINT), anchor="rm")
        draw_hist(draw, chart_x, base_y, chart["heights"], chart["color"], chart.get("outliers"))


def draw_formula(draw: ImageDraw.ImageDraw) -> None:
    """La fórmula de la escala, en una banda bajo el subtítulo."""
    x0, y0, x1, y1 = FORMULA_BOX
    draw.rounded_rectangle((x0, y0, x1, y1), radius=16, fill=rgb(CARD), outline=rgb(HAIR), width=2)
    parts = [
        ("s = max(|X|)", TEXT, 32, 0),
        ("α", AMBER, 22, -14),
        (" / max(|W|)", TEXT, 32, 0),
        ("1−α", AMBER, 22, -14),
    ]
    total = sum(draw.textlength(text, font=font(size, mono=True)) for text, _, size, _ in parts)
    cursor = (x0 + x1) / 2 - total / 2
    cy = (y0 + y1) // 2 + 3
    for text, color, size, dy in parts:
        face = font(size, mono=True)
        draw.text((cursor, cy + dy), text, font=face, fill=rgb(color), anchor="lm")
        cursor += draw.textlength(text, font=face)


def draw_slider(draw: ImageDraw.ImageDraw) -> None:
    """Eje de α de 0 a 1, con la marca del reparto justo en 0,5."""
    x0, x1 = 200, 1600
    draw.line((x0, SLIDER_Y, x1, SLIDER_Y), fill=rgb(AXIS), width=3)
    for x in (x0, 900, x1):
        draw.line((x, SLIDER_Y - 8, x, SLIDER_Y + 8), fill=rgb(AXIS), width=3)
    draw.ellipse((900 - 13, SLIDER_Y - 13, 900 + 13, SLIDER_Y + 13), fill=rgb(AMBER))
    draw.text((x0, SLIDER_Y + 30), "α = 0: todo a la activación",
              font=font(22), fill=rgb(MUTED), anchor="lm")
    rich_center(draw, 900, SLIDER_Y + 30, [("α = 0,5: reparto justo", TEXT, True, False)], size=22)
    draw.text((x1, SLIDER_Y + 30), "α = 1: todo al peso",
              font=font(22), fill=rgb(MUTED), anchor="rm")


def draw_closing(image: Image.Image, draw: ImageDraw.ImageDraw) -> None:
    """Caja de absorción de la escala y badges de rendimiento."""
    x0, y0, x1, y1 = CLOSE_BOX
    draw.rounded_rectangle((x0, y0, x1, y1), radius=16, fill=mix(TEAL, BG, 0.92),
                           outline=mix(TEAL, BG, 0.55), width=2)
    rich(draw, x0 + 26, (y0 + y1) // 2, [
        ("s", TEAL, True, True),
        (" se calcula fuera de línea y se absorbe en el LayerNorm previo: cero sobrecoste",
         TEXT, False, False),
    ], size=24)

    badges = ("W8A8 en Tensor Cores", "hasta 1,56×")
    for index, text in enumerate(badges):
        by0 = y0 + index * 44
        draw.rounded_rectangle((1300, by0, W - MARGIN, by0 + 38), radius=19,
                               fill=mix(AMBER, BG, 0.92), outline=mix(AMBER, BG, 0.55), width=2)
        draw.text((1505, by0 + 19), text, font=font(22), fill=rgb(AMBER), anchor="mm")


# ---------------------------------------------------------------------------
# 4. Composición
# ---------------------------------------------------------------------------
def draw() -> Image.Image:
    """Compón el diagrama y devuelve la imagen final."""
    image, canvas = new_canvas()

    canvas.text((MARGIN, 130), "SmoothQuant: repartir el pico",
                font=font(58, bold=True), fill=rgb(TEXT), anchor="lm")
    canvas.text((MARGIN, 202), "la misma multiplicación, con menos dificultad en X",
                font=font(32), fill=rgb(MUTED), anchor="lm")

    draw_formula(canvas)

    before_charts = [
        {"label": "activaciones", "color": AMBER, "max_txt": "máx ≈ 70",
         "heights": gauss(3.0, 1.0, 24), "outliers": {14: 72, 15: 104, 16: 86, 17: 52}},
        {"label": "pesos", "color": TEAL, "max_txt": "máx ≈ 1",
         "heights": gauss(5.5, 1.5, 52)},
    ]
    after_charts = [
        {"label": "activaciones", "color": AMBER, "max_txt": "máx ≈ 8,4",
         "heights": gauss(8.5, 3.2, 88)},
        {"label": "pesos", "color": TEAL, "max_txt": "máx ≈ 8,4",
         "heights": gauss(9.0, 2.8, 74)},
    ]
    draw_panel(canvas, LEFT_PANEL, "antes", before_charts)
    draw_panel(canvas, RIGHT_PANEL, "después", after_charts)

    # La transformación: X entre s y W por s
    arrow(canvas, 772, 540, 1026, 540)
    rich_center(canvas, 900, 507, [("X", AMBER, True, True), (" ÷ s", AMBER, False, False)], size=24)
    rich_center(canvas, 900, 577, [("W", TEAL, True, True), (" × s", TEAL, False, False)], size=24)

    draw_slider(canvas)
    draw_closing(image, canvas)

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

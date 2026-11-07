"""«La asimetría entre Keys y Values»

Diagrama propuesto por el estudio de diagramas a partir de una recomendación del
blog: la caché de atención no es simétrica. Los valores (V) son homogéneos y se
cuantizan sin drama; las claves (K) concentran outliers de hasta diez veces el
promedio y, al bajar a INT4, los picos comprimen el rango y se comen la
resolución. La figura contrasta las dos distribuciones sobre un rango INT4
compartido.

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
SUNK = "#0E1216"
BORDER_STRONG = "#262A2E"
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

# Geometría de la composición
PANEL_TOP, PANEL_BOT = 280, 875
HEADER_LINE, HEADER_UNDERLINE = 371, 391
BASELINE = 811
LEFT_PANEL = (90, 855)
RIGHT_PANEL = (945, 1710)
INSET = 48

RULER_X0, RULER_X1 = 360, 1710
BAR_TOP, BAR_BOT = 935, 1005
LEVELS = 16  # INT4: dieciséis niveles, dieciséis peldaños


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


# ---------------------------------------------------------------------------
# 3. Piezas del diagrama
# ---------------------------------------------------------------------------
def draw_panel(draw: ImageDraw.ImageDraw, x0: int, x1: int, letter: str,
               accent: str) -> None:
    """Panel de una distribución: letra, subrayado de acento y línea base."""
    draw.rounded_rectangle((x0, PANEL_TOP, x1, PANEL_BOT), radius=22,
                           fill=rgb(CARD), outline=rgb(HAIR), width=2)
    draw.text((x0 + INSET, HEADER_LINE), letter, font=font(56, bold=True),
              fill=rgb(accent), anchor="ls")
    draw.line((x0 + INSET, HEADER_UNDERLINE, x0 + INSET + 78, HEADER_UNDERLINE),
              fill=mix(accent, BG, 0.45), width=4)
    draw.line((x0 + INSET, BASELINE, x1 - INSET, BASELINE), fill=rgb(AXIS), width=3)


def bump(draw: ImageDraw.ImageDraw, x0: int, x1: int, mu: float, sigma: float,
         height: int, fill: str, line: str, width: int = 4) -> None:
    """Campana gaussiana rellena sobre la línea base del panel."""
    span = 3.4
    lo, hi = max(0.0, mu - span * sigma), min(1.0, mu + span * sigma)
    points = []
    steps = 220
    for index in range(steps + 1):
        u = lo + (hi - lo) * index / steps
        y = BASELINE - height * math.exp(-0.5 * ((u - mu) / sigma) ** 2)
        points.append((x0 + (x1 - x0) * u, y))
    draw.polygon([(x0 + (x1 - x0) * lo, BASELINE), *points,
                  (x0 + (x1 - x0) * hi, BASELINE)], fill=fill)
    draw.line(points, fill=line, width=width, joint="curve")


def draw_distributions(draw: ImageDraw.ImageDraw) -> None:
    """V: una campana estrecha. K: la campana desplazada y dos picos a la derecha."""
    vx0, vx1 = LEFT_PANEL[0] + INSET, LEFT_PANEL[1] - INSET
    kx0, kx1 = RIGHT_PANEL[0] + INSET, RIGHT_PANEL[1] - INSET

    # Valores: una sola población homogénea.
    bump(draw, vx0, vx1, mu=0.43, sigma=0.076, height=288,
         fill=mix(TEAL, BG, 0.58), line=TEAL)

    # Claves: la población central y dos canales con outliers de ×10.
    bump(draw, kx0, kx1, mu=0.255, sigma=0.076, height=242,
         fill=mix(AMBER, BG, 0.48), line=AMBER)
    peak_a, peak_b = 0.845, 0.925
    bump(draw, kx0, kx1, mu=peak_a, sigma=0.017, height=380,
         fill=mix(RED, BG, 0.38), line=RED, width=3)
    bump(draw, kx0, kx1, mu=peak_b, sigma=0.017, height=340,
         fill=mix(RED, BG, 0.38), line=RED, width=3)

    # Corchete que agrupa los dos picos y etiqueta su magnitud.
    xa = kx0 + (kx1 - kx0) * peak_a
    xb = kx0 + (kx1 - kx0) * peak_b
    draw.line((xa - 10, 406, xb + 10, 406), fill=rgb(RED), width=2)
    for x in (xa - 10, xb + 10):
        draw.line((x, 406, x, 416), fill=rgb(RED), width=2)
    draw.text(((xa + xb) / 2, 398), "×10", font=font(36, bold=True, mono=True),
              fill=rgb(RED), anchor="ms")


def draw_ruler(draw: ImageDraw.ImageDraw) -> None:
    """El rango INT4 compartido: dieciséis peldaños y su paso de cuantización."""
    mid = (BAR_TOP + BAR_BOT) // 2
    draw.text((MARGIN, mid), "rango INT4", font=font(32, bold=True),
              fill=rgb(MUTED), anchor="lm")
    draw.rounded_rectangle((RULER_X0, BAR_TOP, RULER_X1, BAR_BOT), radius=20,
                           fill=rgb(SUNK), outline=rgb(BORDER_STRONG), width=2)

    width = RULER_X1 - RULER_X0
    step = width / LEVELS

    # El último peldaño lo ocupa el pico: el rango se estira hasta allí.
    draw.rounded_rectangle((RULER_X1 - step + 8, BAR_TOP + 8, RULER_X1 - 8, BAR_BOT - 8),
                           radius=12, fill=mix(RED, SUNK, 0.55))
    for index in range(1, LEVELS):
        x = RULER_X0 + index * step
        last = index == LEVELS - 1
        draw.line((x, BAR_TOP + 10, x, BAR_BOT - 10),
                  fill=rgb(RED if last else FAINT), width=4 if last else 2)

    # El paso de cuantización, medido sobre el primer peldaño.
    draw.line((RULER_X0, 1029, RULER_X0 + step, 1029), fill=rgb(FAINT), width=2)
    for x in (RULER_X0, RULER_X0 + step):
        draw.line((x, 1029, x, 1021), fill=rgb(FAINT), width=2)
    draw.text((RULER_X0 + step / 2, 1057), "paso", font=font(26),
              fill=rgb(MUTED), anchor="ms")

    # Nota al pie bajo el peldaño que ocupa el pico.
    draw.text((RULER_X1, 1055), "el pico comprime el rango",
              font=font(30), fill=rgb(RED), anchor="ra")


# ---------------------------------------------------------------------------
# 4. Composición
# ---------------------------------------------------------------------------
def draw() -> Image.Image:
    """Compón el diagrama y devuelve la imagen final."""
    image, canvas = new_canvas()

    canvas.text((MARGIN, 140), "Valores frente a claves", font=font(58, bold=True),
                fill=rgb(TEXT), anchor="lm")

    draw_panel(canvas, *LEFT_PANEL, "V", TEAL)
    draw_panel(canvas, *RIGHT_PANEL, "K", AMBER)
    draw_distributions(canvas)
    draw_ruler(canvas)

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

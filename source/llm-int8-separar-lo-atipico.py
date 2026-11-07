"""«LLM.int8(): separar lo atípico»

Diagrama propuesto por el estudio de diagramas a partir de la recomendación
«LLM.int8() parte la matriz en dos»: la descomposición en precisión mixta del
método de Dettmers et al. Se apartan las pocas columnas atípicas en FP16, el
resto va a INT8 y se muestra el coste del acceso irregular.

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
LIGHT_TEAL = "#5EEAD4"
AMBER = "#F59E0B"
GREEN = "#4ADE80"
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
    """Liberation Sans para rótulos y DejaVu Sans Mono para cifras y siglas."""
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
          color: str = AMBER, width: int = 4, head: int = 18) -> None:
    """Flecha recta con punta triangular."""
    draw.line((x0, y0, x1, y1), fill=rgb(color), width=width)
    ang = math.atan2(y1 - y0, x1 - x0)
    left = (x1 - head * math.cos(ang - 0.45), y1 - head * math.sin(ang - 0.45))
    right = (x1 - head * math.cos(ang + 0.45), y1 - head * math.sin(ang + 0.45))
    draw.polygon([(x1, y1), left, right], fill=rgb(color))


# ---------------------------------------------------------------------------
# 3. Piezas del diagrama
# ---------------------------------------------------------------------------
MATRIX_X, MATRIX_Y = 108, 320
COLS = ROWS = 20
CELL, GAP = 27, 4
STRIDE = CELL + GAP
MATRIX_W = COLS * CELL + (COLS - 1) * GAP     # 616
RED_COLS = (8, 9, 10)

BOX_X, BOX_W, BOX_H = 790, 360, 80
FP16_Y = 420
INT8_Y = 790
OUT_X, OUT_Y, OUT_W, OUT_H = 1430, 560, 260, 140
BADGE = (1130, 960, 1710, 1040)


def draw_matrix(draw: ImageDraw.ImageDraw) -> None:
    """Matriz de pesos: celdas INT8 en teal y tres columnas atípicas en rojo."""
    for row in range(ROWS):
        for col in range(COLS):
            x = MATRIX_X + col * STRIDE
            y = MATRIX_Y + row * STRIDE
            if col in RED_COLS:
                color = mix(RED, BG, 0.15)
            else:
                color = mix(TEAL, BG, 0.28)
            draw.rounded_rectangle((x, y, x + CELL, y + CELL), radius=4, fill=color)


def draw_marginal_scales(draw: ImageDraw.ImageDraw) -> None:
    """Una escala por fila (izquierda) y una por columna (abajo)."""
    for row in range(ROWS):
        y = MATRIX_Y + row * STRIDE + CELL / 2
        draw.rounded_rectangle((MARGIN, y - 3, MARGIN + 16, y + 3), radius=3,
                               fill=rgb(LIGHT_TEAL))
    for col in range(COLS):
        x = MATRIX_X + col * STRIDE + CELL / 2
        draw.rounded_rectangle((x - 3, MATRIX_Y + MATRIX_W + 16, x + 3, MATRIX_Y + MATRIX_W + 36),
                               radius=3, fill=rgb(LIGHT_TEAL))


def draw_columns_bracket(draw: ImageDraw.ImageDraw) -> None:
    """Llave sobre las columnas atípicas con su rótulo."""
    x0 = MATRIX_X + RED_COLS[0] * STRIDE
    x1 = MATRIX_X + RED_COLS[-1] * STRIDE + CELL
    y = MATRIX_Y - 12
    draw.line((x0, y, x1, y), fill=rgb(RED), width=2)
    for x in (x0, x1):
        draw.line((x, y, x, y + 8), fill=rgb(RED), width=2)
    rich_center(draw, (x0 + x1) / 2, MATRIX_Y - 32, [("columnas atípicas", RED, False, False)], size=24)


def draw_branch_box(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int,
                    title: str, detail: str, color: str) -> None:
    """Caja de una rama: título en su color y detalle en gris."""
    draw.rounded_rectangle((x, y, x + w, y + h), radius=16, fill=rgb(CARD),
                           outline=mix(color, CARD, 0.55), width=2)
    draw.rounded_rectangle((x + 2, y + 12, x + 8, y + h - 12), radius=3, fill=rgb(color))
    draw.text((x + 26, y + h / 2 - 13), title, font=font(26, bold=True), fill=rgb(color), anchor="lm")
    draw.text((x + 26, y + h / 2 + 15), detail, font=font(24), fill=rgb(MUTED), anchor="lm")


def draw_output(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int) -> None:
    """Caja de suma donde confluyen las dos ramas."""
    draw.rounded_rectangle((x, y, x + w, y + h), radius=20, fill=rgb(CARD),
                           outline=rgb(AXIS), width=2)
    draw.text((x + w / 2, y + h / 2), "salida", font=font(30, bold=True),
              fill=rgb(TEXT), anchor="mm")


def draw_badge(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str) -> None:
    """Aviso de coste: el acceso irregular se come la ventaja de velocidad."""
    x0, y0, x1, y1 = box
    draw.rounded_rectangle((x0, y0, x1, y1), radius=16, fill=mix(RED, BG, 0.9),
                           outline=mix(RED, BG, 0.55), width=2)
    draw.text(((x0 + x1) / 2, (y0 + y1) / 2), text, font=font(24),
              fill=rgb(RED), anchor="mm")


# ---------------------------------------------------------------------------
# 4. Composición
# ---------------------------------------------------------------------------
def draw() -> Image.Image:
    """Compón el diagrama y devuelve la imagen final."""
    image, canvas = new_canvas()

    canvas.text((MARGIN, 120), "LLM.int8(): separar lo atípico",
                font=font(58, bold=True), fill=rgb(TEXT), anchor="lm")
    canvas.text((MARGIN, 192), "99 % en INT8, 1 % en FP16",
                font=font(32), fill=rgb(MUTED), anchor="lm")

    canvas.text((MARGIN, 288), "matriz de pesos", font=font(26), fill=rgb(MUTED), anchor="lm")

    draw_matrix(canvas)
    draw_columns_bracket(canvas)
    draw_marginal_scales(canvas)
    canvas.text((MARGIN, 1012), "escala por fila y por columna",
                font=font(24), fill=rgb(MUTED), anchor="lm")

    # Ramas: de la matriz a la caja de cada precisión, y de ahí a la salida
    arrow(canvas, MATRIX_X + MATRIX_W + 6, FP16_Y + BOX_H / 2, BOX_X - 6, FP16_Y + BOX_H / 2)
    arrow(canvas, MATRIX_X + MATRIX_W + 6, INT8_Y + BOX_H / 2, BOX_X - 6, INT8_Y + BOX_H / 2)
    draw_branch_box(canvas, BOX_X, FP16_Y, BOX_W, BOX_H,
                    "1 % atípico", "diminuta en FP16", GREEN)
    draw_branch_box(canvas, BOX_X, INT8_Y, BOX_W, BOX_H,
                    "99 % restante", "en INT8", TEAL)
    arrow(canvas, BOX_X + BOX_W + 6, FP16_Y + BOX_H / 2, OUT_X - 6, OUT_Y + 50)
    arrow(canvas, BOX_X + BOX_W + 6, INT8_Y + BOX_H / 2, OUT_X - 6, OUT_Y + 90)
    draw_output(canvas, OUT_X, OUT_Y, OUT_W, OUT_H)
    draw_badge(canvas, BADGE, "acceso irregular: se pierde la ventaja de velocidad")

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

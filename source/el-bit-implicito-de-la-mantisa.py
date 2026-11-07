"""«El bit implícito de la mantisa»

Diagrama propuesto por el estudio de diagramas a partir de una recomendación del
blog: la mantisa de un número normalizado empieza siempre por 1, así que ese bit
no se guarda. La tira muestra las 23 celdas que sí se almacenan y, a su
izquierda, la celda fantasma del bit implícito: 23 guardados más 1 prestado dan
24 bits de precisión.

Autocontenido: solo Pillow. `python3 source.py` escribe out.png y
`DIAGRAM_OUT=versions/v1.png python3 source.py` escribe donde diga el estudio.
"""

from __future__ import annotations

import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# 1. Paleta y tipografía (tema oscuro de PyramidSpace)
# ---------------------------------------------------------------------------
BG = "#090B0D"
CARD = "#111519"
HAIR = "#1F2123"
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

# Geometría de la composición
TITLE_Y, SUBTITLE_Y = 140, 218
LABEL_Y = 396
CELL_TOP, CELL_BOT = 424, 714
CELL_W, CELL_GAP, GHOST_GAP = 56, 8, 20
GHOST_W = 76
GHOST_X = 120
STRIP_X = GHOST_X + GHOST_W + GHOST_GAP
BIT_LABEL_Y = 800
CARD_BOX = (90, 930, 1710, 1062)
EQUATION_Y = 996


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
    """Liberation Sans para rótulos y DejaVu Sans Mono para las cifras."""
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


def rich_center(draw: ImageDraw.ImageDraw, cx: float, cy: int, parts: list[Part],
                size: int) -> None:
    """Texto en tramos con color, peso y fuente propios, centrado en `cx`."""
    total = sum(draw.textlength(text, font=font(size, bold=bold, mono=mono))
                for text, _, bold, mono in parts)
    cursor = cx - total / 2
    for text, color, bold, mono in parts:
        face = font(size, bold=bold, mono=mono)
        draw.text((cursor, cy), text, font=face, fill=rgb(color), anchor="lm")
        cursor += draw.textlength(text, font=face)


# ---------------------------------------------------------------------------
# 3. Piezas del diagrama
# ---------------------------------------------------------------------------
def dashed_rect(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], radius: int,
                color: str, width: int = 3, dash: int = 16, gap: int = 10) -> None:
    """Borde discontinuo con esquinas redondeadas (las esquinas van macizas)."""
    x0, y0, x1, y1 = box
    for y in (y0, y1):
        x = x0 + radius
        while x < x1 - radius:
            x2 = min(x + dash, x1 - radius)
            draw.line((x, y, x2, y), fill=rgb(color), width=width)
            x = x2 + gap
    for x in (x0, x1):
        y = y0 + radius
        while y < y1 - radius:
            y2 = min(y + dash, y1 - radius)
            draw.line((x, y, x, y2), fill=rgb(color), width=width)
            y = y2 + gap
    d = radius * 2
    draw.arc((x0, y0, x0 + d, y0 + d), 180, 270, fill=rgb(color), width=width)
    draw.arc((x1 - d, y0, x1, y0 + d), 270, 360, fill=rgb(color), width=width)
    draw.arc((x0, y1 - d, x0 + d, y1), 90, 180, fill=rgb(color), width=width)
    draw.arc((x1 - d, y1 - d, x1, y1), 0, 90, fill=rgb(color), width=width)


def draw_strip(draw: ImageDraw.ImageDraw) -> None:
    """La celda fantasma del 1 implícito y las 23 celdas guardadas de la mantisa."""
    cell_h = CELL_BOT - CELL_TOP
    teal_fill = mix(TEAL, BG, 0.85)
    amber_fill = mix(AMBER, BG, 0.85)

    # El bit que no se guarda: celda de borde discontinuo con el 1 en contorno.
    ghost = (GHOST_X, CELL_TOP, GHOST_X + GHOST_W, CELL_BOT)
    draw.rounded_rectangle(ghost, radius=12, fill=amber_fill)
    dashed_rect(draw, ghost, radius=12, color=AMBER, width=3)
    draw.text((GHOST_X + GHOST_W / 2, CELL_TOP + cell_h / 2), "1",
              font=font(124, bold=True, mono=True), fill=amber_fill,
              stroke_width=4, stroke_fill=rgb(AMBER), anchor="mm")

    # Las 23 celdas que sí ocupan espacio.
    for index in range(23):
        x = STRIP_X + index * (CELL_W + CELL_GAP)
        draw.rounded_rectangle((x, CELL_TOP, x + CELL_W, CELL_BOT), radius=12,
                               fill=teal_fill, outline=rgb(TEAL), width=2)


def strip_right() -> int:
    """Borde derecho de la tira de la mantisa."""
    return STRIP_X + 23 * CELL_W + 22 * CELL_GAP


def draw_labels(draw: ImageDraw.ImageDraw) -> None:
    """Rótulos: la celda fantasma y la mantisa, más la cota de los 23 bits."""
    draw.text((GHOST_X + GHOST_W / 2 + 7, LABEL_Y), "1 implícito", font=font(30),
              fill=rgb(AMBER), anchor="ms")
    right = strip_right()
    draw.text(((STRIP_X + right) / 2, LABEL_Y), "mantisa", font=font(30),
              fill=rgb(TEAL), anchor="ms")

    # Cota de los 23 bits guardados.
    bracket_y = CELL_BOT + 26
    draw.line((STRIP_X, bracket_y, right, bracket_y), fill=rgb(FAINT), width=2)
    for x in (STRIP_X, right):
        draw.line((x, bracket_y, x, bracket_y - 10), fill=rgb(FAINT), width=2)
    draw.text(((STRIP_X + right) / 2, BIT_LABEL_Y), "23 bits", font=font(28),
              fill=rgb(MUTED), anchor="ms")


PARTS: list[Part] = [
        ("23", TEXT, True, True),
        (" guardados", MUTED, False, False),
        ("   +   ", MUTED, False, False),
        ("1 implícito", AMBER, True, False),
        ("   =   ", MUTED, False, False),
        ("24 bits de precisión", TEAL, True, False),
]
EQ_SIZE = 40


def draw_equation(draw: ImageDraw.ImageDraw) -> None:
    """La cuenta al pie: 23 guardados más el implícito, 24 de precisión."""
    draw.rounded_rectangle(CARD_BOX, radius=22, fill=rgb(CARD), outline=rgb(HAIR), width=2)
    rich_center(draw, W / 2, EQUATION_Y, PARTS, size=EQ_SIZE)


# ---------------------------------------------------------------------------
# 4. Composición
# ---------------------------------------------------------------------------
def draw() -> Image.Image:
    """Compón el diagrama y devuelve la imagen final."""
    image, canvas = new_canvas()

    canvas.text((MARGIN, TITLE_Y), "El bit gratis", font=font(60, bold=True),
                fill=rgb(TEXT), anchor="lm")
    canvas.text((MARGIN, SUBTITLE_Y), "siempre vale 1, así que no se guarda",
                font=font(32), fill=rgb(MUTED), anchor="lm")

    draw_strip(canvas)
    draw_labels(canvas)
    draw_equation(canvas)

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

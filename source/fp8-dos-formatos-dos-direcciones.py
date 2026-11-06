""""FP8: dos formatos, dos direcciones"

Diagrama propuesto por el estudio de diagramas a partir de la recomendación
«FP8 con dos formatos y dos direcciones»: el mismo byte de 8 bits se reparte de
dos maneras (E4M3: 1/4/3; E5M2: 1/5/2) y cada reparto se usa en una dirección
distinta de la red (E4M3 hacia adelante con pesos y activaciones; E5M2 hacia
atrás con los gradientes).

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
BG = "#090B0D"          # --bg
CARD = "#111519"        # --surface
ELEV = "#20262D"        # --surface-3
LINE_CARD = "#262A2E"   # borde de 1 px sobre tarjeta
LINE_STRONG = "#3F4142" # borde fuerte
TEXT = "#F8FAFC"
MUTED = "#94A3B8"
TEAL = "#2DD4BF"        # acento primario (mantisa)
AMBER = "#F59E0B"       # acento secundario (retropropagación)
GREEN = "#4ADE80"       # éxito (propagación hacia adelante)
RED = "#F87171"         # signo

SIGN = RED
EXP = "#94A3B8"
MANT = TEAL

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
    """Carga Liberation Sans (la sans del blog) o DejaVu Sans Mono."""
    if mono:
        path = DEJAVU / ("DejaVuSansMono-Bold.ttf" if bold else "DejaVuSansMono.ttf")
    else:
        path = LIBERATION / ("LiberationSans-Bold.ttf" if bold else "LiberationSans-Regular.ttf")
    try:
        return ImageFont.truetype(str(path), size)
    except OSError:
        try:
            fallback = DEJAVU / ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf")
            return ImageFont.truetype(str(fallback), size)
        except OSError:
            return ImageFont.load_default()


def new_canvas() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    """Lienzo oscuro sin marco (el CSS del blog pone las esquinas)."""
    image = Image.new("RGB", (W, H), rgb(BG))
    return image, ImageDraw.Draw(image)


def card(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, lane: str) -> None:
    """Tarjeta con el filo del color de su dirección."""
    draw.rounded_rectangle((x, y, x + w, y + h), radius=24, fill=rgb(CARD),
                           outline=rgb(LINE_CARD), width=2)
    draw.rounded_rectangle((x + 2, y + 22, x + 9, y + h - 22), radius=3, fill=rgb(lane))


def arrow(draw: ImageDraw.ImageDraw, start, end, color: str, width: int = 7, head: int = 28) -> None:
    """Flecha recta con cabeza triangular."""
    draw.line((start, end), fill=rgb(color), width=width)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    left = (end[0] - head * math.cos(angle - math.pi / 7), end[1] - head * math.sin(angle - math.pi / 7))
    right = (end[0] - head * math.cos(angle + math.pi / 7), end[1] - head * math.sin(angle + math.pi / 7))
    draw.polygon([end, left, right], fill=rgb(color))


def pill(draw: ImageDraw.ImageDraw, x: int, cy: int, text: str, color: str,
         base: str = BG, size: int = 28) -> int:
    """Etiqueta compacta con relleno tenue del color y texto del color pleno."""
    face = font(size, bold=True)
    width = int(draw.textlength(text, font=face) + 44)
    height = size + 26
    draw.rounded_rectangle((x, cy - height / 2, x + width, cy + height / 2), radius=height / 2,
                           fill=mix(color, base, 0.86), outline=mix(color, base, 0.52), width=2)
    draw.text((x + width / 2, cy), text, font=face, fill=rgb(color), anchor="mm")
    return width


def rich_text(draw: ImageDraw.ImageDraw, x: int, cy: int,
              parts: list[tuple[str, str, bool]], size: int) -> None:
    """Texto en varios tramos con color y peso propios, alineado a la izquierda."""
    cursor = x
    for text, color, bold in parts:
        face = font(size, bold=bold)
        draw.text((cursor, cy), text, font=face, fill=rgb(color), anchor="lm")
        cursor += draw.textlength(text, font=face)


# ---------------------------------------------------------------------------
# 3. Piezas del diagrama
# ---------------------------------------------------------------------------
CELL_W, CELL_H, CELL_GAP = 62, 68, 6
HEADER_OFF = 52
STRIP_OFF = 112
BALANCE_OFF = 300


def bit_strip(draw: ImageDraw.ImageDraw, x: int, y: int,
              fields: list[tuple[str, int, str]]) -> None:
    """Ocho cajitas de bit agrupadas por campo, con su llave y su nombre."""
    cursor = x
    groups: list[tuple[str, int, int, str]] = []
    bit = 7
    for name, count, color in fields:
        group_x = cursor
        group_w = count * CELL_W + (count - 1) * CELL_GAP
        for index in range(count):
            cell_x = cursor + index * (CELL_W + CELL_GAP)
            draw.rounded_rectangle((cell_x, y, cell_x + CELL_W, y + CELL_H), radius=12,
                                   fill=rgb(color))
            draw.text((cell_x + CELL_W / 2, y + CELL_H / 2), str(bit),
                      font=font(30, bold=True, mono=True), fill=rgb(BG), anchor="mm")
            bit -= 1
        cursor = group_x + group_w + CELL_GAP
        groups.append((name, group_x, group_w, color))

    bracket_y = y + CELL_H + 16
    for name, group_x, group_w, color in groups:
        draw.line((group_x, bracket_y, group_x + group_w, bracket_y), fill=rgb(color), width=3)
        draw.line((group_x, bracket_y, group_x, bracket_y + 9), fill=rgb(color), width=3)
        draw.line((group_x + group_w, bracket_y, group_x + group_w, bracket_y + 9),
                  fill=rgb(color), width=3)
        draw.text((group_x + group_w / 2, bracket_y + 24), name,
                  font=font(28), fill=rgb(color), anchor="mm")


def format_card(draw: ImageDraw.ImageDraw, y0: int, name: str, max_text: str,
                fields: list[tuple[str, int, str]], pill_text: str, pill_color: str,
                note_parts: list[tuple[str, str, bool]]) -> None:
    """Tarjeta de formato: nombre, máximo, tira de bits y balance en una línea."""
    x0, w, h = MARGIN, CARD_W, CARD_H
    lane = GREEN if pill_color == GREEN else AMBER
    card(draw, x0, y0, w, h, lane)

    draw.text((x0 + 40, y0 + HEADER_OFF), name, font=font(46, bold=True), fill=rgb(TEXT), anchor="lm")
    draw.text((x0 + w - 40, y0 + HEADER_OFF + 2), max_text, font=font(36, bold=True),
              fill=rgb(TEXT), anchor="rm")

    bit_strip(draw, x0 + 40, y0 + STRIP_OFF, fields)

    pill(draw, x0 + 40, y0 + BALANCE_OFF, pill_text, pill_color, base=CARD, size=30)

    # Nota alineada a la derecha, con las cifras en blanco.
    x_right = x0 + w - 40
    cursor = x_right
    for text, color, bold in reversed(note_parts):
        face = font(28, bold=bold)
        cursor -= draw.textlength(text, font=face)
        draw.text((cursor, y0 + BALANCE_OFF), text, font=face, fill=rgb(color), anchor="lm")


# ---------------------------------------------------------------------------
# 4. Composición
# ---------------------------------------------------------------------------
CARD_W, CARD_H = 620, 360
CARD_Y = (320, 730)
FWD_Y = CARD_Y[0] + CARD_H // 2      # 500
BWD_Y = CARD_Y[1] + CARD_H // 2      # 910
FLOW_X0, FLOW_X1 = 724, 1710
BLOCK = (1120, 450, 1420, 960)


def draw() -> Image.Image:
    """Compón el diagrama y devuelve la imagen final."""
    image, canvas = new_canvas()

    # Cabecera
    canvas.text((MARGIN, 124), "FP8: dos formatos, dos direcciones",
                font=font(62, bold=True), fill=rgb(TEXT), anchor="lm")
    rich_text(canvas, MARGIN, 200, [
        ("E4M3", GREEN, True),
        (" adelante · ", MUTED, False),
        ("E5M2", AMBER, True),
        (" atrás", MUTED, False),
    ], size=32)

    # Tarjetas de formato (izquierda)
    format_card(
        canvas, CARD_Y[0], "E4M3", "máx 448",
        [("signo", 1, SIGN), ("exponente", 4, EXP), ("mantisa", 3, MANT)],
        "+ precisión", GREEN,
        [("sin inf · ", MUTED, False), ("1 NaN", TEXT, True)],
    )
    format_card(
        canvas, CARD_Y[1], "E5M2", "máx 57.344",
        [("signo", 1, SIGN), ("exponente", 5, EXP), ("mantisa", 2, MANT)],
        "+ rango", AMBER,
        [("saltos de ", MUTED, False), ("25 %", TEXT, True)],
    )

    # Flujos: adelante hacia la derecha, atrás hacia la izquierda
    arrow(canvas, (FLOW_X0, FWD_Y), (FLOW_X1, FWD_Y), GREEN)
    arrow(canvas, (FLOW_X1, BWD_Y), (FLOW_X0, BWD_Y), AMBER)

    # Bloque central que atraviesan los dos flujos
    canvas.rounded_rectangle(BLOCK, radius=32, fill=rgb(ELEV), outline=rgb(LINE_STRONG), width=2)
    canvas.text(((BLOCK[0] + BLOCK[2]) / 2, (BLOCK[1] + BLOCK[3]) / 2), "bloque",
                font=font(44), fill=rgb(MUTED), anchor="mm")

    # Qué tensores van en cada dirección
    pill(canvas, 738, FWD_Y - 50, "pesos y activaciones", GREEN, base=BG, size=30)
    pill(canvas, 1452, BWD_Y + 50, "gradientes", AMBER, base=BG, size=30)

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

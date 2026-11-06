""""INT4: 4 bits y 16 niveles"

Diagrama propuesto por el estudio de diagramas a partir de la recomendación
«INT4: 4 bits y 16 niveles»: el mismo reparto del byte con la mitad de cajitas
(1 bit de signo y 3 de valor, dieciséis códigos de −8 a +7). Su rejilla de
dieciséis escalones se compara con la de INT8 (256 niveles) dibujada detrás en
gris: el escalón de INT4 es dieciséis veces más grueso.

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
AXIS = "#3F4142"
TEXT = "#F8FAFC"
MUTED = "#94A3B8"
REF_GREY = "#64748B"
AMBER = "#F59E0B"
TEAL = "#2DD4BF"

CELL_TEXT_AMBER = "#2A1A00"
CELL_TEXT_TEAL = "#06201C"

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


def rich_right(draw: ImageDraw.ImageDraw, right: int, cy: int, parts: list[Part], size: int) -> None:
    """Como `rich`, pero alineado a la derecha."""
    total = sum(draw.textlength(text, font=font(size, bold=bold, mono=mono))
                for text, _, bold, mono in parts)
    rich(draw, round(right - total), cy, parts, size)


# ---------------------------------------------------------------------------
# 3. Piezas del diagrama
# ---------------------------------------------------------------------------
CELL, GAP, NBITS = 130, 6, 4
STRIP_X = MARGIN
STRIP_W = NBITS * CELL + (NBITS - 1) * GAP      # 482
STRIP_Y = 322

AXIS_X0, AXIS_X1 = MARGIN, W - MARGIN
AXIS_Y = 700

TITLE_Y, SUB_Y = 140, 216

INT4_TICK_TOP = AXIS_Y - 110
INT8_TICK_TOP = AXIS_Y - 50
STEP_INDEX = 8                                  # escalón entre los niveles 8 y 9


def level_x(index: int, levels: int) -> float:
    """Centro del nivel `index` cuando hay `levels` niveles en el ancho."""
    return AXIS_X0 + (index + 0.5) / levels * (AXIS_X1 - AXIS_X0)


def draw_strip(draw: ImageDraw.ImageDraw) -> None:
    """La tira del INT4: 1 bit de signo y 3 de valor, con su número de bit."""
    fields = (
        ("signo", 1, AMBER, CELL_TEXT_AMBER),
        ("valor (3 bits)", 3, TEAL, CELL_TEXT_TEAL),
    )
    x = STRIP_X
    bit = NBITS - 1
    for name, count, color, text_color in fields:
        group_w = count * CELL + (count - 1) * GAP
        for index in range(count):
            cell_x = x + index * (CELL + GAP)
            draw.rounded_rectangle((cell_x, STRIP_Y, cell_x + CELL, STRIP_Y + CELL), radius=16,
                                   fill=rgb(color))
            draw.text((cell_x + CELL / 2, STRIP_Y + CELL / 2), str(bit),
                      font=font(30, bold=True, mono=True), fill=rgb(text_color), anchor="mm")
            bit -= 1
        draw.text((x + group_w / 2, STRIP_Y - 26), name,
                  font=font(28), fill=rgb(color), anchor="mm")
        x += group_w + GAP


def draw_scale_card(draw: ImageDraw.ImageDraw) -> None:
    """Caja de la escala por bloque que usa INT4."""
    box = (1400, 306, W - MARGIN, 486)
    draw.rounded_rectangle(box, radius=22, fill=rgb(CARD), outline=rgb(HAIR), width=2)
    draw.text((box[0] + 34, box[1] + 50), "escala por bloque", font=font(30, bold=True),
              fill=rgb(TEXT), anchor="lm")
    draw.text((box[0] + 34, box[1] + 106), "64 / 128 elementos", font=font(26),
              fill=rgb(MUTED), anchor="lm")


def draw_axis(draw: ImageDraw.ImageDraw) -> None:
    """Rejilla de INT8 (referencia, detrás) y de INT4 (delante)."""
    # Referencia INT8: 256 niveles en gris tenue, detrás
    for index in range(256):
        x = level_x(index, 256)
        draw.line((x, INT8_TICK_TOP, x, AXIS_Y), fill=rgb(REF_GREY), width=2)

    # El escalón de INT4 resaltado en ámbar
    left, right = level_x(STEP_INDEX, 16), level_x(STEP_INDEX + 1, 16)

    # La recta y los 16 niveles de INT4
    draw.line((AXIS_X0, AXIS_Y, AXIS_X1, AXIS_Y), fill=rgb(AXIS), width=3)
    for index in range(16):
        x = level_x(index, 16)
        color = AMBER if index in (STEP_INDEX, STEP_INDEX + 1) else TEAL
        draw.line((x, INT4_TICK_TOP, x, AXIS_Y), fill=rgb(color), width=10 if color == AMBER else 8)

    # Cota del escalón: el tramo de recta entre sus dos niveles, en ámbar
    draw.line((left, AXIS_Y, right, AXIS_Y), fill=rgb(AMBER), width=12)

    draw.text((AXIS_X0, 552), "−8 … +7", font=font(28), fill=rgb(MUTED), anchor="lm")
    rich_right(draw, AXIS_X1, 552, [
        ("referencia INT8 (256 niveles)", REF_GREY, False, False),
    ], size=26)


def draw_comparisons(draw: ImageDraw.ImageDraw) -> None:
    """Las dos comparaciones, al pie de la recta."""
    rich(draw, MARGIN, 760, [
        ("16", TEXT, True, True),
        (" códigos", MUTED, False, False),
    ], size=30)
    rich_center(draw, (level_x(STEP_INDEX, 16) + level_x(STEP_INDEX + 1, 16)) / 2, 760, [
        ("el escalón es ", MUTED, False, False),
        ("16", TEXT, True, True),
        (" veces más grueso", MUTED, False, False),
    ], size=30)


def draw_note(draw: ImageDraw.ImageDraw) -> None:
    """Nota del complemento a dos, al pie."""
    box = (MARGIN, 930, W - MARGIN, 1060)
    draw.rounded_rectangle(box, radius=22, fill=rgb(CARD), outline=rgb(HAIR), width=2)
    rich_center(draw, W / 2, (box[1] + box[3]) / 2, [
        ("el −8 no tiene positivo: ", MUTED, False, False),
        ("complemento a dos", TEXT, False, False),
    ], size=32)


# ---------------------------------------------------------------------------
# 4. Composición
# ---------------------------------------------------------------------------
def draw() -> Image.Image:
    """Compón el diagrama y devuelve la imagen final."""
    image, canvas = new_canvas()

    canvas.text((MARGIN, TITLE_Y), "INT4: 4 bits y 16 niveles",
                font=font(60, bold=True), fill=rgb(TEXT), anchor="lm")
    canvas.text((MARGIN, SUB_Y), "el mismo reparto con la mitad de cajitas",
                font=font(34), fill=rgb(MUTED), anchor="lm")

    draw_strip(canvas)
    draw_scale_card(canvas)
    draw_axis(canvas)
    draw_comparisons(canvas)
    draw_note(canvas)

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

""""Cuántos bits ocupa de verdad un INT4"

Diagrama propuesto por el estudio de diagramas a partir de la recomendación
«Cuántos bits ocupa de verdad un INT4»: un INT4 no está solo, cada bloque de
valores lleva su escala y esa escala también ocupa. Arriba, una escala FP32
cada 64 pesos (4 + 0,5 = 4,5 bits/parámetro); abajo, la doble cuantización de
QLoRA (escala FP8 + escala de escalas FP32, 4 + 0,125 + 0,002 ≈ 4,127). Al pie,
la barra apilada con las tres porciones.

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
FAINT = "#64748B"
REF_GREY = "#94A3B8"
AMBER = "#F59E0B"
TEAL = "#2DD4BF"

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
    """Liberation Sans para rótulos y DejaVu Sans Mono para las cuentas."""
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
CELL, GAP, NCELLS = 110, 10, 6
CELLS_X = MARGIN
CELLS_W = NCELLS * CELL + (NCELLS - 1) * GAP     # 650
BOX_X, BOX_W = 830, 210
SECOND_X, SECOND_W = 1070, 210

ROW1_Y = 340
ROW2_Y = 580
ROW_H = CELL

TITLE_Y, SUB_Y = 130, 204
CAPTION_Y, LEGEND_Y = 810, 890
BAR_Y0, BAR_Y1 = 950, 1030


def draw_values_row(draw: ImageDraw.ImageDraw, y: int) -> None:
    """Seis cajitas de valor INT4: cada una con sus cuatro bits."""
    for index in range(NCELLS):
        x = CELLS_X + index * (CELL + GAP)
        draw.rounded_rectangle((x, y, x + CELL, y + CELL), radius=16,
                               fill=mix(TEAL, BG, 0.9))
        # cuatro cuadraditos: los 4 bits de cada valor
        bit_w, bit_gap = 20, 5
        total = 4 * bit_w + 3 * bit_gap
        bx = x + (CELL - total) / 2
        by = y + (CELL - 20) / 2
        for bit in range(4):
            sx = bx + bit * (bit_w + bit_gap)
            draw.rounded_rectangle((sx, by, sx + bit_w, by + 20), radius=4, fill=rgb(TEAL))


def draw_scale_box(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, title: str,
                   detail: str, voice: str, color: str) -> None:
    """Caja de escala: título, tamaño en bits y cada cuántos elementos."""
    draw.rounded_rectangle((x, y, x + w, y + ROW_H), radius=16, fill=rgb(CARD),
                           outline=mix(color, CARD, 0.6), width=2)
    draw.rounded_rectangle((x + 2, y + 16, x + 8, y + ROW_H - 16), radius=3, fill=rgb(color))
    draw.text((x + 22, y + 26), title, font=font(24, bold=True), fill=rgb(TEXT), anchor="lm")
    draw.text((x + 22, y + 54), detail, font=font(22, mono=True), fill=rgb(color), anchor="lm")
    draw.text((x + 22, y + 79), voice, font=font(22), fill=rgb(MUTED), anchor="lm")


def draw_connector(draw: ImageDraw.ImageDraw, x0: int, x1: int, y: int) -> None:
    """Conector horizontal entre la fila y su escala."""
    draw.line((x0, y, x1, y), fill=rgb(AXIS), width=3)


def draw_equations(draw: ImageDraw.ImageDraw) -> None:
    """Las dos cuentas, a la derecha de cada fila."""
    rich_right(draw, W - MARGIN, ROW1_Y + ROW_H / 2, [
        ("4", TEXT, True, True),
        (" + ", MUTED, False, False),
        ("0,5", AMBER, True, True),
        (" = ", MUTED, False, False),
        ("4,5", TEXT, True, True),
        (" bits/parámetro", MUTED, False, False),
    ], size=30)
    rich_right(draw, W - MARGIN, ROW2_Y + ROW_H / 2, [
        ("4", TEXT, True, True),
        (" + ", MUTED, False, False),
        ("0,125", AMBER, True, True),
        (" + ", MUTED, False, False),
        ("0,002", REF_GREY, True, True),
        (" ≈ ", MUTED, False, False),
        ("4,127", TEXT, True, True),
    ], size=30)


def draw_footer(image: Image.Image, draw: ImageDraw.ImageDraw) -> None:
    """Cuenta de cierre, leyenda y barra apilada de las tres porciones."""
    rich(draw, MARGIN, CAPTION_Y, [
        ("el sobrecosto baja de ", MUTED, False, False),
        ("0,5", AMBER, True, True),
        (" a ", MUTED, False, False),
        ("0,127", TEXT, True, True),
        (" bits", MUTED, False, False),
    ], size=32)

    # Leyenda de la barra
    legend = (
        (MARGIN, TEAL, "valor", "4", " bits"),
        (700, AMBER, "escala", "0,125", ""),
        (1150, REF_GREY, "escala de escalas", "0,002", ""),
    )
    for x, color, name, value, unit in legend:
        draw.ellipse((x, LEGEND_Y - 7, x + 14, LEGEND_Y + 7), fill=rgb(color))
        rich(draw, x + 26, LEGEND_Y, [
            (name + " · ", MUTED, False, False),
            (value, TEXT, True, True),
            (unit, MUTED, False, False),
        ], size=26)

    # Barra apilada, recortada con las esquinas redondeadas
    layer = Image.new("RGB", (W, H), rgb(BG))
    bar = ImageDraw.Draw(layer)
    bar.rectangle((MARGIN, BAR_Y0, W - MARGIN, BAR_Y1), fill=rgb(TEAL))
    bar.rectangle((1656, BAR_Y0, 1704, BAR_Y1), fill=rgb(AMBER))
    bar.rectangle((1706, BAR_Y0, W - MARGIN, BAR_Y1), fill=rgb(REF_GREY))
    bar.line((1655, BAR_Y0, 1655, BAR_Y1), fill=rgb(HAIR), width=2)
    bar.line((1705, BAR_Y0, 1705, BAR_Y1), fill=rgb(HAIR), width=2)
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).rounded_rectangle((MARGIN, BAR_Y0, W - MARGIN, BAR_Y1),
                                           radius=14, fill=255)
    image.paste(layer, (0, 0), mask)


# ---------------------------------------------------------------------------
# 4. Composición
# ---------------------------------------------------------------------------
def draw() -> Image.Image:
    """Compón el diagrama y devuelve la imagen final."""
    image, canvas = new_canvas()

    canvas.text((MARGIN, TITLE_Y), "Cuántos bits ocupa de verdad un INT4",
                font=font(58, bold=True), fill=rgb(TEXT), anchor="lm")
    canvas.text((MARGIN, SUB_Y), "el valor y su escala",
                font=font(32), fill=rgb(MUTED), anchor="lm")

    # Fila superior: valores + escala FP32
    canvas.text((MARGIN, ROW1_Y - 28), "valores INT4 · 4 bits",
                font=font(26), fill=rgb(MUTED), anchor="lm")
    draw_values_row(canvas, ROW1_Y)
    draw_connector(canvas, CELLS_X + CELLS_W, BOX_X, ROW1_Y + ROW_H // 2)
    draw_scale_box(canvas, BOX_X, ROW1_Y, BOX_W, "escala FP32",
                   "32 bits", "cada 64 pesos", AMBER)

    # Fila inferior: los mismos valores con doble cuantización
    draw_values_row(canvas, ROW2_Y)
    draw_connector(canvas, CELLS_X + CELLS_W, BOX_X, ROW2_Y + ROW_H // 2)
    draw_scale_box(canvas, BOX_X, ROW2_Y, BOX_W, "escala FP8",
                   "8 bits", "cada 64 pesos", AMBER)
    draw_connector(canvas, BOX_X + BOX_W, SECOND_X, ROW2_Y + ROW_H // 2)
    draw_scale_box(canvas, SECOND_X, ROW2_Y, SECOND_W, "escala de escalas",
                   "FP32", "cada 256 escalas", REF_GREY)

    draw_equations(canvas)
    draw_footer(image, canvas)

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

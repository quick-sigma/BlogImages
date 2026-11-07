"""«MXFP4 frente a NVFP4»

Diagrama propuesto por el estudio de diagramas a partir de la recomendación
«MXFP4 frente a NVFP4»: el mismo elemento E2M1 con dos formas de guardar la
escala (bloques de 32 con E8M0 frente a bloques de 16 con E4M3 y escala global)
y sus bits efectivos por peso.

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


# ---------------------------------------------------------------------------
# 3. Piezas del diagrama
# ---------------------------------------------------------------------------
PANEL_L = (90, 280, 880, 900)
PANEL_R = (920, 280, 1710, 900)

CELL_W, CELL_H, GAP = 18, 100, 4


def draw_panel(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], title: str) -> None:
    """Tarjeta del panel con su título."""
    x0, y0, x1, y1 = box
    draw.rounded_rectangle((x0, y0, x1, y1), radius=20, fill=rgb(CARD),
                           outline=rgb(HAIR), width=2)
    draw.text((x0 + 30, y0 + 52), title, font=font(26, bold=True), fill=rgb(TEXT), anchor="lm")


def draw_block(draw: ImageDraw.ImageDraw, x0: int, y: int, count: int) -> int:
    """Fila de celdas E2M1; devuelve el ancho total."""
    for i in range(count):
        x = x0 + i * (CELL_W + GAP)
        draw.rounded_rectangle((x, y, x + CELL_W, y + CELL_H), radius=4,
                               fill=mix(TEAL, BG, 0.85), outline=rgb(TEAL), width=1)
    return count * (CELL_W + GAP) - GAP


def draw_scale_box(draw: ImageDraw.ImageDraw, cx: int, y: int, label: str) -> None:
    """Caja de escala local: E8M0 o E4M3."""
    width, height = 130, 48
    draw.rounded_rectangle((cx - width / 2, y, cx + width / 2, y + height), radius=10,
                           fill=mix(AMBER, BG, 0.88), outline=mix(AMBER, BG, 0.5), width=2)
    draw.text((cx, y + height / 2), label, font=font(20, bold=True, mono=True),
              fill=rgb(AMBER), anchor="mm")
    draw.line((cx, y + height, cx, y + height + 20), fill=mix(AMBER, BG, 0.45), width=2)


def draw_bits_bar(image: Image.Image, draw: ImageDraw.ImageDraw, x0: int, y: int,
                  width: int, split: float, number: str) -> None:
    """Barra apilada de bits efectivos: elemento en teal y escala en ámbar."""
    height = 32
    split_x = round(x0 + width * split)
    layer = Image.new("RGB", (W, H), rgb(BG))
    bar = ImageDraw.Draw(layer)
    bar.rectangle((x0, y, x0 + width, y + height), fill=rgb(TEAL))
    bar.rectangle((split_x, y, x0 + width, y + height), fill=rgb(AMBER))
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).rounded_rectangle((x0, y, x0 + width, y + height), radius=10, fill=255)
    image.paste(layer, (0, 0), mask)
    draw.text((x0, y - 30), "bits efectivos por peso", font=font(20), fill=rgb(FAINT), anchor="lm")
    text_width = draw.textlength(number, font=font(26, bold=True, mono=True))
    draw.text((x0 + width - text_width, y - 30), number, font=font(26, bold=True, mono=True),
              fill=rgb(TEXT), anchor="lm")


def draw_global_bracket(draw: ImageDraw.ImageDraw, x0: int, x1: int, y: int, label: str) -> None:
    """Llave gris de la escala global, por encima de los dos bloques."""
    draw.line((x0, y, x1, y), fill=mix(MUTED, BG, 0.45), width=2)
    for x in (x0, x1):
        draw.line((x, y, x, y - 14), fill=mix(MUTED, BG, 0.45), width=2)
    draw.text(((x0 + x1) / 2, y - 34), label, font=font(22), fill=rgb(MUTED), anchor="mm")


def draw_legend(draw: ImageDraw.ImageDraw, y: int) -> None:
    """Leyenda de colores al pie."""
    items = (
        (MARGIN, TEAL, "E2M1 · 4 bits"),
        (520, AMBER, "escala local · 8 bits"),
        (1080, MUTED, "escala global · FP32"),
    )
    for x, color, text in items:
        draw.ellipse((x, y - 7, x + 14, y + 7), fill=rgb(color))
        draw.text((x + 26, y), text, font=font(22), fill=rgb(MUTED), anchor="lm")


# ---------------------------------------------------------------------------
# 4. Composición
# ---------------------------------------------------------------------------
def draw() -> Image.Image:
    """Compón el diagrama y devuelve la imagen final."""
    image, canvas = new_canvas()

    canvas.text((MARGIN, 140), "MXFP4 frente a NVFP4",
                font=font(58, bold=True), fill=rgb(TEXT), anchor="lm")

    draw_panel(canvas, PANEL_L, "MXFP4 (OCP)")
    draw_panel(canvas, PANEL_R, "NVFP4 (NVIDIA)")

    # MXFP4: un bloque de 32 con su escala E8M0
    draw_scale_box(canvas, 470, 450, "E8M0")
    draw_block(canvas, 120, 520, 32)
    canvas.text((120, 660), "E2M1", font=font(22), fill=rgb(MUTED), anchor="lm")
    canvas.text((820, 660), "bloque 32", font=font(22), fill=rgb(MUTED), anchor="rm")
    draw_bits_bar(image, canvas, 120, 770, 580, 4 / 4.25, "≈4,25 bits")

    # NVFP4: dos bloques de 16 con E4M3 cada uno y una escala global FP32
    draw_global_bracket(canvas, 960, 1664, 424, "escala FP32")
    for block_x, scale_x in ((960, 1126), (1332, 1498)):
        draw_scale_box(canvas, scale_x, 450, "E4M3")
        draw_block(canvas, block_x, 520, 16)
    canvas.text((960, 660), "E2M1", font=font(22), fill=rgb(MUTED), anchor="lm")
    canvas.text((1664, 660), "bloque 16", font=font(22), fill=rgb(MUTED), anchor="rm")
    draw_bits_bar(image, canvas, 950, 770, 580, 4 / 4.5, "≈4,50 bits")

    draw_legend(canvas, 1000)

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

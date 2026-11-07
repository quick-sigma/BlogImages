"""«LoRA en todas las capas»

Diagrama propuesto por el estudio de diagramas a partir de la recomendación
«LoRA en todas las capas»: QLoRA demuestra que los adaptadores van en todas las
capas lineales del Transformer (atención y feed-forward), no solo en Q, K, V y O;
la base NF4 queda congelada y solo se entrena un 0,2 %.

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
    """Liberation Sans para rótulos y DejaVu Sans Mono para las siglas."""
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


def rich(draw: ImageDraw.ImageDraw, x: int, cy: int, parts: list[tuple[str, str, bool, bool]],
         size: int) -> int:
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
BLOCK = (90, 250, 1080, 1010)
LAYER_X0, LAYER_X1 = 130, 1040
LAYER_H = 90
LAYER_Y = (360, 485, 610, 735, 860)
LAYERS = ("Q", "K", "V", "O", "FFN")
ADAPTER_X0, ADAPTER_X1 = 1120, 1300
ADAPTER_H = 58
BUS_X = 1380


def draw_padlock(draw: ImageDraw.ImageDraw, x: int, y: int) -> None:
    """Candado pequeño: cuerpo y arco."""
    draw.arc((x + 7, y - 4, x + 31, y + 22), start=180, end=360, fill=rgb(MUTED), width=5)
    draw.line((x + 7, y + 10, x + 7, y + 18), fill=rgb(MUTED), width=5)
    draw.line((x + 31, y + 10, x + 31, y + 18), fill=rgb(MUTED), width=5)
    draw.rounded_rectangle((x, y + 14, x + 38, y + 42), radius=7, fill=mix(MUTED, BG, 0.72))


def draw_block(draw: ImageDraw.ImageDraw) -> None:
    """Tarjeta del bloque Transformer con sus capas lineales en NF4."""
    x0, y0, x1, y1 = BLOCK
    draw.rounded_rectangle((x0, y0, x1, y1), radius=20, fill=rgb(CARD),
                           outline=rgb(HAIR), width=2)
    draw_padlock(draw, x0 + 30, y0 + 28)
    draw.text((x0 + 78, y0 + 46), "base NF4 congelada", font=font(24, bold=True),
              fill=rgb(MUTED), anchor="lm")


def draw_layers(draw: ImageDraw.ImageDraw) -> None:
    """Una barra por capa lineal, en teal apagado."""
    for label, y in zip(LAYERS, LAYER_Y):
        draw.rounded_rectangle((LAYER_X0, y, LAYER_X1, y + LAYER_H), radius=12,
                               fill=mix(TEAL, BG, 0.85), outline=mix(TEAL, BG, 0.4), width=2)
        draw.text(((LAYER_X0 + LAYER_X1) / 2, y + LAYER_H / 2), label,
                  font=font(34, bold=True, mono=True), fill=rgb(TEAL), anchor="mm")


def draw_adapters(draw: ImageDraw.ImageDraw) -> None:
    """Un adaptador LoRA al lado de cada capa, en ámbar."""
    for label, y in zip(LAYERS, LAYER_Y):
        cy = y + LAYER_H / 2
        draw.line((LAYER_X1, cy, ADAPTER_X0, cy), fill=rgb(AXIS), width=2)
        draw.rounded_rectangle((ADAPTER_X0, cy - ADAPTER_H / 2, ADAPTER_X1, cy + ADAPTER_H / 2),
                               radius=10, fill=mix(AMBER, BG, 0.85),
                               outline=mix(AMBER, BG, 0.45), width=2)
        draw.text(((ADAPTER_X0 + ADAPTER_X1) / 2, cy), "+", font=font(30, bold=True),
                  fill=rgb(AMBER), anchor="mm")


def draw_gradients(draw: ImageDraw.ImageDraw) -> None:
    """Bus de gradientes que entra solo en los adaptadores."""
    draw.text((BUS_X + 30, BLOCK[1] + 60), "gradientes", font=font(22), fill=rgb(MUTED),
              anchor="lm")
    top = LAYER_Y[0] + LAYER_H / 2
    bottom = LAYER_Y[-1] + LAYER_H / 2
    draw.line((BUS_X, top, BUS_X, bottom), fill=mix(MUTED, BG, 0.45), width=4)
    for y in LAYER_Y:
        cy = y + LAYER_H / 2
        draw.line((BUS_X, cy, ADAPTER_X1 + 4, cy), fill=mix(MUTED, BG, 0.45), width=4)
        draw.polygon([(ADAPTER_X1 + 4, cy), (ADAPTER_X1 + 20, cy - 9), (ADAPTER_X1 + 20, cy + 9)],
                     fill=rgb(MUTED))


# ---------------------------------------------------------------------------
# 4. Composición
# ---------------------------------------------------------------------------
def draw() -> Image.Image:
    """Compón el diagrama y devuelve la imagen final."""
    image, canvas = new_canvas()

    canvas.text((MARGIN, 140), "LoRA en todas las capas",
                font=font(58, bold=True), fill=rgb(TEXT), anchor="lm")

    draw_block(canvas)
    draw_layers(canvas)
    canvas.text((ADAPTER_X0, BLOCK[1] + 46), "adaptador 16 bits", font=font(22),
                fill=rgb(MUTED), anchor="lm")
    draw_adapters(canvas)
    draw_gradients(canvas)

    rich(canvas, MARGIN, 1075, [
        ("0,2 %", AMBER, True, False),
        (" entrenable", MUTED, False, False),
    ], size=36)

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

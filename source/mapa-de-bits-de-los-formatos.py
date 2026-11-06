"""Mapa de bits de los formatos numéricos.

Figura para el blog PyramidSpace: los cinco formatos de la tabla (FP32, FP16,
BF16, FP8 E4M3, FP8 E5M2) sobre una misma regla de bits, para ver de un golpe
cómo cada uno reparte su presupuesto entre signo, exponente y mantisa.

Decisiones de estilo (memoria de estilo del usuario):
- Paleta del tema oscuro del blog, no la paleta heredada del estudio.
- Texto mínimo: título, nombres cortos, trios de bits y leyenda. Los rangos
  numéricos ya están en la tabla que precede a la figura en el post.

Ubicación recomendada: "Después de la tabla que empieza con «|Formato|Signo / Exp. / Mantisa|Máximo normal|Menor normal|»"
"""

from __future__ import annotations

import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# 1. Paleta del tema oscuro del blog y tipografía
# ---------------------------------------------------------------------------
BG = "#090B0D"            # --bg del tema oscuro
TEXT = "#F8FAFC"          # --text
MUTED = "#94A3B8"         # --muted
FAINT = "#64748B"         # tercer nivel de texto
TEAL = "#2DD4BF"          # --accent (rango)
AMBER = "#F59E0B"         # --accent-2 (precisión)
BORDER = "#1F2123"        # --border compuesto sobre el fondo
BORDER_SOFT = "#262A2E"   # --border compuesto sobre superficie
BORDER_STRONG = "#3F4142" # borde fuerte

SIGN_FILL = "#94A3B8"     # el bit que nunca cambia, deliberadamente apagado
FIELD_FILL = (SIGN_FILL, TEAL, AMBER)

W, H = 1800, 1200
MARGIN = 90

FONT_SANS = [
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]
FONT_SANS_BOLD = [
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]
FONT_MONO = [
    "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationMono-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
]

# Metadatos rellenados por el estudio; se conservan para trazabilidad.
TITLE = "Mapa de bits de los formatos numéricos"
LOCATION = "Después de la tabla que empieza con «|Formato|Signo / Exp. / Mantisa|Máximo normal|Menor normal|»"
CONTENT = (
    "Pone los cinco formatos de la tabla sobre una misma regla de bits para que se vea "
    "cómo cada uno reparte el presupuesto entre signo, exponente y mantisa."
)
SOURCE = "diagram-studio"


def rgb(value: str) -> tuple[int, int, int]:
    """Convierte `#RRGGBB` en una tupla RGB."""
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def _first_available(paths: list[str]) -> str:
    for path in paths:
        if Path(path).is_file():
            return path
    return paths[-1]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Carga la sans neutra (Liberation Sans, DejaVu de respaldo)."""
    path = _first_available(FONT_SANS_BOLD if bold else FONT_SANS)
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def mono(size: int) -> ImageFont.FreeTypeFont:
    """Carga una monoespaciada para los contadores de bits."""
    path = _first_available(FONT_MONO)
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


# ---------------------------------------------------------------------------
# 2. Lienzo y formas
# ---------------------------------------------------------------------------
def new_canvas(width: int = W, height: int = H) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    """Crea el lienzo oscuro con su `ImageDraw`."""
    image = Image.new("RGB", (width, height), rgb(BG))
    return image, ImageDraw.Draw(image)


# ---------------------------------------------------------------------------
# 3. Datos y geometría del diagrama
# ---------------------------------------------------------------------------
FORMATS = (
    ("FP32", (1, 8, 23)),
    ("FP16", (1, 5, 10)),
    ("BF16", (1, 8, 7)),
    ("E4M3", (1, 4, 3)),
    ("E5M2", (1, 5, 2)),
)

STRIP_X = 360        # eje izquierdo común de todas las tiras
ROW_Y0 = 352         # primera tira
ROW_PITCH = 124      # separación entre tiras
CELL_W = 36          # ancho de una celda de un bit
CELL_H = 72          # alto de una celda
CELL_PITCH = 40      # paso horizontal: celda + separación
CELL_RADIUS = 8
COUNT_X = 210        # columna de los trios de bits
COUNT_SIZE = 30

RULER_BASELINE = 232
RULER_AXIS_Y = 244
RULER_TICK = 12
LEGEND_Y = 1044


def draw_ruler(canvas: ImageDraw.ImageDraw) -> None:
    """Regla de bits compartida: marcas cada 8 bits a partir del eje común."""
    end_x = STRIP_X + 32 * CELL_PITCH - (CELL_PITCH - CELL_W)
    canvas.text((MARGIN, RULER_BASELINE), "bits", font=font(24), fill=rgb(FAINT), anchor="ls")
    canvas.line((MARGIN, RULER_AXIS_Y, end_x, RULER_AXIS_Y), fill=rgb(BORDER), width=2)
    for mark in range(0, 33, 8):
        x = STRIP_X + mark * CELL_PITCH
        if mark == 32:
            x = end_x
        canvas.line((x, RULER_AXIS_Y, x, RULER_AXIS_Y + RULER_TICK), fill=rgb(BORDER_STRONG), width=2)
        canvas.text((x, RULER_BASELINE), str(mark), font=font(26), fill=rgb(MUTED), anchor="ms")


def draw_counts(canvas: ImageDraw.ImageDraw, x: int, y: int, counts: tuple[int, int, int]) -> None:
    """Trio 1·8·23 con cada cifra en el color de su campo."""
    face = mono(COUNT_SIZE)
    cursor = float(x)
    for index, count in enumerate(counts):
        piece = str(count)
        canvas.text((cursor, y), piece, font=face, fill=rgb(FIELD_FILL[index]), anchor="lm")
        cursor += canvas.textlength(piece, font=face)
        if index < len(counts) - 1:
            canvas.text((cursor + 7, y), "·", font=face, fill=rgb(FAINT), anchor="lm")
            cursor += 7 + canvas.textlength("·", font=face) + 7


def draw_strip(canvas: ImageDraw.ImageDraw, top: int, counts: tuple[int, int, int]) -> None:
    """Tira de un bit por celda, coloreada por campo."""
    bit = 0
    for field_index, count in enumerate(counts):
        for _ in range(count):
            left = STRIP_X + bit * CELL_PITCH
            canvas.rounded_rectangle(
                (left, top, left + CELL_W, top + CELL_H),
                radius=CELL_RADIUS,
                fill=rgb(FIELD_FILL[field_index]),
            )
            bit += 1


def draw_legend(canvas: ImageDraw.ImageDraw) -> None:
    """Leyenda de campos y de lo que significa cada uno."""
    entries = (
        ("signo", SIGN_FILL),
        ("exponente = rango", TEAL),
        ("mantisa = precisión", AMBER),
    )
    x = MARGIN
    for label, color in entries:
        canvas.rounded_rectangle((x, LEGEND_Y - 14, x + 28, LEGEND_Y + 14), radius=7, fill=rgb(color))
        canvas.text((x + 40, LEGEND_Y), label, font=font(32), fill=rgb(MUTED), anchor="lm")
        x += 40 + canvas.textlength(label, font=font(32)) + 64


# ---------------------------------------------------------------------------
# 4. Composición del diagrama
# ---------------------------------------------------------------------------
def draw() -> Image.Image:
    """Compón el diagrama. Devuelve la imagen final."""
    image, canvas = new_canvas()

    # Cabecera
    canvas.text((MARGIN, 70), "El reparto de bits: de FP32 a FP8",
                font=font(58, bold=True), fill=rgb(TEXT))

    draw_ruler(canvas)

    # Cinco tiras sobre el mismo eje
    for index, (name, counts) in enumerate(FORMATS):
        top = ROW_Y0 + index * ROW_PITCH
        middle = top + CELL_H // 2
        canvas.text((MARGIN, middle), name, font=font(36, bold=True), fill=rgb(TEXT), anchor="lm")
        draw_counts(canvas, COUNT_X, middle, counts)
        draw_strip(canvas, top, counts)

    draw_legend(canvas)

    return image


def save(image: Image.Image, path: str | Path | None = None) -> Path:
    """Guarda el PNG en `DIAGRAM_OUT` (o en `out.png` si se ejecuta a mano)."""
    target = Path(path or os.environ.get("DIAGRAM_OUT", "out.png"))
    target.parent.mkdir(parents=True, exist_ok=True)
    image.save(target, format="PNG")
    return target


if __name__ == "__main__":
    destination = save(draw())
    print(f"diagrama escrito en {destination}")

"""Presupuesto de memoria de un LLM

Diagrama propuesto por el estudio de diagramas a partir de una recomendación del
blog. Este archivo es autocontenido: se copia a la carpeta del trabajo, el agente
edita `draw()` y `diagram_render` lo ejecuta. La imagen se publica junto al AVIF
en `source/` del repositorio BlogImages, así que debe poder ejecutarse solo con
Pillow:

    python3 source.py            # escribe out.png
    DIAGRAM_OUT=versions/v1.png python3 source.py

Ubicación recomendada: "Abajo del texto «un modelo de 4B parámetros necesita unos 8 GB solo para sus pesos, sin contar el contexto ni el sistema»"
Contenido recomendado: "Compara cuánta memoria ocupan solo los pesos de un modelo según los parámetros y los bytes por parámetro, y deja ver por qué cargar un modelo grande en 16 bits es inviable.\n\nComponentes: dos grupos de barras horizontales comparables, uno «4B parámetros» y otro «671B parámetros (DeepSeek-V3)»; en cada grupo tres barras por formato (FP16, FP8, INT4/FP4) con su tamaño; un eje horizontal de gigabytes en escala logarítmica; una tarjeta vacía «+ contexto + sistema» que recuerda lo que no se cuenta; una etiqueta de llamada «cuantizar = menos bits por número».\nEstilo: estilo oscuro de la casa, fondo #0B0F19 y tarjetas #0F172A; FP16 en cian #22D3EE, FP8 en ámbar #F59E0B, INT4/FP4 en verde #34D399; DejaVu Sans, título 52 px y etiquetas 24 px; barras con radio 8 px, rejilla tenue #1E293B y sin sombras.\nPosicionamiento: título y subtítulo arriba; grupo «4B» arriba y grupo «671B» abajo, ambos alineados al mismo eje horizontal de gigabytes a la izquierda; la tarjeta «+ contexto + sistema» a la derecha del grupo grande, en gris tenue #64748B; leyenda de colores al pie.\nTextos en la imagen: título «El presupuesto de memoria de un modelo»; subtítulo «solo los pesos, en precisión de 16 bits»; etiquetas «4B parámetros», «671B parámetros (DeepSeek-V3)», «FP16 · 8 GB», «FP8 · 4 GB», «INT4 · 2 GB», «FP16 ≈ 1,3 TB», «FP8 ≈ 0,67 TB», «INT4 ≈ 0,34 TB»; recuadro «+ contexto + sistema (no incluidos)»; nota al pie «FP8 e INT4 se derivan de la aritmética de la sección: 1 y 0,5 bytes por parámetro»."

Estilo: paleta del tema oscuro del blog (PyramidSpace). Fondo #090B0D, tarjetas
#111519, bordes #1F2123, texto #F8FAFC, secundario #94A3B8, acento teal #2DD4BF,
ámbar #F59E0B y verde #4ADE80. Sans neutra (Liberation Sans, DejaVu de respaldo),
texto grande para la columna de lectura de 720 px. Lienzo 1800 x 1200.
"""

from __future__ import annotations

import math
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# 1. Paleta y tipografía del tema oscuro del blog
# ---------------------------------------------------------------------------
BG = "#090B0D"          # --bg del tema oscuro
CARD = "#111519"        # --surface
CARD_RAISED = "#171C21" # --surface-2
BORDER = "#1F2123"      # --border (blanco 9 %) compuesto sobre --bg
BORDER_SOFT = "#262A2E" # --border compuesto sobre --surface
BORDER_STRONG = "#3F4142"
TEXT = "#F8FAFC"        # --text
MUTED = "#94A3B8"       # --muted
FAINT = "#64748B"
TEAL = "#2DD4BF"        # --accent
AMBER = "#F59E0B"       # --accent-2
GREEN = "#4ADE80"       # --success
RED = "#F87171"         # --danger
ON_TEAL = "#06201C"     # texto sobre relleno teal

# Alias del esqueleto de la casa, conservados por compatibilidad.
CYAN = TEAL
CYAN_SOFT = "#5EEAD4"
AMBER_SOFT = "#D97706"
LINE = BORDER

W, H = 1800, 1200
MARGIN = 90

FONT_CANDIDATES = {
    False: (
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ),
    True: (
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ),
}

# Metadatos rellenados por el estudio; se conservan para trazabilidad.
TITLE = "Presupuesto de memoria de un LLM"
LOCATION = "Abajo del texto «un modelo de 4B parámetros necesita unos 8 GB solo para sus pesos, sin contar el contexto ni el sistema»"
CONTENT = "Compara cuánta memoria ocupan solo los pesos de un modelo según los parámetros y los bytes por parámetro, y deja ver por qué cargar un modelo grande en 16 bits es inviable.\n\nComponentes: dos grupos de barras horizontales comparables, uno «4B parámetros» y otro «671B parámetros (DeepSeek-V3)»; en cada grupo tres barras por formato (FP16, FP8, INT4/FP4) con su tamaño; un eje horizontal de gigabytes en escala logarítmica; una tarjeta vacía «+ contexto + sistema» que recuerda lo que no se cuenta; una etiqueta de llamada «cuantizar = menos bits por número».\nEstilo: paleta del tema oscuro del blog; FP16 en teal #2DD4BF, FP8 en ámbar #F59E0B, INT4/FP4 en verde #4ADE80; sans neutra, título 58 px y etiquetas de 22 px o más; barras con radio 10 px y rejilla tenue, sin sombras.\nPosicionamiento: título y subtítulo arriba; grupo «4B» arriba y grupo «671B» abajo, ambos alineados al mismo eje horizontal de gigabytes a la izquierda; la tarjeta «+ contexto + sistema» al pie a la derecha, en gris tenue; leyenda de colores bajo la cabecera.\nTextos en la imagen: título «El presupuesto de memoria de un modelo»; subtítulo «Los pesos del modelo, sin contar el contexto ni el sistema»; etiquetas «4B parámetros», «671B parámetros · DeepSeek-V3», «FP16», «FP8», «INT4/FP4», «8 GB», «4 GB», «2 GB», «≈ 1,3 TB», «≈ 0,67 TB», «≈ 0,34 TB»; llamada «cuantizar = menos bits por número»; recuadro «+ contexto + sistema / no incluidos en estas cifras»; notas al pie sobre escala logarítmica y bytes por parámetro."
SOURCE = "diagram-studio"


def rgb(value: str) -> tuple[int, int, int]:
    """Convierte `#RRGGBB` en una tupla RGB."""
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


_FONT_CACHE: dict[tuple[int, bool], ImageFont.FreeTypeFont] = {}


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Carga Liberation Sans (o DejaVu como respaldo) con caché."""
    key = (size, bold)
    if key not in _FONT_CACHE:
        face = None
        for path in FONT_CANDIDATES[bold]:
            try:
                face = ImageFont.truetype(path, size)
                break
            except OSError:
                continue
        _FONT_CACHE[key] = face or ImageFont.load_default()
    return _FONT_CACHE[key]


def mix(c1: str, c2: str, t: float) -> tuple[int, int, int]:
    """Interpola dos colores hex; `t=0` devuelve `c1`."""
    t = max(0.0, min(1.0, t))
    a, b = rgb(c1), rgb(c2)
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


# ---------------------------------------------------------------------------
# 2. Lienzo y formas
# ---------------------------------------------------------------------------
def new_canvas(width: int = W, height: int = H) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    """Crea el lienzo oscuro con su `ImageDraw`."""
    image = Image.new("RGB", (width, height), rgb(BG))
    return image, ImageDraw.Draw(image)


def rounded_box(draw: ImageDraw.ImageDraw, xy, radius: int = 24, fill: str = CARD,
                outline: str = BORDER, width: int = 2) -> None:
    """Dibuja una tarjeta redondeada."""
    draw.rounded_rectangle(xy, radius=radius, fill=rgb(fill), outline=rgb(outline), width=width)


def _round_rect_points(x0, y0, x1, y1, radius: int, step: float = 3.0):
    """Muestrea el perímetro de un rectángulo redondeado, en orden."""
    r = radius
    points: list[tuple[float, float]] = []

    def add_line(a, b):
        length = math.hypot(b[0] - a[0], b[1] - a[1])
        count = max(1, int(length / step))
        for i in range(count + 1):
            t = i / count
            points.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))

    def add_arc(cx, cy, start, end):
        count = max(8, int(abs(end - start) * r / 180 / step) + 2)
        for i in range(count + 1):
            angle = math.radians(start + (end - start) * i / count)
            points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))

    add_line((x0 + r, y0), (x1 - r, y0))
    add_arc(x1 - r, y0 + r, -90, 0)
    add_line((x1, y0 + r), (x1, y1 - r))
    add_arc(x1 - r, y1 - r, 0, 90)
    add_line((x1 - r, y1), (x0 + r, y1))
    add_arc(x0 + r, y1 - r, 90, 180)
    add_line((x0, y1 - r), (x0, y0 + r))
    add_arc(x0 + r, y0 + r, 180, 270)
    return points


def dashed_box(draw: ImageDraw.ImageDraw, xy, radius: int = 20,
               outline: str = BORDER_STRONG, width: int = 2,
               dash: int = 16, gap: int = 12) -> None:
    """Rectángulo redondeado con contorno discontinuo (para el recuadro vacío)."""
    x0, y0, x1, y1 = xy
    points = _round_rect_points(x0, y0, x1, y1, radius)
    cumulative = [0.0]
    for index in range(1, len(points)):
        cumulative.append(cumulative[-1] + math.hypot(
            points[index][0] - points[index - 1][0],
            points[index][1] - points[index - 1][1],
        ))
    total = cumulative[-1]
    period = dash + gap

    start = 0.0
    while start < total:
        end = min(start + dash, total)
        index = 0
        while index < len(points) - 1 and cumulative[index + 1] <= start:
            index += 1
        position = start
        while position < end - 0.01 and index < len(points) - 1:
            segment = cumulative[index + 1] - cumulative[index]
            if segment <= 0:
                index += 1
                continue
            stop = min(end, cumulative[index + 1])
            t0 = (position - cumulative[index]) / segment
            t1 = (stop - cumulative[index]) / segment
            draw.line(
                (points[index][0] + (points[index + 1][0] - points[index][0]) * t0,
                 points[index][1] + (points[index + 1][1] - points[index][1]) * t0,
                 points[index][0] + (points[index + 1][0] - points[index][0]) * t1,
                 points[index][1] + (points[index + 1][1] - points[index][1]) * t1),
                fill=rgb(outline), width=width,
            )
            position = stop
            index += 1
        start += period


def draw_text_block(draw: ImageDraw.ImageDraw, x: int, y: int, text: str,
                    face, color: str, max_width: int, spacing: int = 8) -> int:
    """Dibuja texto con ajuste de línea y devuelve la Y final."""
    for paragraph in text.split("\n"):
        words = paragraph.split()
        line = ""
        for word in words:
            candidate = f"{line} {word}".strip()
            if draw.textlength(candidate, font=face) <= max_width or not line:
                line = candidate
            else:
                draw.text((x, y), line, font=face, fill=rgb(color))
                y += face.size + spacing
                line = word
        if line:
            draw.text((x, y), line, font=face, fill=rgb(color))
            y += face.size + spacing
    return y


def arrow(draw: ImageDraw.ImageDraw, start: tuple[float, float], end: tuple[float, float],
          color: str = AMBER, width: int = 4, head: int = 18) -> None:
    """Flecha recta con cabeza triangular."""
    draw.line((start, end), fill=rgb(color), width=width)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    left = (end[0] - head * math.cos(angle - math.pi / 7), end[1] - head * math.sin(angle - math.pi / 7))
    right = (end[0] - head * math.cos(angle + math.pi / 7), end[1] - head * math.sin(angle + math.pi / 7))
    draw.polygon([end, left, right], fill=rgb(color))


def badge(draw: ImageDraw.ImageDraw, x: int, y: int, text: str, fill: str = TEAL,
          text_color: str = ON_TEAL, size: int = 22) -> int:
    """Etiqueta compacta de una línea; devuelve su ancho."""
    face = font(size, bold=True)
    width = draw.textlength(text, font=face) + 36
    draw.rounded_rectangle((x, y, x + width, y + size + 16), radius=(size + 16) // 2,
                           fill=rgb(fill))
    draw.text((x + 18, y + (size + 16) / 2), text, font=face, fill=rgb(text_color), anchor="lm")
    return int(width)


# ---------------------------------------------------------------------------
# 3. Geometría del gráfico
# ---------------------------------------------------------------------------
AXIS_X0 = 310               # 1 GB
AXIS_X1 = 1620              # 3000 GB
AXIS_MIN_GB = 1
AXIS_MAX_GB = 3000
CARD_X0, CARD_X1 = 90, 1710
CARD_Y0, CARD_Y1 = 296, 1000
GRID_BOTTOM = 938

TICKS = ((1, "1 GB"), (10, "10 GB"), (100, "100 GB"), (1000, "1 TB"))

GROUPS = (
    {
        "label": "4B parámetros",
        "y": 368,
        "bars": (
            ("FP16", 8, "8 GB", TEAL),
            ("FP8", 4, "4 GB", AMBER),
            ("INT4/FP4", 2, "2 GB", GREEN),
        ),
    },
    {
        "label": "671B parámetros · DeepSeek-V3",
        "y": 690,
        "bars": (
            ("FP16", 1342, "≈ 1,3 TB", TEAL),
            ("FP8", 671, "≈ 0,67 TB", AMBER),
            ("INT4/FP4", 335.5, "≈ 0,34 TB", GREEN),
        ),
    },
)


def gb_to_x(value_gb: float) -> float:
    """Proyecta un tamaño en GB sobre el eje logarítmico."""
    lo, hi = math.log10(AXIS_MIN_GB), math.log10(AXIS_MAX_GB)
    return AXIS_X0 + (math.log10(value_gb) - lo) / (hi - lo) * (AXIS_X1 - AXIS_X0)


# ---------------------------------------------------------------------------
# 4. Composición del diagrama
# ---------------------------------------------------------------------------
def draw() -> Image.Image:
    """Compón el diagrama. Devuelve la imagen final."""
    image, canvas = new_canvas()

    # Cabecera
    canvas.text((MARGIN, 54), "El presupuesto de memoria de un modelo",
                font=font(58, bold=True), fill=rgb(TEXT))
    canvas.text((MARGIN, 136), "Los pesos del modelo, sin contar el contexto ni el sistema",
                font=font(30), fill=rgb(MUTED))
    deck = (
        ("Con los mismos bytes por parámetro, 671B necesita ", MUTED, False),
        ("≈168×", TEAL, True),
        (" la memoria de 4B.", MUTED, False),
    )
    dx = MARGIN
    for text, color, bold in deck:
        face = font(24, bold=bold)
        canvas.text((dx, 178), text, font=face, fill=rgb(color))
        dx += canvas.textlength(text, font=face)
    canvas.line((MARGIN, 222, W - MARGIN, 222), fill=rgb(BORDER), width=2)

    # Leyenda de formatos
    legend = (("FP16 · 2 B", TEAL), ("FP8 · 1 B", AMBER), ("INT4/FP4 · 0,5 B", GREEN))
    legend_face = font(24)
    lx = MARGIN
    for label, color in legend:
        canvas.rounded_rectangle((lx, 244, lx + 26, 270), radius=7, fill=rgb(color))
        canvas.text((lx + 38, 257), label, font=legend_face, fill=rgb(MUTED), anchor="lm")
        lx += 38 + canvas.textlength(label, font=legend_face) + 48

    # Llamada
    badge(canvas, W - MARGIN - (canvas.textlength("cuantizar = menos bits por número",
                                                   font=font(22, bold=True)) + 36), 238,
          "cuantizar = menos bits por número")

    # Tarjeta del gráfico
    rounded_box(canvas, (CARD_X0, CARD_Y0, CARD_X1, CARD_Y1), radius=28, fill=CARD,
                outline=BORDER, width=2)

    # Rejilla vertical
    for value, _ in TICKS:
        gx = gb_to_x(value)
        canvas.line((gx, CARD_Y0 + 40, gx, GRID_BOTTOM), fill=rgb(BORDER_SOFT), width=2)

    # Grupos y barras
    for group in GROUPS:
        canvas.text((CARD_X0 + 20, group["y"] - 46), group["label"],
                    font=font(30, bold=True), fill=rgb(TEXT))
        for index, (fmt, gb, value_label, color) in enumerate(group["bars"]):
            top = group["y"] + index * 86
            end = gb_to_x(gb)
            canvas.rounded_rectangle((AXIS_X0, top, end, top + 64), radius=10, fill=rgb(color))
            canvas.text((AXIS_X0 - 22, top + 32), fmt, font=font(24), fill=rgb(MUTED), anchor="rm")
            canvas.text((end + 18, top + 32), value_label, font=font(28, bold=True),
                        fill=rgb(TEXT), anchor="lm")

    # Eje y etiquetas
    for value, label in TICKS:
        canvas.text((gb_to_x(value), 952), label, font=font(24), fill=rgb(MUTED), anchor="ma")

    # Notas al pie
    canvas.text((MARGIN, 1016), "Escala logarítmica · las barras arrancan en 1 GB.",
                font=font(22), fill=rgb(MUTED))
    canvas.text((MARGIN, 1058),
                "Tamaño ≈ parámetros × bytes por parámetro: FP8 e INT4/FP4 usan 1 y 0,5 bytes.",
                font=font(22), fill=rgb(MUTED))

    # Recuadro de lo que no se cuenta
    dashed_box(canvas, (1120, 1012, 1710, 1100), radius=20, outline=BORDER_STRONG, width=2)
    canvas.text((1150, 1026), "+ contexto + sistema", font=font(26, bold=True), fill=rgb(MUTED))
    canvas.text((1150, 1064), "no incluidos en estas cifras", font=font(22), fill=rgb(MUTED))

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

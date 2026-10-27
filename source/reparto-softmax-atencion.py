""""Reparto softmax de la atención"

Diagrama propuesto por el estudio de diagramas a partir de una recomendación del
blog. Este archivo es autocontenido: se copia a la carpeta del trabajo, el agente
edita `draw()` y `diagram_render` lo ejecuta. La imagen se publica junto al AVIF
en `source/` del repositorio BlogImages, así que debe poder ejecutarse solo con
Pillow:

    python3 source.py            # escribe out.png
    DIAGRAM_OUT=versions/v1.png python3 source.py

Ubicación recomendada: "Abajo del texto «Softmax es la función que toma los puntajes brutos de similitud y los convierte en una distribución de probabilidad que suma exactamente 100%»."
Contenido recomendado: "Visualiza el paso de puntajes brutos a porcentajes de atención con los cuatro valores del ejemplo y el vector mezclado resultante.\nComponentes: cuatro barras de puntaje bruto («depósito 8.5», «dinero 7.2», «el 1.3», «parque 0.8»); tarjeta central «Softmax»; cuatro barras de porcentaje («45%», «38%», «9%», «8%»); una tarjeta de verificación «Σ = 100%»; tarjeta de salida «Nuevo vector de banco: contexto financiero».\nEstilo: estilo oscuro de la casa; fondo #0B0F19, tarjetas #0F172A; barras brutas en gris #64748B, barras porcentuales en cian #22D3EE y cian suave #38BDF8; la tarjeta Softmax en ámbar #F59E0B; la verificación Σ en verde #34D399; DejaVu Sans, título 50 px, cuerpo 24 px; barras de 60 px de ancho con etiqueta numérica al final.\nPosicionamiento: columna izquierda con las cuatro barras brutas, tarjeta «Softmax» en el centro con una flecha ancha de entrada, columna derecha con las cuatro barras porcentuales; debajo de la columna derecha, la tarjeta «Σ = 100%» y, más abajo, la tarjeta del nuevo vector ocupando el ancho completo; cada barra porcentual alineada con su barra bruta de origen.\nTextos en la imagen: título «Softmax: el reparto de la atención»; subtítulo «De puntajes brutos a porcentajes que suman 100%»; etiquetas «Puntajes de similitud», «depósito 8.5», «dinero 7.2», «el 1.3», «parque 0.8», «Softmax», «Atención», «45%», «38%», «9%», «8%», «Σ = 100%», «Nuevo vector de banco: contexto financiero»."

Estilo de la casa: fondo #0B0F19, tarjetas #0F172A, texto #E2E8F0, acentos cian
#22D3EE y ámbar #F59E0B, DejaVu Sans. Lienzo 1800 x 1200.
"""

from __future__ import annotations

import math
import os
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# 1. Paleta y tipografía
# ---------------------------------------------------------------------------
BG = "#0B0F19"
BG_SOFT = "#0F172A"
CARD = "#0F172A"
CARD_RAISED = "#141E33"
LINE = "#1E293B"
TEXT = "#E2E8F0"
MUTED = "#94A3B8"
FAINT = "#64748B"
CYAN = "#22D3EE"
CYAN_SOFT = "#38BDF8"
AMBER = "#F59E0B"
AMBER_SOFT = "#D97706"
GREEN = "#34D399"
RED = "#F87171"

W, H = 1800, 1200
MARGIN = 90

FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
FONT_REGULAR = FONT_DIR / "DejaVuSans.ttf"
FONT_BOLD = FONT_DIR / "DejaVuSans-Bold.ttf"

# Metadatos rellenados por el estudio; se conservan para trazabilidad.
TITLE = "Reparto softmax de la atención"
LOCATION = "Abajo del texto «Softmax es la función que toma los puntajes brutos de similitud y los convierte en una distribución de probabilidad que suma exactamente 100%»."
CONTENT = "Visualiza el paso de puntajes brutos a porcentajes de atención con los cuatro valores del ejemplo y el vector mezclado resultante.\nComponentes: cuatro barras de puntaje bruto («depósito 8.5», «dinero 7.2», «el 1.3», «parque 0.8»); tarjeta central «Softmax»; cuatro barras de porcentaje («45%», «38%», «9%», «8%»); una tarjeta de verificación «Σ = 100%»; tarjeta de salida «Nuevo vector de banco: contexto financiero».\nEstilo: estilo oscuro de la casa; fondo #0B0F19, tarjetas #0F172A; barras brutas en gris #64748B, barras porcentuales en cian #22D3EE y cian suave #38BDF8; la tarjeta Softmax en ámbar #F59E0B; la verificación Σ en verde #34D399; DejaVu Sans, título 50 px, cuerpo 24 px; barras de 60 px de ancho con etiqueta numérica al final.\nPosicionamiento: columna izquierda con las cuatro barras brutas, tarjeta «Softmax» en el centro con una flecha ancha de entrada, columna derecha con las cuatro barras porcentuales; debajo de la columna derecha, la tarjeta «Σ = 100%» y, más abajo, la tarjeta del nuevo vector ocupando el ancho completo; cada barra porcentual alineada con su barra bruta de origen.\nTextos en la imagen: título «Softmax: el reparto de la atención»; subtítulo «De puntajes brutos a porcentajes que suman 100%»; etiquetas «Puntajes de similitud», «depósito 8.5», «dinero 7.2», «el 1.3», «parque 0.8», «Softmax», «Atención», «45%», «38%», «9%», «8%», «Σ = 100%», «Nuevo vector de banco: contexto financiero»."
SOURCE = "diagram-studio"


def rgb(value: str) -> tuple[int, int, int]:
    """Convierte `#RRGGBB` en una tupla RGB."""
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Carga DejaVu (o la fuente por defecto si no está disponible)."""
    path = FONT_BOLD if bold else FONT_REGULAR
    try:
        return ImageFont.truetype(str(path), size)
    except OSError:
        return ImageFont.load_default()


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
                outline: str = LINE, width: int = 2) -> None:
    """Dibuja una tarjeta redondeada."""
    draw.rounded_rectangle(xy, radius=radius, fill=rgb(fill), outline=rgb(outline), width=width)


def card(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int,
         title: str, lines: list[str] | None = None, accent: str = CYAN,
         title_size: int = 34, body_size: int = 24) -> None:
    """Tarjeta con una barra de acento, título y cuerpo con wrap."""
    rounded_box(draw, (x, y, x + w, y + h), fill=CARD, outline=LINE)
    draw.rounded_rectangle((x, y, x + 8, y + h), radius=4, fill=rgb(accent))
    draw.text((x + 32, y + 24), title, font=font(title_size, bold=True), fill=rgb(TEXT))
    body = lines or []
    if body:
        draw_text_block(draw, x + 32, y + 24 + title_size + 18, "\n".join(body),
                        font(body_size), MUTED, max_width=w - 64)


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


def badge(draw: ImageDraw.ImageDraw, x: int, y: int, text: str, fill: str = CYAN,
          text_color: str = BG, size: int = 22) -> None:
    """Etiqueta compacta de una línea."""
    face = font(size, bold=True)
    w = draw.textlength(text, font=face)
    draw.rounded_rectangle((x, y, x + w + 28, y + size + 16), radius=(size + 16) // 2, fill=rgb(fill))
    draw.text((x + 14, y + 7), text, font=face, fill=rgb(text_color))


def wrap(value: str, width: int = 110) -> str:
    """Envuelve el texto de la recomendación para el pie."""
    return "\n".join(textwrap.wrap(value, width=width)) or value


# ---------------------------------------------------------------------------
# 3. Composición del diagrama (edita esta función)
# ---------------------------------------------------------------------------
def text_center(draw: ImageDraw.ImageDraw, cx: float, y: float, text: str,
                face, color: str) -> None:
    """Texto centrado horizontalmente en `cx`."""
    width = draw.textlength(text, font=face)
    draw.text((cx - width / 2, y), text, font=face, fill=rgb(color))


def draw() -> Image.Image:
    """Compón el diagrama. Devuelve la imagen final."""
    image, canvas = new_canvas()

    # ---------------------------------------------------------------- cabecera
    canvas.text((MARGIN, 54), "Softmax: el reparto de la atención",
                font=font(50, bold=True), fill=rgb(TEXT))
    canvas.text((MARGIN, 124), "De puntajes brutos a porcentajes que suman 100%",
                font=font(24), fill=rgb(MUTED))
    canvas.line((MARGIN, 176, W - MARGIN, 176), fill=rgb(LINE), width=2)

    rows = [262, 372, 482, 592]
    centers = [top + 45 for top in rows]  # 307, 417, 527, 637

    canvas.text((150, 208), "Puntajes de similitud", font=font(20, bold=True), fill=rgb(MUTED))
    canvas.text((1120, 208), "Atención", font=font(20, bold=True), fill=rgb(CYAN))

    # ------------------------------------------------------- puntajes brutos
    raw = [("depósito", 8.5, 250), ("dinero", 7.2, 212),
           ("el", 1.3, 38), ("parque", 0.8, 24)]
    for index, (word, value, width) in enumerate(raw):
        cy = centers[index]
        canvas.text((150, cy - 16), word, font=font(22), fill=rgb(TEXT))
        canvas.rounded_rectangle((340, cy - 28, 340 + width, cy + 28), radius=12,
                                 fill=rgb(FAINT))
        canvas.text((340 + width + 16, cy - 15), f"{value}", font=font(22), fill=rgb(MUTED))

    # ---------------------------------------------------------------- softmax
    rounded_box(canvas, (720, 360, 1060, 588), radius=22, fill=CARD, outline=LINE)
    canvas.rounded_rectangle((720, 360, 728, 588), radius=4, fill=rgb(AMBER))
    canvas.text((752, 386), "Softmax", font=font(34, bold=True), fill=rgb(AMBER))
    canvas.line((752, 436, 1028, 436), fill=rgb(LINE), width=2)
    draw_text_block(canvas, 752, 452,
                    "puntajes → probabilidades", font(20), MUTED, max_width=286)
    draw_text_block(canvas, 752, 502,
                    "distribución que suma 100%", font(19), FAINT, max_width=286)

    arrow(canvas, (676, 471), (714, 471), color=AMBER, width=12, head=26)
    arrow(canvas, (1066, 471), (1114, 471), color=AMBER, width=12, head=26)

    # ------------------------------------------------------------ porcentajes
    pct = [("45%", 250, CYAN), ("38%", 211, CYAN_SOFT),
           ("9%", 50, mix(CYAN, BG, 0.28)), ("8%", 44, mix(CYAN, BG, 0.36))]
    for index, (label, width, color) in enumerate(pct):
        cy = centers[index]
        canvas.rounded_rectangle((1120, cy - 28, 1120 + width, cy + 28), radius=12, fill=color)
        canvas.text((1120 + width + 16, cy - 16), label, font=font(24, bold=True),
                    fill=rgb(TEXT))

    # ---------------------------------------------------------------- suma 100%
    rounded_box(canvas, (1120, 700, 1650, 836), radius=22, fill=CARD, outline=LINE)
    canvas.rounded_rectangle((1120, 700, 1128, 836), radius=4, fill=rgb(GREEN))
    canvas.text((1152, 722), "Σ = 100%", font=font(38, bold=True), fill=rgb(GREEN))
    draw_text_block(canvas, 1152, 782, "la atención se reparte entera",
                    font(20), MUTED, max_width=440)

    # ------------------------------------------------------------- nota izquierda
    draw_text_block(canvas, 150, 700,
                    "Cada porcentaje indica cuánto pesa el valor de esa palabra "
                    "en la mezcla final de «banco».",
                    font(21), MUTED, max_width=720)

    # ------------------------------------------------------------ nuevo vector
    rounded_box(canvas, (150, 890, 1650, 1080), radius=22, fill=CARD, outline=LINE)
    canvas.rounded_rectangle((150, 890, 158, 1080), radius=4, fill=rgb(CYAN_SOFT))
    canvas.text((188, 914), "Nuevo vector de banco: contexto financiero",
                font=font(30, bold=True), fill=rgb(TEXT))
    canvas.text((188, 966), "mezcla ponderada de los valores según esos porcentajes",
                font=font(20), fill=rgb(MUTED))
    bars = [22, 34, 16, 28, 40, 24, 30, 20]
    for bar_index, height in enumerate(bars):
        bx = 1180 + bar_index * 52
        canvas.rounded_rectangle((bx, 1046 - height, bx + 34, 1046), radius=8,
                                 fill=mix(CYAN_SOFT, BG, 0.08 + (bar_index % 3) * 0.12))

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

""""Escalamiento de la atención √d_k"

Diagrama propuesto por el estudio de diagramas a partir de una recomendación del
blog. Este archivo es autocontenido: se copia a la carpeta del trabajo, el agente
edita `draw()` y `diagram_render` lo ejecuta. La imagen se publica junto al AVIF
en `source/` del repositorio BlogImages, así que debe poder ejecutarse solo con
Pillow:

    python3 source.py            # escribe out.png
    DIAGRAM_OUT=versions/v1.png python3 source.py

Ubicación recomendada: "Abajo del texto «Para evitar esto, se dividen los puntajes de similitud por la raíz cuadrada de la dimensión de las Llaves (√d_k)»."
Contenido recomendado: "Compara el efecto de no escalar los puntajes (softmax saturado y plano) con escalarlos por √d_k (softmax con diferencias claras), usando el símil del control de volumen.\nComponentes: tarjeta izquierda «Sin escalar» con cuatro barras casi iguales y aviso «saturado»; tarjeta central «Control de volumen: ÷ √d_k» con un dial; tarjeta derecha «Con escalamiento» con barras bien diferenciadas y aviso «discrimina»; tarjeta inferior con la fórmula «softmax(Q·Kᵀ / √d_k)»; tarjeta de ejemplo «d_k = 512 → ÷ 22.6».\nEstilo: estilo oscuro de la casa; fondo #0B0F19, tarjetas #0F172A; el panel «Sin escalar» con acento rojo #F87171 y barras grises #64748B; el panel «Con escalamiento» con acento verde #34D399 y barras cian #22D3EE; el dial en ámbar #F59E0B; DejaVu Sans, título 50 px, cuerpo 23 px; línea divisoria bajo el subtítulo.\nPosicionamiento: dos paneles comparados de izquierda a derecha con el control de volumen justo en el medio como bisagra; la fórmula en una tarjeta ancha debajo de los paneles; el ejemplo de d_k debajo de la fórmula; título y subtítulo arriba, centrados.\nTextos en la imagen: título «Escalar la atención: el control de volumen»; subtítulo «Sin escala, softmax se satura y no distingue»; etiquetas «Sin escalar», «Todos los porcentajes colapsan», «Control de volumen», «÷ √d_k», «Con escalamiento», «Softmax en zona sensible», «softmax(Q·Kᵀ / √d_k)», «d_k = 512 → ÷ 22.6»."

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
TITLE = "Escalamiento de la atención √d_k"
LOCATION = "Abajo del texto «Para evitar esto, se dividen los puntajes de similitud por la raíz cuadrada de la dimensión de las Llaves (√d_k)»."
CONTENT = "Compara el efecto de no escalar los puntajes (softmax saturado y plano) con escalarlos por √d_k (softmax con diferencias claras), usando el símil del control de volumen.\nComponentes: tarjeta izquierda «Sin escalar» con cuatro barras casi iguales y aviso «saturado»; tarjeta central «Control de volumen: ÷ √d_k» con un dial; tarjeta derecha «Con escalamiento» con barras bien diferenciadas y aviso «discrimina»; tarjeta inferior con la fórmula «softmax(Q·Kᵀ / √d_k)»; tarjeta de ejemplo «d_k = 512 → ÷ 22.6».\nEstilo: estilo oscuro de la casa; fondo #0B0F19, tarjetas #0F172A; el panel «Sin escalar» con acento rojo #F87171 y barras grises #64748B; el panel «Con escalamiento» con acento verde #34D399 y barras cian #22D3EE; el dial en ámbar #F59E0B; DejaVu Sans, título 50 px, cuerpo 23 px; línea divisoria bajo el subtítulo.\nPosicionamiento: dos paneles comparados de izquierda a derecha con el control de volumen justo en el medio como bisagra; la fórmula en una tarjeta ancha debajo de los paneles; el ejemplo de d_k debajo de la fórmula; título y subtítulo arriba, centrados.\nTextos en la imagen: título «Escalar la atención: el control de volumen»; subtítulo «Sin escala, softmax se satura y no distingue»; etiquetas «Sin escalar», «Todos los porcentajes colapsan», «Control de volumen», «÷ √d_k», «Con escalamiento», «Softmax en zona sensible», «softmax(Q·Kᵀ / √d_k)», «d_k = 512 → ÷ 22.6»."
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
    text_center(canvas, 900, 54, "Escalar la atención: el control de volumen",
                font(50, bold=True), TEXT)
    text_center(canvas, 900, 124, "Sin escala, softmax se satura y no distingue",
                font(24), MUTED)
    canvas.line((MARGIN, 176, W - MARGIN, 176), fill=rgb(LINE), width=2)

    baseline = 680
    bar_w = 86

    # --------------------------------------------------------- panel sin escalar
    rounded_box(canvas, (90, 240, 760, 780), radius=24, fill=CARD, outline=LINE)
    canvas.rounded_rectangle((90, 240, 98, 780), radius=4, fill=rgb(RED))
    canvas.text((120, 266), "Sin escalar", font=font(34, bold=True), fill=rgb(TEXT))
    badge(canvas, 120, 316, "saturado", fill=RED, text_color=BG, size=19)
    canvas.line((120, baseline, 730, baseline), fill=rgb(LINE), width=2)
    for index, height in enumerate([248, 240, 254, 244]):
        x = 160 + index * 148
        canvas.rounded_rectangle((x, baseline - height, x + bar_w, baseline), radius=10,
                                 fill=rgb(FAINT))
    canvas.text((120, 706), "Todos los porcentajes colapsan", font=font(21), fill=rgb(MUTED))

    # ---------------------------------------------------- panel con escalamiento
    rounded_box(canvas, (1040, 240, 1710, 780), radius=24, fill=CARD, outline=LINE)
    canvas.rounded_rectangle((1040, 240, 1048, 780), radius=4, fill=rgb(GREEN))
    canvas.text((1070, 266), "Con escalamiento", font=font(34, bold=True), fill=rgb(TEXT))
    badge(canvas, 1070, 316, "discrimina", fill=GREEN, text_color=BG, size=19)
    canvas.line((1070, baseline, 1680, baseline), fill=rgb(LINE), width=2)
    colors = [CYAN, CYAN_SOFT, mix(CYAN, BG, 0.35), mix(CYAN, BG, 0.45)]
    for index, height in enumerate([285, 225, 100, 74]):
        x = 1110 + index * 148
        canvas.rounded_rectangle((x, baseline - height, x + bar_w, baseline), radius=10,
                                 fill=colors[index] if isinstance(colors[index], tuple) else rgb(colors[index]))
    canvas.text((1070, 706), "Softmax en zona sensible", font=font(21), fill=rgb(MUTED))

    # ------------------------------------------------------ control de volumen
    rounded_box(canvas, (780, 330, 1030, 690), radius=22, fill=CARD, outline=LINE)
    text_center(canvas, 905, 352, "Control de volumen", font(18, bold=True), AMBER)
    canvas.ellipse((835, 440, 975, 580), fill=rgb(CARD_RAISED), outline=rgb(LINE), width=2)
    canvas.arc((845, 450, 965, 570), start=140, end=400, fill=rgb(AMBER), width=6)
    for angle in (150, 210, 270, 330, 30):
        rad = math.radians(angle)
        inner = (905 + 54 * math.cos(rad), 510 + 54 * math.sin(rad))
        outer = (905 + 66 * math.cos(rad), 510 + 66 * math.sin(rad))
        canvas.line((inner, outer), fill=rgb(MUTED), width=3)
    needle = math.radians(315)
    canvas.line((905, 510, 905 + 58 * math.cos(needle), 510 + 58 * math.sin(needle)),
                fill=rgb(AMBER), width=6)
    canvas.ellipse((893, 498, 917, 522), fill=rgb(AMBER))
    text_center(canvas, 905, 600, "÷ √d_k", font(30, bold=True), AMBER)

    # ---------------------------------------------------------------- fórmula
    rounded_box(canvas, (300, 820, 1500, 940), radius=22, fill=CARD, outline=LINE)
    canvas.rounded_rectangle((300, 820, 308, 940), radius=4, fill=rgb(CYAN_SOFT))
    text_center(canvas, 900, 848, "softmax(Q·Kᵀ / √d_k)", font(36, bold=True), TEXT)
    text_center(canvas, 900, 902, "la división ocurre antes del softmax", font(19), MUTED)

    # ---------------------------------------------------------------- ejemplo
    rounded_box(canvas, (600, 970, 1200, 1080), radius=22, fill=CARD, outline=LINE)
    text_center(canvas, 900, 992, "d_k = 512 → ÷ 22.6", font(28, bold=True), CYAN_SOFT)
    text_center(canvas, 900, 1036, "raíz cuadrada de la dimensión de las llaves", font(18), MUTED)

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

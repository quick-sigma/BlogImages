""""Arquitectura encoder-decoder"

Diagrama propuesto por el estudio de diagramas a partir de una recomendación del
blog. Este archivo es autocontenido: se copia a la carpeta del trabajo, el agente
edita `draw()` y `diagram_render` lo ejecuta. La imagen se publica junto al AVIF
en `source/` del repositorio BlogImages, así que debe poder ejecutarse solo con
Pillow:

    python3 source.py            # escribe out.png
    DIAGRAM_OUT=versions/v1.png python3 source.py

Ubicación recomendada: "Abajo del texto «Los Transformers originales tienen una arquitectura que en Deep Learning conocemos como Codificador-Decodificador (Encoder-Decoder)»."
Contenido recomendado: "Vista general del Transformer original: el codificador comprende toda la oración una sola vez y el decodificador genera palabra por palabra apoyándose en esa comprensión y en la máscara causal.\nComponentes: tarjeta «Codificador (El Lector)» con tres subcapas apiladas («Auto-atención», «Feed Forward», «Conexión residual»); tarjeta «Decodificador (El Escritor)» con cuatro subcapas («Auto-atención enmascarada», «Atención cruzada», «Feed Forward», «Conexión residual»); flecha horizontal «Mapa de comprensión» del codificador al decodificador; tarjeta de salida «Predicción de la siguiente palabra»; etiqueta de iteración «× N palabras» bajo el decodificador; insignia «El codificador se ejecuta una vez».\nEstilo: estilo oscuro de la casa; fondo #0B0F19, tarjetas #0F172A; codificador en cian #22D3EE, decodificador en ámbar #F59E0B, subcapas en gris #1E293B con texto #E2E8F0; la flecha de comprensión en cian suave #38BDF8; DejaVu Sans, título 50 px, cuerpo 22 px; radio de tarjeta 18 px.\nPosicionamiento: dos columnas verticales, codificador a la izquierda y decodificador a la derecha; la flecha de comprensión cruza horizontalmente a la altura de la atención cruzada; la salida queda a la derecha del decodificador; la insignia de una sola ejecución sobre el codificador y la etiqueta de iteración bajo el decodificador; título y subtítulo arriba.\nTextos en la imagen: título «Arquitectura Transformer»; subtítulo «Comprender una vez, escribir palabra por palabra»; etiquetas «Codificador (El Lector)», «Auto-atención», «Feed Forward», «Conexión residual», «Decodificador (El Escritor)», «Auto-atención enmascarada», «Atención cruzada», «Mapa de comprensión», «Predicción de la siguiente palabra», «× N palabras», «El codificador se ejecuta una vez»."

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
TITLE = "Arquitectura encoder-decoder"
LOCATION = "Abajo del texto «Los Transformers originales tienen una arquitectura que en Deep Learning conocemos como Codificador-Decodificador (Encoder-Decoder)»."
CONTENT = "Vista general del Transformer original: el codificador comprende toda la oración una sola vez y el decodificador genera palabra por palabra apoyándose en esa comprensión y en la máscara causal.\nComponentes: tarjeta «Codificador (El Lector)» con tres subcapas apiladas («Auto-atención», «Feed Forward», «Conexión residual»); tarjeta «Decodificador (El Escritor)» con cuatro subcapas («Auto-atención enmascarada», «Atención cruzada», «Feed Forward», «Conexión residual»); flecha horizontal «Mapa de comprensión» del codificador al decodificador; tarjeta de salida «Predicción de la siguiente palabra»; etiqueta de iteración «× N palabras» bajo el decodificador; insignia «El codificador se ejecuta una vez».\nEstilo: estilo oscuro de la casa; fondo #0B0F19, tarjetas #0F172A; codificador en cian #22D3EE, decodificador en ámbar #F59E0B, subcapas en gris #1E293B con texto #E2E8F0; la flecha de comprensión en cian suave #38BDF8; DejaVu Sans, título 50 px, cuerpo 22 px; radio de tarjeta 18 px.\nPosicionamiento: dos columnas verticales, codificador a la izquierda y decodificador a la derecha; la flecha de comprensión cruza horizontalmente a la altura de la atención cruzada; la salida queda a la derecha del decodificador; la insignia de una sola ejecución sobre el codificador y la etiqueta de iteración bajo el decodificador; título y subtítulo arriba.\nTextos en la imagen: título «Arquitectura Transformer»; subtítulo «Comprender una vez, escribir palabra por palabra»; etiquetas «Codificador (El Lector)», «Auto-atención», «Feed Forward», «Conexión residual», «Decodificador (El Escritor)», «Auto-atención enmascarada», «Atención cruzada», «Mapa de comprensión», «Predicción de la siguiente palabra», «× N palabras», «El codificador se ejecuta una vez»."
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
    canvas.text((MARGIN, 54), "Arquitectura Transformer",
                font=font(50, bold=True), fill=rgb(TEXT))
    canvas.text((MARGIN, 124), "Comprender una vez, escribir palabra por palabra",
                font=font(26), fill=rgb(MUTED))
    canvas.line((MARGIN, 176, W - MARGIN, 176), fill=rgb(LINE), width=2)

    badge(canvas, 150, 262, "El codificador se ejecuta una vez", fill=CYAN,
          text_color=BG, size=18)

    # ------------------------------------------------------ codificador (lector)
    rounded_box(canvas, (150, 320, 680, 960), radius=18, fill=CARD, outline=LINE)
    canvas.rounded_rectangle((150, 320, 158, 960), radius=4, fill=rgb(CYAN))
    canvas.text((182, 346), "Codificador (El Lector)", font=font(28, bold=True), fill=rgb(TEXT))
    encoder_layers = [("Auto-atención", 415, 530), ("Feed Forward", 575, 690),
                      ("Conexión residual", 730, 845)]
    for label, top, bottom in encoder_layers:
        canvas.rounded_rectangle((182, top, 650, bottom), radius=14,
                                 fill=rgb(LINE), outline=mix(CYAN, BG, 0.55), width=2)
        canvas.text((206, (top + bottom) // 2 - 15), label, font=font(22, bold=True), fill=rgb(TEXT))
    canvas.text((182, 900), "lee toda la oración, de una vez", font=font(19), fill=rgb(MUTED))

    # ----------------------------------------------------- decodificador (escritor)
    rounded_box(canvas, (900, 300, 1400, 1010), radius=18, fill=CARD, outline=LINE)
    canvas.rounded_rectangle((900, 300, 908, 1010), radius=4, fill=rgb(AMBER))
    canvas.text((932, 326), "Decodificador (El Escritor)", font=font(28, bold=True), fill=rgb(TEXT))
    decoder_layers = [("Auto-atención enmascarada", 380, 480), ("Atención cruzada", 502, 602),
                      ("Feed Forward", 624, 724), ("Conexión residual", 746, 846)]
    for label, top, bottom in decoder_layers:
        canvas.rounded_rectangle((932, top, 1370, bottom), radius=14,
                                 fill=rgb(LINE), outline=mix(AMBER, BG, 0.55), width=2)
        canvas.text((956, (top + bottom) // 2 - 15), label, font=font(22, bold=True), fill=rgb(TEXT))
    canvas.text((932, 882), "genera palabra por palabra", font=font(19), fill=rgb(MUTED))
    canvas.text((932, 942), "solo mira las palabras ya escritas", font=font(19), fill=rgb(FAINT))

    # --------------------------------------------------- mapa de comprensión
    arrow(canvas, (686, 552), (896, 552), color=CYAN_SOFT, width=6, head=22)
    canvas.text((698, 490), "Mapa de", font=font(18, bold=True), fill=rgb(CYAN_SOFT))
    canvas.text((698, 518), "comprensión", font=font(18, bold=True), fill=rgb(CYAN_SOFT))

    # ------------------------------------------------------------------ salida
    rounded_box(canvas, (1470, 432, 1700, 672), radius=18, fill=CARD, outline=LINE)
    canvas.rounded_rectangle((1470, 432, 1478, 672), radius=4, fill=rgb(CYAN_SOFT))
    draw_text_block(canvas, 1502, 458, "Predicción de la siguiente palabra",
                    font(19, bold=True), TEXT, max_width=166)
    rounded_box(canvas, (1502, 588, 1668, 628), radius=20, fill=CARD_RAISED, outline=CYAN_SOFT, width=2)
    text_center(canvas, 1585, 598, "texto generado", font(16), MUTED)
    arrow(canvas, (1404, 552), (1466, 552), color=CYAN_SOFT, width=5, head=18)

    # -------------------------------------------------------------- iteración
    badge(canvas, 932, 1036, "× N palabras", fill=AMBER, text_color=BG, size=19)
    canvas.text((1108, 1042), "cada paso añade una palabra", font=font(19), fill=rgb(MUTED))

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

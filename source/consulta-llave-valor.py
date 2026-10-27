""""Consultas, llaves y valores"

Diagrama propuesto por el estudio de diagramas a partir de una recomendación del
blog. Este archivo es autocontenido: se copia a la carpeta del trabajo, el agente
edita `draw()` y `diagram_render` lo ejecuta. La imagen se publica junto al AVIF
en `source/` del repositorio BlogImages, así que debe poder ejecutarse solo con
Pillow:

    python3 source.py            # escribe out.png
    DIAGRAM_OUT=versions/v1.png python3 source.py

Ubicación recomendada: "Abajo del texto «Para lograr esto, el Transformer usa tres conceptos clave: Consultas (Queries), Llaves (Keys) y Valores (Values)»."
Contenido recomendado: "Explica con el ejemplo del blog cómo una palabra lanza una consulta, se compara con las llaves de las demás y recoge sus valores; muestra que «banco» se inclina hacia el sentido financiero.\nComponentes: tarjeta «Consulta (Query): banco» a la izquierda; cuatro tarjetas «Llave (Key)» en columna central («depósito: soy una entidad financiera», «dinero: soy un medio de pago», «el: soy un artículo», «parque: soy un lugar al aire libre»); cuatro tarjetas «Valor (Value)» a la derecha con el contenido semántico de cada palabra; tarjeta final «Vector enriquecido de banco»; conectores de similitud entre la consulta y cada llave.\nEstilo: estilo oscuro de la casa; fondo #0B0F19, tarjetas #0F172A; consulta en cian #22D3EE, llaves en ámbar #F59E0B, valores en verde #34D399, salida en cian suave #38BDF8; el conector más fuerte se dibuja más grueso; DejaVu Sans, título 50 px, cuerpo 22 px; espaciado uniforme de 20 px entre tarjetas.\nPosicionamiento: tres columnas de izquierda a derecha (Consulta → Llaves → Valores); cada llave alineada horizontalmente con su valor; la tarjeta de resultado va abajo a la derecha tras una flecha que sale de los valores; el conector hacia «depósito» es el de mayor grosor para indicar la coincidencia.\nTextos en la imagen: título «Consulta, llave y valor»; subtítulo «Cada palabra pregunta, ofrece etiqueta y entrega contenido»; etiquetas «Consulta (Query)», «banco», «Llave (Key)», «depósito», «dinero», «el», «parque», «Valor (Value)», «Vector enriquecido de banco»; leyenda «grosor de la línea = similitud»."

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
TITLE = "Consultas, llaves y valores"
LOCATION = "Abajo del texto «Para lograr esto, el Transformer usa tres conceptos clave: Consultas (Queries), Llaves (Keys) y Valores (Values)»."
CONTENT = "Explica con el ejemplo del blog cómo una palabra lanza una consulta, se compara con las llaves de las demás y recoge sus valores; muestra que «banco» se inclina hacia el sentido financiero.\nComponentes: tarjeta «Consulta (Query): banco» a la izquierda; cuatro tarjetas «Llave (Key)» en columna central («depósito: soy una entidad financiera», «dinero: soy un medio de pago», «el: soy un artículo», «parque: soy un lugar al aire libre»); cuatro tarjetas «Valor (Value)» a la derecha con el contenido semántico de cada palabra; tarjeta final «Vector enriquecido de banco»; conectores de similitud entre la consulta y cada llave.\nEstilo: estilo oscuro de la casa; fondo #0B0F19, tarjetas #0F172A; consulta en cian #22D3EE, llaves en ámbar #F59E0B, valores en verde #34D399, salida en cian suave #38BDF8; el conector más fuerte se dibuja más grueso; DejaVu Sans, título 50 px, cuerpo 22 px; espaciado uniforme de 20 px entre tarjetas.\nPosicionamiento: tres columnas de izquierda a derecha (Consulta → Llaves → Valores); cada llave alineada horizontalmente con su valor; la tarjeta de resultado va abajo a la derecha tras una flecha que sale de los valores; el conector hacia «depósito» es el de mayor grosor para indicar la coincidencia.\nTextos en la imagen: título «Consulta, llave y valor»; subtítulo «Cada palabra pregunta, ofrece etiqueta y entrega contenido»; etiquetas «Consulta (Query)», «banco», «Llave (Key)», «depósito», «dinero», «el», «parque», «Valor (Value)», «Vector enriquecido de banco»; leyenda «grosor de la línea = similitud»."
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
    canvas.text((MARGIN, 54), "Consulta, llave y valor",
                font=font(50, bold=True), fill=rgb(TEXT))
    canvas.text((MARGIN, 122), "Cada palabra pregunta, ofrece etiqueta y entrega contenido",
                font=font(24), fill=rgb(MUTED))
    canvas.line((MARGIN, 176, W - MARGIN, 176), fill=rgb(LINE), width=2)

    rows = [250, 416, 582, 748]
    row_h = 140
    centers = [top + row_h // 2 for top in rows]  # 317, 475, 633, 791

    canvas.text((560, 210), "Llave (Key)", font=font(20, bold=True), fill=rgb(AMBER))
    canvas.text((1150, 210), "Valor (Value)", font=font(20, bold=True), fill=rgb(GREEN))

    # ---------------------------------------------------------------- consulta
    rounded_box(canvas, (90, 410, 470, 730), radius=22, fill=CARD, outline=LINE)
    canvas.rounded_rectangle((90, 410, 98, 730), radius=4, fill=rgb(CYAN))
    canvas.text((120, 434), "Consulta (Query)", font=font(28, bold=True), fill=rgb(TEXT))
    rounded_box(canvas, (120, 486, 300, 546), radius=30, fill=CARD_RAISED, outline=CYAN, width=2)
    text_center(canvas, 210, 500, "banco", font(28, bold=True), CYAN)
    draw_text_block(canvas, 120, 580,
                    "busco instituciones financieras o muebles para sentarse",
                    font(19), MUTED, max_width=300)

    draw_text_block(canvas, 90, 764,
                    "La consulta se compara con las llaves de todas las palabras.",
                    font(20), MUTED, max_width=330)

    # ------------------------------------------------------------------ llaves
    keys = [
        ("depósito", "soy una entidad financiera"),
        ("dinero", "soy un medio de pago"),
        ("el", "soy un artículo"),
        ("parque", "soy un lugar al aire libre"),
    ]
    for index, (word, tag) in enumerate(keys):
        top = rows[index]
        rounded_box(canvas, (560, top, 1060, top + row_h), radius=18, fill=CARD, outline=LINE)
        canvas.rounded_rectangle((560, top, 568, top + row_h), radius=4, fill=rgb(AMBER))
        canvas.text((600, top + 22), word, font=font(30, bold=True), fill=rgb(TEXT))
        canvas.text((600, top + 82), tag, font=font(19), fill=rgb(MUTED))

    # ----------------------------------------------------------------- valores
    values = [
        "contenido de «depósito»",
        "contenido de «dinero»",
        "contenido de «el»",
        "contenido de «parque»",
    ]
    vectors = [
        [16, 26, 12, 22, 30, 18, 24, 14, 20],
        [22, 14, 28, 18, 12, 26, 16, 30, 20],
        [10, 20, 14, 26, 22, 12, 18, 24, 16],
        [26, 18, 22, 12, 28, 20, 14, 24, 30],
    ]
    for index, label in enumerate(values):
        top = rows[index]
        rounded_box(canvas, (1150, top, 1650, top + row_h), radius=18, fill=CARD, outline=LINE)
        canvas.rounded_rectangle((1150, top, 1158, top + row_h), radius=4, fill=rgb(GREEN))
        canvas.text((1190, top + 22), label, font=font(20, bold=True), fill=rgb(TEXT))
        for bar_index, height in enumerate(vectors[index]):
            bx = 1190 + bar_index * 24
            canvas.rounded_rectangle((bx, top + 118 - height, bx + 14, top + 118), radius=4,
                                     fill=mix(GREEN, BG, 0.1 + (bar_index % 3) * 0.12))

    # ------------------------------------------------- conectores de similitud
    similarities = [(0, 11), (1, 7), (2, 3), (3, 3)]
    for index, width in similarities:
        arrow(canvas, (472, 580), (554, centers[index]), color=AMBER,
              width=width, head=8 + width)
    for cy in centers:
        arrow(canvas, (1064, cy), (1144, cy), color=GREEN, width=3, head=10)

    # ----------------------------------------------------------------- salida
    rounded_box(canvas, (1150, 920, 1650, 1100), radius=22, fill=CARD, outline=LINE)
    canvas.rounded_rectangle((1150, 920, 1158, 1100), radius=4, fill=rgb(CYAN_SOFT))
    canvas.text((1190, 944), "Vector enriquecido de banco", font=font(26, bold=True), fill=rgb(TEXT))
    canvas.text((1190, 988), "mezcla de los valores según su similitud",
                font=font(19), fill=rgb(MUTED))
    for bar_index, height in enumerate([18, 28, 14, 24, 32, 20, 26]):
        bx = 1190 + bar_index * 26
        canvas.rounded_rectangle((bx, 1078 - height, bx + 16, 1078), radius=5,
                                 fill=mix(CYAN_SOFT, BG, 0.1 + (bar_index % 3) * 0.1))
    arrow(canvas, (1400, 894), (1400, 916), color=CYAN_SOFT, width=4, head=12)

    # ---------------------------------------------------------------- leyenda
    canvas.text((90, 960), "grosor de la línea = similitud", font=font(20), fill=rgb(MUTED))
    canvas.line((90, 1012, 170, 1012), fill=rgb(AMBER), width=10)
    canvas.text((190, 998), "más similitud", font=font(18), fill=rgb(FAINT))
    canvas.line((90, 1052, 170, 1052), fill=rgb(AMBER), width=3)
    canvas.text((190, 1040), "menos similitud", font=font(18), fill=rgb(FAINT))

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

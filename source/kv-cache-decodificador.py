""""KV Cache del decodificador"

Diagrama propuesto por el estudio de diagramas a partir de una recomendación del
blog. Este archivo es autocontenido: se copia a la carpeta del trabajo, el agente
edita `draw()` y `diagram_render` lo ejecuta. La imagen se publica junto al AVIF
en `source/` del repositorio BlogImages, así que debe poder ejecutarse solo con
Pillow:

    python3 source.py            # escribe out.png
    DIAGRAM_OUT=versions/v1.png python3 source.py

Ubicación recomendada: "Abajo del texto «el modelo utiliza una especie de libreta inteligente llamada KV Cache (Cache de Claves y Valores)»."
Contenido recomendado: "Muestra cómo el decodificador guarda en una libreta las claves y valores de las palabras ya procesadas y solo calcula la atención de la palabra nueva, evitando releer todo desde cero.\nComponentes: columna izquierda «Palabras ya procesadas» con píldoras («El», «perro», «ladra», «fuerte») en gris; tarjeta central «Libreta KV Cache» con filas «K: … / V: …» por cada palabra; tarjeta derecha «Palabra nueva: ¿?»; tarjeta inferior «Solo se calcula la atención de la nueva»; insignia «Ahorro: no se recalcula el pasado»; flechas de lectura desde la libreta hacia la palabra nueva.\nEstilo: estilo oscuro de la casa; fondo #0B0F19, tarjetas #0F172A; palabras procesadas en gris #64748B, libreta en cian #22D3EE con filas alternas #141E33, palabra nueva en ámbar #F59E0B, ahorro en verde #34D399; DejaVu Sans, título 50 px, cuerpo 22 px; líneas de 2 px dentro de la libreta.\nPosicionamiento: de izquierda a derecha, palabras procesadas → libreta KV → palabra nueva; las flechas salen de la libreta hacia la palabra nueva y no hacia atrás, para subrayar que el pasado no se recalcula; la tarjeta de ahorro cruza abajo; título y subtítulo arriba.\nTextos en la imagen: título «KV Cache: la libreta del decodificador»; subtítulo «Guardar el pasado para no releerlo»; etiquetas «Palabras ya procesadas», «El», «perro», «ladra», «fuerte», «Libreta KV Cache», «K: clave», «V: valor», «Palabra nueva», «Solo se calcula la atención de la nueva», «Ahorro: no se recalcula el pasado»."

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
TITLE = "KV Cache del decodificador"
LOCATION = "Abajo del texto «el modelo utiliza una especie de libreta inteligente llamada KV Cache (Cache de Claves y Valores)»."
CONTENT = "Muestra cómo el decodificador guarda en una libreta las claves y valores de las palabras ya procesadas y solo calcula la atención de la palabra nueva, evitando releer todo desde cero.\nComponentes: columna izquierda «Palabras ya procesadas» con píldoras («El», «perro», «ladra», «fuerte») en gris; tarjeta central «Libreta KV Cache» con filas «K: … / V: …» por cada palabra; tarjeta derecha «Palabra nueva: ¿?»; tarjeta inferior «Solo se calcula la atención de la nueva»; insignia «Ahorro: no se recalcula el pasado»; flechas de lectura desde la libreta hacia la palabra nueva.\nEstilo: estilo oscuro de la casa; fondo #0B0F19, tarjetas #0F172A; palabras procesadas en gris #64748B, libreta en cian #22D3EE con filas alternas #141E33, palabra nueva en ámbar #F59E0B, ahorro en verde #34D399; DejaVu Sans, título 50 px, cuerpo 22 px; líneas de 2 px dentro de la libreta.\nPosicionamiento: de izquierda a derecha, palabras procesadas → libreta KV → palabra nueva; las flechas salen de la libreta hacia la palabra nueva y no hacia atrás, para subrayar que el pasado no se recalcula; la tarjeta de ahorro cruza abajo; título y subtítulo arriba.\nTextos en la imagen: título «KV Cache: la libreta del decodificador»; subtítulo «Guardar el pasado para no releerlo»; etiquetas «Palabras ya procesadas», «El», «perro», «ladra», «fuerte», «Libreta KV Cache», «K: clave», «V: valor», «Palabra nueva», «Solo se calcula la atención de la nueva», «Ahorro: no se recalcula el pasado»."
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
    canvas.text((MARGIN, 54), "KV Cache: la libreta del decodificador",
                font=font(50, bold=True), fill=rgb(TEXT))
    canvas.text((MARGIN, 124), "Guardar el pasado para no releerlo",
                font=font(26), fill=rgb(MUTED))
    canvas.line((MARGIN, 176, W - MARGIN, 176), fill=rgb(LINE), width=2)
    badge(canvas, 1190, 204, "Ahorro: no se recalcula el pasado", fill=GREEN,
          text_color=BG, size=17)

    rows = [390, 510, 630, 750]
    row_h = 106
    centers = [top + row_h // 2 for top in rows]  # 443, 563, 683, 803

    # --------------------------------------------------- palabras ya procesadas
    rounded_box(canvas, (90, 300, 540, 880), radius=22, fill=CARD, outline=LINE)
    canvas.rounded_rectangle((90, 300, 98, 880), radius=4, fill=rgb(FAINT))
    canvas.text((120, 326), "Palabras ya procesadas", font=font(22, bold=True), fill=rgb(MUTED))
    for index, (word, center) in enumerate(zip(["El", "perro", "ladra", "fuerte"], centers)):
        rounded_box(canvas, (120, center - 32, 500, center + 32), radius=32,
                    fill=CARD_RAISED, outline=FAINT, width=2)
        text_center(canvas, 310, center - 19, word, font(26, bold=True), MUTED)

    # ------------------------------------------------------ libreta KV Cache
    rounded_box(canvas, (620, 300, 1200, 880), radius=22, fill=CARD, outline=LINE)
    canvas.rounded_rectangle((620, 300, 628, 880), radius=4, fill=rgb(CYAN))
    canvas.text((650, 322), "Libreta KV Cache", font=font(24, bold=True), fill=rgb(CYAN))
    canvas.text((650, 356), "claves y valores ya calculados", font=font(18), fill=rgb(FAINT))
    book_words = ["El", "perro", "ladra", "fuerte"]
    for index, (word, top) in enumerate(zip(book_words, rows)):
        fill = CARD_RAISED if index % 2 == 0 else CARD
        canvas.rounded_rectangle((644, top, 1176, top + row_h), radius=14, fill=rgb(fill),
                                 outline=rgb(LINE), width=2)
        canvas.text((668, top + 16), word, font=font(26, bold=True), fill=rgb(TEXT))
        canvas.text((876, top + 22), "K: clave", font=font(17, bold=True), fill=rgb(MUTED))
        canvas.text((1040, top + 22), "V: valor", font=font(17, bold=True), fill=rgb(MUTED))
        canvas.text((876, top + 56), "vector guardado", font=font(14), fill=rgb(FAINT))
        canvas.text((1040, top + 56), "vector guardado", font=font(14), fill=rgb(FAINT))

    # ---------------------------------------------------------- palabra nueva
    rounded_box(canvas, (1260, 420, 1710, 760), radius=22, fill=CARD, outline=LINE)
    canvas.rounded_rectangle((1260, 420, 1268, 760), radius=4, fill=rgb(AMBER))
    canvas.text((1292, 446), "Palabra nueva", font=font(22, bold=True), fill=rgb(AMBER))
    rounded_box(canvas, (1292, 494, 1412, 570), radius=38, fill=CARD_RAISED, outline=AMBER, width=2)
    text_center(canvas, 1352, 512, "¿?", font(34, bold=True), AMBER)
    draw_text_block(canvas, 1292, 596, "solo se calcula la atención de esta palabra",
                    font(19), MUTED, max_width=380)
    canvas.text((1292, 690), "el resto sale de la libreta", font=font(18), fill=rgb(FAINT))

    # ---------------------------------------------------------------- flechas
    for cy in centers:
        arrow(canvas, (1204, cy), (1232, cy), color=CYAN, width=3, head=10)
    canvas.line((1238, 443, 1238, 803), fill=rgb(CYAN), width=3)
    arrow(canvas, (1238, 600), (1254, 600), color=CYAN, width=3, head=11)

    # ------------------------------------------------------------ tarjeta final
    rounded_box(canvas, (90, 920, 1710, 1060), radius=22, fill=CARD, outline=LINE)
    canvas.rounded_rectangle((90, 920, 98, 1060), radius=4, fill=rgb(GREEN))
    canvas.text((130, 962), "Solo se calcula la atención de la nueva", font=font(26, bold=True),
                fill=rgb(TEXT))
    canvas.text((130, 1008), "el pasado ya está en la libreta: no se relee", font=font(19),
                fill=rgb(MUTED))

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

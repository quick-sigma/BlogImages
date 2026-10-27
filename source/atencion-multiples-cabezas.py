""""Varios ojos: atención multi-cabeza"

Diagrama propuesto por el estudio de diagramas a partir de una recomendación del
blog. Este archivo es autocontenido: se copia a la carpeta del trabajo, el agente
edita `draw()` y `diagram_render` lo ejecuta. La imagen se publica junto al AVIF
en `source/` del repositorio BlogImages, así que debe poder ejecutarse solo con
Pillow:

    python3 source.py            # escribe out.png
    DIAGRAM_OUT=versions/v1.png python3 source.py

Ubicación recomendada: "Abajo del texto «En lugar de obligar a un solo mecanismo a entender todas las relaciones del lenguaje, el modelo despliega varios mecanismos de atención en paralelo, donde cada uno se especializa en detectar distintos patrones»."
Contenido recomendado: "Muestra cómo la misma oración se procesa por varias cabezas especializadas en paralelo y cómo sus resultados se concatenan en una representación más rica.\nComponentes: tarjeta «Entrada: El perro ladra fuerte»; cuatro tarjetas de cabeza en paralelo («Cabeza 1: pronombres», «Cabeza 2: sintaxis», «Cabeza 3: semántica», «Cabeza 4: negaciones»), cada una con una mini-frase de ejemplo; tarjeta «Concatenación»; tarjeta de salida «Representación enriquecida»; insignia «8 cabezas en el paper original».\nEstilo: estilo oscuro de la casa; fondo #0B0F19, tarjetas #0F172A; las cabezas alternan acentos cian #22D3EE, cian suave #38BDF8, verde #34D399 y ámbar #F59E0B; concatenación en gris #94A3B8; DejaVu Sans, título 50 px, cuerpo 22 px; flechas de 4 px; separación de 24 px entre cabezas.\nPosicionamiento: abanico horizontal; la entrada a la izquierda en el centro vertical; las cuatro cabezas en columna a la derecha de la entrada; tras ellas, sus flechas convergen en la tarjeta «Concatenación» y de ahí una sola flecha a la salida a la derecha; la insignia «8 cabezas» arriba a la derecha.\nTextos en la imagen: título «Atención de múltiples cabezas»; subtítulo «Varios ojos para la misma verdad»; etiquetas «Entrada: El perro ladra fuerte», «Cabeza 1: pronombres», «Cabeza 2: sintaxis», «Cabeza 3: semántica», «Cabeza 4: negaciones», «Concatenación», «Representación enriquecida», «8 cabezas en el paper original»."

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
TITLE = "Varios ojos: atención multi-cabeza"
LOCATION = "Abajo del texto «En lugar de obligar a un solo mecanismo a entender todas las relaciones del lenguaje, el modelo despliega varios mecanismos de atención en paralelo, donde cada uno se especializa en detectar distintos patrones»."
CONTENT = "Muestra cómo la misma oración se procesa por varias cabezas especializadas en paralelo y cómo sus resultados se concatenan en una representación más rica.\nComponentes: tarjeta «Entrada: El perro ladra fuerte»; cuatro tarjetas de cabeza en paralelo («Cabeza 1: pronombres», «Cabeza 2: sintaxis», «Cabeza 3: semántica», «Cabeza 4: negaciones»), cada una con una mini-frase de ejemplo; tarjeta «Concatenación»; tarjeta de salida «Representación enriquecida»; insignia «8 cabezas en el paper original».\nEstilo: estilo oscuro de la casa; fondo #0B0F19, tarjetas #0F172A; las cabezas alternan acentos cian #22D3EE, cian suave #38BDF8, verde #34D399 y ámbar #F59E0B; concatenación en gris #94A3B8; DejaVu Sans, título 50 px, cuerpo 22 px; flechas de 4 px; separación de 24 px entre cabezas.\nPosicionamiento: abanico horizontal; la entrada a la izquierda en el centro vertical; las cuatro cabezas en columna a la derecha de la entrada; tras ellas, sus flechas convergen en la tarjeta «Concatenación» y de ahí una sola flecha a la salida a la derecha; la insignia «8 cabezas» arriba a la derecha.\nTextos en la imagen: título «Atención de múltiples cabezas»; subtítulo «Varios ojos para la misma verdad»; etiquetas «Entrada: El perro ladra fuerte», «Cabeza 1: pronombres», «Cabeza 2: sintaxis», «Cabeza 3: semántica», «Cabeza 4: negaciones», «Concatenación», «Representación enriquecida», «8 cabezas en el paper original»."
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
    canvas.text((MARGIN, 54), "Atención de múltiples cabezas",
                font=font(50, bold=True), fill=rgb(TEXT))
    canvas.text((MARGIN, 124), "Varios ojos para la misma verdad",
                font=font(26), fill=rgb(MUTED))
    canvas.line((MARGIN, 176, W - MARGIN, 176), fill=rgb(LINE), width=2)

    badge(canvas, 1200, 200, "8 cabezas en el paper original", fill=AMBER,
          text_color=BG, size=18)

    # ------------------------------------------------------------------ entrada
    rounded_box(canvas, (90, 560, 440, 780), radius=22, fill=CARD, outline=LINE)
    canvas.rounded_rectangle((90, 560, 98, 780), radius=4, fill=rgb(CYAN))
    canvas.text((120, 590), "Entrada", font=font(20, bold=True), fill=rgb(MUTED))
    draw_text_block(canvas, 120, 632, "El perro ladra fuerte", font(30, bold=True),
                    TEXT, max_width=290)
    canvas.text((120, 716), "una sola oración", font=font(19), fill=rgb(FAINT))

    # ------------------------------------------------------------------- cabezas
    heads = [
        ("Cabeza 1: pronombres", "«él» se refiere a «perro»", CYAN),
        ("Cabeza 2: sintaxis", "sujeto = «perro»; verbo = «ladra»", CYAN_SOFT),
        ("Cabeza 3: semántica", "«ladra» es una acción del perro", GREEN),
        ("Cabeza 4: negaciones", "detecta la negación de la oración", AMBER),
    ]
    head_tops = [280, 490, 700, 910]
    head_h, head_w = 150, 420
    head_centers = [top + head_h // 2 for top in head_tops]  # 355, 565, 775, 985
    for index, (title, example, accent) in enumerate(heads):
        top = head_tops[index]
        rounded_box(canvas, (700, top, 700 + head_w, top + head_h), radius=20,
                    fill=CARD, outline=LINE)
        canvas.rounded_rectangle((700, top, 708, top + head_h), radius=4, fill=rgb(accent))
        canvas.text((736, top + 26), title, font=font(23, bold=True), fill=rgb(accent))
        draw_text_block(canvas, 736, top + 76, example, font(19), MUTED, max_width=348)

    # -------------------------------------------------------------- concatenación
    rounded_box(canvas, (1170, 576, 1420, 756), radius=22, fill=CARD, outline=LINE)
    canvas.rounded_rectangle((1170, 576, 1178, 756), radius=4, fill=rgb(MUTED))
    canvas.text((1202, 604), "Concatenación", font=font(24, bold=True), fill=rgb(TEXT))
    draw_text_block(canvas, 1202, 652, "se unen las cuatro cabezas", font(18), MUTED,
                    max_width=186)

    # ------------------------------------------------------------------- salida
    rounded_box(canvas, (1480, 546, 1710, 786), radius=22, fill=CARD, outline=LINE)
    canvas.rounded_rectangle((1480, 546, 1488, 786), radius=4, fill=rgb(CYAN_SOFT))
    draw_text_block(canvas, 1512, 574, "Representación enriquecida", font(19, bold=True),
                    TEXT, max_width=178)
    for bar_index, height in enumerate([18, 30, 14, 26, 34, 20, 28]):
        bx = 1512 + bar_index * 24
        canvas.rounded_rectangle((bx, 736 - height, bx + 16, 736), radius=5,
                                 fill=mix(CYAN_SOFT, BG, 0.08 + (bar_index % 3) * 0.12))

    # ------------------------------------------------------------------ flechas
    for index, (_, _, accent) in enumerate(heads):
        arrow(canvas, (444, 670), (696, head_centers[index]), color=accent, width=4, head=14)
    for index, cy in enumerate(head_centers):
        arrow(canvas, (1124, cy), (1166, 620 + index * 30), color=MUTED, width=4, head=14)
    arrow(canvas, (1424, 666), (1476, 666), color=CYAN_SOFT, width=5, head=16)

    # ---------------------------------------------------------------- nota final
    draw_text_block(canvas, 90, 1088,
                    "Nadie programó estas especialidades: el modelo las aprendió "
                    "durante el entrenamiento.",
                    font(20), MUTED, max_width=1000)

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

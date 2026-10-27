""""Los tres ingredientes del escalado"

Diagrama propuesto por el estudio de diagramas a partir de una recomendación del
blog. Este archivo es autocontenido: se copia a la carpeta del trabajo, el agente
edita `draw()` y `diagram_render` lo ejecuta. La imagen se publica junto al AVIF
en `source/` del repositorio BlogImages, así que debe poder ejecutarse solo con
Pillow:

    python3 source.py            # escribe out.png
    DIAGRAM_OUT=versions/v1.png python3 source.py

Ubicación recomendada: "Abajo del texto «Imagina que estás cocinando. El rendimiento final del modelo depende de tres ingredientes clave»."
Contenido recomendado: "Presenta los tres factores que determinan el rendimiento y la ley de potencia que los relaciona: duplicar cualquiera de ellos produce una mejora suave y predecible.\nComponentes: tres tarjetas de ingrediente arriba («Parámetros: el tamaño de la olla», «Datos: los ingredientes», «Cómputo: el fuego»); un panel grande inferior con una curva de ley de potencia en ejes logarítmicos («Cómputo» en X, «Pérdida» en Y); una anotación sobre la curva «mejora suave y predecible»; una nota «arquitectura ≈ tamaño total» al lado de las tarjetas.\nEstilo: estilo oscuro de la casa; fondo #0B0F19, tarjetas #0F172A; parámetros en cian #22D3EE, datos en verde #34D399, cómputo en ámbar #F59E0B; la curva en cian suave #38BDF8 sobre una cuadrícula tenue #1E293B; DejaVu Sans, título 50 px, cuerpo 22 px; sin degradados ni sombras.\nPosicionamiento: las tres tarjetas en fila ocupando el tercio superior; el panel de la curva debajo ocupando el ancho completo y el resto del alto; la anotación pegada a la curva en su tramo medio; la nota de arquitectura a la derecha del bloque de tarjetas; título y subtítulo arriba.\nTextos en la imagen: título «Leyes de escalado»; subtítulo «Tres ingredientes, una curva predecible»; etiquetas «Parámetros», «el tamaño de la olla», «Datos», «los ingredientes», «Cómputo», «el fuego», «Pérdida», «Cómputo», «mejora suave y predecible», «arquitectura ≈ tamaño total»."

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
TITLE = "Los tres ingredientes del escalado"
LOCATION = "Abajo del texto «Imagina que estás cocinando. El rendimiento final del modelo depende de tres ingredientes clave»."
CONTENT = "Presenta los tres factores que determinan el rendimiento y la ley de potencia que los relaciona: duplicar cualquiera de ellos produce una mejora suave y predecible.\nComponentes: tres tarjetas de ingrediente arriba («Parámetros: el tamaño de la olla», «Datos: los ingredientes», «Cómputo: el fuego»); un panel grande inferior con una curva de ley de potencia en ejes logarítmicos («Cómputo» en X, «Pérdida» en Y); una anotación sobre la curva «mejora suave y predecible»; una nota «arquitectura ≈ tamaño total» al lado de las tarjetas.\nEstilo: estilo oscuro de la casa; fondo #0B0F19, tarjetas #0F172A; parámetros en cian #22D3EE, datos en verde #34D399, cómputo en ámbar #F59E0B; la curva en cian suave #38BDF8 sobre una cuadrícula tenue #1E293B; DejaVu Sans, título 50 px, cuerpo 22 px; sin degradados ni sombras.\nPosicionamiento: las tres tarjetas en fila ocupando el tercio superior; el panel de la curva debajo ocupando el ancho completo y el resto del alto; la anotación pegada a la curva en su tramo medio; la nota de arquitectura a la derecha del bloque de tarjetas; título y subtítulo arriba.\nTextos en la imagen: título «Leyes de escalado»; subtítulo «Tres ingredientes, una curva predecible»; etiquetas «Parámetros», «el tamaño de la olla», «Datos», «los ingredientes», «Cómputo», «el fuego», «Pérdida», «Cómputo», «mejora suave y predecible», «arquitectura ≈ tamaño total»."
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
    canvas.text((MARGIN, 54), "Leyes de escalado",
                font=font(50, bold=True), fill=rgb(TEXT))
    canvas.text((MARGIN, 124), "Tres ingredientes, una curva predecible",
                font=font(24), fill=rgb(MUTED))
    canvas.line((MARGIN, 176, W - MARGIN, 176), fill=rgb(LINE), width=2)

    # ----------------------------------------------------------- ingredientes
    ingredients = [
        (90, 520, CYAN, "Parámetros", "el tamaño de la olla"),
        (550, 980, GREEN, "Datos", "los ingredientes"),
        (1010, 1440, AMBER, "Cómputo", "el fuego"),
    ]
    for x0, x1, accent, title, subtitle in ingredients:
        rounded_box(canvas, (x0, 240, x1, 420), radius=20, fill=CARD, outline=LINE)
        canvas.rounded_rectangle((x0, 240, x0 + 8, 420), radius=4, fill=rgb(accent))
        canvas.text((x0 + 112, 274), title, font=font(26, bold=True), fill=rgb(TEXT))
        canvas.text((x0 + 112, 314), subtitle, font=font(19), fill=rgb(MUTED))

        ix = x0 + 34
        if title == "Parámetros":
            for i in range(3):
                canvas.rounded_rectangle((ix, 276 + i * 20, ix + 56 - i * 10, 288 + i * 20),
                                         radius=6, fill=rgb(accent))
        elif title == "Datos":
            for i in range(3):
                for j in range(2):
                    canvas.rounded_rectangle((ix + i * 20, 272 + j * 26, ix + 14 + i * 20,
                                              284 + j * 26), radius=4, fill=rgb(accent))
        else:
            canvas.polygon([(ix + 28, 268), (ix + 12, 302), (ix + 44, 302)], fill=rgb(accent))
            canvas.polygon([(ix + 28, 286), (ix + 6, 320), (ix + 50, 320)],
                           fill=mix(AMBER, BG, 0.35))

    # --------------------------------------------------------- nota arquitectura
    rounded_box(canvas, (1470, 240, 1710, 420), radius=20, fill=CARD, outline=LINE)
    canvas.rounded_rectangle((1470, 240, 1478, 420), radius=4, fill=rgb(MUTED))
    draw_text_block(canvas, 1502, 274, "arquitectura ≈ tamaño total",
                    font(21, bold=True), TEXT, max_width=180)

    # ---------------------------------------------------------------- gráfica
    rounded_box(canvas, (90, 450, 1710, 1100), radius=22, fill=CARD, outline=LINE)
    left, top, right, bottom = 340, 540, 1600, 1000

    for i in range(6):
        gx = left + i * (right - left) // 5
        canvas.line((gx, top, gx, bottom), fill=rgb(LINE), width=2)
        gy = top + i * (bottom - top) // 5
        canvas.line((left, gy, right, gy), fill=rgb(LINE), width=2)
    canvas.line((left, top, left, bottom), fill=rgb(MUTED), width=2)
    canvas.line((left, bottom, right, bottom), fill=rgb(MUTED), width=2)

    canvas.text((left, top - 34), "Pérdida", font=font(19, bold=True), fill=rgb(MUTED))
    canvas.text((right - 96, bottom + 18), "Cómputo", font=font(19, bold=True), fill=rgb(MUTED))
    canvas.text((left, bottom + 48), "escala logarítmica", font=font(15), fill=rgb(FAINT))

    curve = []
    for step in range(0, 101):
        t = step / 100
        curve.append((left + t * (right - left), bottom - (bottom - top) * ((1 - t) ** 1.8)))
    canvas.line(curve, fill=rgb(CYAN_SOFT), width=4, joint="curve")
    for t in (0.25, 0.5, 0.75):
        px = left + t * (right - left)
        py = bottom - (bottom - top) * ((1 - t) ** 1.8)
        canvas.ellipse((px - 6, py - 6, px + 6, py + 6), fill=rgb(CYAN_SOFT))

    # ---------------------------------------------------------------- anotación
    ax, ay = 1010, 700
    canvas.text((ax, ay), "mejora suave y predecible", font=font(22, bold=True), fill=rgb(TEXT))
    arrow(canvas, (ax + 10, ay + 44), (ax - 60, ay + 150), color=FAINT, width=2, head=10)

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

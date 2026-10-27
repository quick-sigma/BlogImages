""""Chinchilla: la receta óptima"

Diagrama propuesto por el estudio de diagramas a partir de una recomendación del
blog. Este archivo es autocontenido: se copia a la carpeta del trabajo, el agente
edita `draw()` y `diagram_render` lo ejecuta. La imagen se publica junto al AVIF
en `source/` del repositorio BlogImages, así que debe poder ejecutarse solo con
Pillow:

    python3 source.py            # escribe out.png
    DIAGRAM_OUT=versions/v1.png python3 source.py

Ubicación recomendada: "Abajo del texto «Demostraron que, para un presupuesto computacional fijo (digamos, tienes 1000 GPUs por un mes), la receta óptima no era un modelo gigante con pocos datos, sino un modelo mediano con muchísimos más datos»."
Contenido recomendado: "Contrasta la receta anterior (modelo gigante con pocos datos) con la de Chinchilla (modelo mediano con muchos más datos) bajo el mismo presupuesto de cómputo, destacando el coste de inferencia.\nComponentes: barra superior «Presupuesto fijo: 1000 GPUs × 1 mes»; panel izquierdo «Antes: modelo gigante, pocos datos» con icono de modelo grande y un bloque de datos pequeño; panel derecho «Chinchilla: modelo mediano, muchos datos» con icono mediano y un bloque de datos grande; tarjeta de resultado izquierda «Mejor al entrenar, caro al usar»; tarjeta de resultado derecha «Igual o mejor, más barato de usar»; nota final «LLaMA 7B/13B superó a GPT-3 175B».\nEstilo: estilo oscuro de la casa; fondo #0B0F19, tarjetas #0F172A; presupuesto en ámbar #F59E0B; el panel izquierdo con acento rojo #F87171, el derecho con acento verde #34D399; bloques de datos en cian #22D3EE; DejaVu Sans, título 50 px, cuerpo 22 px; comparación simétrica y limpia.\nPosicionamiento: título y subtítulo arriba; la barra de presupuesto cruza todo el ancho debajo del subtítulo; dos columnas iguales debajo, «Antes» a la izquierda y «Chinchilla» a la derecha, separadas por una línea vertical tenue; las tarjetas de resultado al pie de cada columna; la nota de LLaMA como franja inferior centrada.\nTextos en la imagen: título «La receta óptima: Chinchilla»; subtítulo «Mismo cómputo, mejor reparto»; etiquetas «Presupuesto fijo: 1000 GPUs × 1 mes», «Antes», «modelo gigante, pocos datos», «Chinchilla», «modelo mediano, muchos datos», «Mejor al entrenar, caro al usar», «Igual o mejor, más barato de usar», «LLaMA 7B/13B superó a GPT-3 175B»."

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
TITLE = "Chinchilla: la receta óptima"
LOCATION = "Abajo del texto «Demostraron que, para un presupuesto computacional fijo (digamos, tienes 1000 GPUs por un mes), la receta óptima no era un modelo gigante con pocos datos, sino un modelo mediano con muchísimos más datos»."
CONTENT = "Contrasta la receta anterior (modelo gigante con pocos datos) con la de Chinchilla (modelo mediano con muchos más datos) bajo el mismo presupuesto de cómputo, destacando el coste de inferencia.\nComponentes: barra superior «Presupuesto fijo: 1000 GPUs × 1 mes»; panel izquierdo «Antes: modelo gigante, pocos datos» con icono de modelo grande y un bloque de datos pequeño; panel derecho «Chinchilla: modelo mediano, muchos datos» con icono mediano y un bloque de datos grande; tarjeta de resultado izquierda «Mejor al entrenar, caro al usar»; tarjeta de resultado derecha «Igual o mejor, más barato de usar»; nota final «LLaMA 7B/13B superó a GPT-3 175B».\nEstilo: estilo oscuro de la casa; fondo #0B0F19, tarjetas #0F172A; presupuesto en ámbar #F59E0B; el panel izquierdo con acento rojo #F87171, el derecho con acento verde #34D399; bloques de datos en cian #22D3EE; DejaVu Sans, título 50 px, cuerpo 22 px; comparación simétrica y limpia.\nPosicionamiento: título y subtítulo arriba; la barra de presupuesto cruza todo el ancho debajo del subtítulo; dos columnas iguales debajo, «Antes» a la izquierda y «Chinchilla» a la derecha, separadas por una línea vertical tenue; las tarjetas de resultado al pie de cada columna; la nota de LLaMA como franja inferior centrada.\nTextos en la imagen: título «La receta óptima: Chinchilla»; subtítulo «Mismo cómputo, mejor reparto»; etiquetas «Presupuesto fijo: 1000 GPUs × 1 mes», «Antes», «modelo gigante, pocos datos», «Chinchilla», «modelo mediano, muchos datos», «Mejor al entrenar, caro al usar», «Igual o mejor, más barato de usar», «LLaMA 7B/13B superó a GPT-3 175B»."
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
    canvas.text((MARGIN, 54), "La receta óptima: Chinchilla",
                font=font(50, bold=True), fill=rgb(TEXT))
    canvas.text((MARGIN, 124), "Mismo cómputo, mejor reparto",
                font=font(24), fill=rgb(MUTED))
    canvas.line((MARGIN, 176, W - MARGIN, 176), fill=rgb(LINE), width=2)

    # --------------------------------------------------------------- presupuesto
    rounded_box(canvas, (90, 206, 1710, 282), radius=18, fill=CARD, outline=LINE)
    canvas.rounded_rectangle((90, 206, 98, 282), radius=4, fill=rgb(AMBER))
    canvas.text((130, 226), "Presupuesto fijo: 1000 GPUs × 1 mes",
                font=font(24, bold=True), fill=rgb(TEXT))
    canvas.text((1400, 230), "el mismo para los dos", font=font(19), fill=rgb(FAINT))

    # ---------------------------------------------------------------- columnas
    canvas.line((900, 310, 900, 990), fill=rgb(LINE), width=2)

    columns = [
        (90, 880, RED, "Antes", "modelo gigante, pocos datos",
         ("grande", 620), ("pocos", 150),
         ("Mejor al entrenar,", "caro al usar"), "cada uso cuesta más"),
        (920, 1710, GREEN, "Chinchilla", "modelo mediano, muchos datos",
         ("mediano", 340), ("muchos", 620),
         ("Igual o mejor,", "más barato de usar"), "más rápido de ejecutar"),
    ]
    for x0, x1, accent, title, subtitle, (model_word, model_w), (data_word, data_w), result, note in columns:
        rounded_box(canvas, (x0, 310, x1, 990), radius=22, fill=CARD, outline=LINE)
        canvas.rounded_rectangle((x0, 310, x0 + 8, 990), radius=4, fill=rgb(accent))
        canvas.text((x0 + 40, 338), title, font=font(34, bold=True), fill=rgb(TEXT))
        canvas.text((x0 + 40, 388), subtitle, font=font(21), fill=rgb(MUTED))

        base = x0 + 40
        canvas.text((base, 462), "Modelo", font=font(19, bold=True), fill=rgb(MUTED))
        canvas.rounded_rectangle((base, 496, base + model_w, 540), radius=12,
                                 fill=mix(accent, BG, 0.12))
        canvas.text((base + model_w + 16, 504), model_word, font=font(18), fill=rgb(FAINT))

        canvas.text((base, 578), "Datos", font=font(19, bold=True), fill=rgb(MUTED))
        canvas.rounded_rectangle((base, 612, base + data_w, 656), radius=12, fill=rgb(CYAN))
        canvas.text((base + data_w + 16, 620), data_word, font=font(18), fill=rgb(FAINT))

        rounded_box(canvas, (x0 + 40, 720, x1 - 40, 920), radius=18, fill=CARD_RAISED, outline=LINE)
        canvas.rounded_rectangle((x0 + 40, 720, x0 + 46, 920), radius=4, fill=rgb(accent))
        canvas.text((x0 + 76, 754), result[0], font=font(25, bold=True), fill=rgb(TEXT))
        canvas.text((x0 + 76, 796), result[1], font=font(25, bold=True), fill=rgb(accent))
        canvas.text((x0 + 76, 858), note, font=font(19), fill=rgb(MUTED))

    # ------------------------------------------------------------- nota inferior
    rounded_box(canvas, (90, 1020, 1710, 1110), radius=18, fill=CARD, outline=LINE)
    canvas.rounded_rectangle((90, 1020, 98, 1110), radius=4, fill=rgb(CYAN))
    text_center(canvas, 900, 1046, "LLaMA 7B/13B superó a GPT-3 175B",
                font(24, bold=True), TEXT)

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

""""Ciclo autorregresivo con velo causal"

Diagrama propuesto por el estudio de diagramas a partir de una recomendación del
blog. Este archivo es autocontenido: se copia a la carpeta del trabajo, el agente
edita `draw()` y `diagram_render` lo ejecuta. La imagen se publica junto al AVIF
en `source/` del repositorio BlogImages, así que debe poder ejecutarse solo con
Pillow:

    python3 source.py            # escribe out.png
    DIAGRAM_OUT=versions/v1.png python3 source.py

Ubicación recomendada: "Abajo del texto «Una vez que el embudo genera \"pero\", esta nueva gota se une al grupo»."
Contenido recomendado: "Muestra el bucle generativo: cada palabra predicha se añade a la secuencia, toda la secuencia vuelve a pasar por el modelo y el proceso se repite hasta el token de fin; el velo causal impide mirar las posiciones futuras.\nComponentes: tarjeta «Secuencia actual» con cinco píldoras («El», «perro», «ladra», «fuerte», «pero»); tarjeta «Transformer (decodificador)» a la derecha; tarjeta «Nueva palabra predicha» con dos posibilidades («no», «es»); tarjeta de condición de parada «Token de fin de secuencia»; tarjeta-escudo «Máscara causal» adosada al modelo; flecha circular de retorno que cierra el bucle.\nEstilo: estilo oscuro de la casa; fondo #0B0F19, tarjetas #0F172A, texto principal #E2E8F0 y secundario #94A3B8; secuencia en cian #22D3EE, modelo en cian suave #38BDF8, escudo/máscara en rojo #F87171, token de fin en verde #34D399, bucle en ámbar #F59E0B; DejaVu Sans, título 52 px, cuerpo 24 px; flechas de 4 px con cabeza triangular.\nPosicionamiento: disposición circular en sentido horario; «Secuencia actual» arriba a la izquierda, «Transformer» arriba a la derecha, «Nueva palabra predicha» abajo a la derecha y «Token de fin» abajo a la izquierda; la flecha de retorno sube por la izquierda desde la nueva palabra hacia la secuencia; la máscara causal se dibuja pegada al modelo con dos flechas tachadas hacia dos huecos futuros «?».\nTextos en la imagen: título «Generar, añadir y repetir»; subtítulo «Un bucle hasta el token de fin»; etiquetas «Secuencia actual», «El», «perro», «ladra», «fuerte», «pero», «Transformer (decodificador)», «Nueva palabra predicha», «no», «es», «Máscara causal: solo ve el pasado», «Token de fin de secuencia»; leyendas «⟳ el ciclo se repite» y «✕ prohibido mirar el futuro»."

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
TITLE = "Ciclo autorregresivo con velo causal"
LOCATION = "Abajo del texto «Una vez que el embudo genera \"pero\", esta nueva gota se une al grupo»."
CONTENT = "Muestra el bucle generativo: cada palabra predicha se añade a la secuencia, toda la secuencia vuelve a pasar por el modelo y el proceso se repite hasta el token de fin; el velo causal impide mirar las posiciones futuras.\nComponentes: tarjeta «Secuencia actual» con cinco píldoras («El», «perro», «ladra», «fuerte», «pero»); tarjeta «Transformer (decodificador)» a la derecha; tarjeta «Nueva palabra predicha» con dos posibilidades («no», «es»); tarjeta de condición de parada «Token de fin de secuencia»; tarjeta-escudo «Máscara causal» adosada al modelo; flecha circular de retorno que cierra el bucle.\nEstilo: estilo oscuro de la casa; fondo #0B0F19, tarjetas #0F172A, texto principal #E2E8F0 y secundario #94A3B8; secuencia en cian #22D3EE, modelo en cian suave #38BDF8, escudo/máscara en rojo #F87171, token de fin en verde #34D399, bucle en ámbar #F59E0B; DejaVu Sans, título 52 px, cuerpo 24 px; flechas de 4 px con cabeza triangular.\nPosicionamiento: disposición circular en sentido horario; «Secuencia actual» arriba a la izquierda, «Transformer» arriba a la derecha, «Nueva palabra predicha» abajo a la derecha y «Token de fin» abajo a la izquierda; la flecha de retorno sube por la izquierda desde la nueva palabra hacia la secuencia; la máscara causal se dibuja pegada al modelo con dos flechas tachadas hacia dos huecos futuros «?».\nTextos en la imagen: título «Generar, añadir y repetir»; subtítulo «Un bucle hasta el token de fin»; etiquetas «Secuencia actual», «El», «perro», «ladra», «fuerte», «pero», «Transformer (decodificador)», «Nueva palabra predicha», «no», «es», «Máscara causal: solo ve el pasado», «Token de fin de secuencia»; leyendas «⟳ el ciclo se repite» y «✕ prohibido mirar el futuro»."
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


def dashed_line(draw: ImageDraw.ImageDraw, start, end, color, width: int = 3,
                dash: int = 12, gap: int = 8) -> None:
    """Línea discontinua entre dos puntos."""
    shade = rgb(color) if isinstance(color, str) else color
    x1, y1 = start
    x2, y2 = end
    length = math.hypot(x2 - x1, y2 - y1)
    if length <= 0:
        return
    ux, uy = (x2 - x1) / length, (y2 - y1) / length
    pos = 0.0
    while pos < length:
        stop = min(pos + dash, length)
        draw.line((x1 + ux * pos, y1 + uy * pos, x1 + ux * stop, y1 + uy * stop),
                  fill=shade, width=width)
        pos += dash + gap


def dashed_box(draw: ImageDraw.ImageDraw, xy, color, width: int = 3,
               dash: int = 9, gap: int = 7) -> None:
    """Rectángulo discontinuo."""
    x0, y0, x1, y1 = xy
    dashed_line(draw, (x0, y0), (x1, y0), color, width, dash, gap)
    dashed_line(draw, (x1, y0), (x1, y1), color, width, dash, gap)
    dashed_line(draw, (x1, y1), (x0, y1), color, width, dash, gap)
    dashed_line(draw, (x0, y1), (x0, y0), color, width, dash, gap)


def cross_mark(draw: ImageDraw.ImageDraw, cx: float, cy: float, size: int = 11,
               color: str = RED, width: int = 4) -> None:
    """Cruz de prohibición."""
    draw.line((cx - size, cy - size, cx + size, cy + size), fill=rgb(color), width=width)
    draw.line((cx - size, cy + size, cx + size, cy - size), fill=rgb(color), width=width)


def loop_mark(draw: ImageDraw.ImageDraw, cx: float, cy: float, r: int = 13,
              color: str = AMBER, width: int = 3) -> None:
    """Icono de ciclo: arco abierto con punta de flecha."""
    draw.arc((cx - r, cy - r, cx + r, cy + r), start=35, end=310, fill=rgb(color), width=width)
    angle = math.radians(310)
    tip = (cx + r * math.cos(angle), cy + r * math.sin(angle))
    tangent = (-math.sin(angle), math.cos(angle))
    normal = (math.cos(angle), math.sin(angle))
    base = (tip[0] - tangent[0] * 14, tip[1] - tangent[1] * 14)
    left = (base[0] + normal[0] * 7, base[1] + normal[1] * 7)
    right = (base[0] - normal[0] * 7, base[1] - normal[1] * 7)
    draw.polygon([tip, left, right], fill=rgb(color))


def draw() -> Image.Image:
    """Compón el diagrama. Devuelve la imagen final."""
    image, canvas = new_canvas()

    # ---------------------------------------------------------------- cabecera
    canvas.text((MARGIN, 54), "Generar, añadir y repetir",
                font=font(54, bold=True), fill=rgb(TEXT))
    canvas.text((MARGIN, 128), "Un bucle hasta el token de fin",
                font=font(26), fill=rgb(MUTED))
    canvas.line((MARGIN, 184, W - MARGIN, 184), fill=rgb(LINE), width=2)

    # ------------------------------------------------------- secuencia actual
    rounded_box(canvas, (150, 236, 800, 446), radius=22, fill=CARD, outline=LINE)
    canvas.rounded_rectangle((150, 236, 158, 446), radius=4, fill=rgb(CYAN))
    canvas.text((182, 258), "Secuencia actual", font=font(30, bold=True), fill=rgb(TEXT))
    canvas.text((182, 300), "tokens ya generados", font=font(19), fill=rgb(FAINT))
    tokens = ["El", "perro", "ladra", "fuerte", "pero"]
    token_w, token_y = 110, 338
    for i, token in enumerate(tokens):
        x = 182 + i * 119
        rounded_box(canvas, (x, token_y, x + token_w, token_y + 54), radius=27,
                    fill=CARD_RAISED, outline=CYAN, width=2)
        text_center(canvas, x + token_w / 2, token_y + 11, token, font(26, bold=True), TEXT)

    # ------------------------------------------------------------- transformer
    rounded_box(canvas, (1000, 236, 1690, 446), radius=22, fill=CARD, outline=LINE)
    canvas.rounded_rectangle((1000, 236, 1008, 446), radius=4, fill=rgb(CYAN_SOFT))
    canvas.text((1032, 258), "Transformer (decodificador)",
                font=font(30, bold=True), fill=rgb(TEXT))
    draw_text_block(canvas, 1032, 302,
                    "Lee la secuencia y predice la siguiente palabra.",
                    font(21), MUTED, max_width=600)
    # pila de capas decorativa
    for i in range(3):
        bar_y = 366 + i * 23
        canvas.rounded_rectangle((1032, bar_y, 1032 + 240 - i * 26, bar_y + 13),
                                 radius=6, fill=mix(CYAN_SOFT, BG, 0.55 - i * 0.12))
    canvas.text((1300, 376), "capas del modelo", font=font(18), fill=rgb(FAINT))

    # -------------------------------------------------- nueva palabra predicha
    rounded_box(canvas, (1000, 766, 1690, 976), radius=22, fill=CARD, outline=LINE)
    canvas.rounded_rectangle((1000, 766, 1008, 976), radius=4, fill=rgb(AMBER))
    canvas.text((1032, 788), "Nueva palabra predicha",
                font=font(30, bold=True), fill=rgb(TEXT))
    for i, candidate in enumerate(["no", "es"]):
        x = 1032 + i * 126
        rounded_box(canvas, (x, 838, x + 110, 892), radius=27,
                    fill=CARD_RAISED, outline=AMBER, width=2)
        text_center(canvas, x + 55, 851, candidate, font(26, bold=True), AMBER)
    canvas.text((1306, 852), "se añade a la secuencia", font=font(19), fill=rgb(MUTED))

    # ------------------------------------------------- token de fin de secuencia
    rounded_box(canvas, (150, 766, 800, 976), radius=22, fill=CARD, outline=LINE)
    canvas.rounded_rectangle((150, 766, 158, 976), radius=4, fill=rgb(GREEN))
    canvas.text((182, 788), "Token de fin de secuencia",
                font=font(30, bold=True), fill=rgb(TEXT))
    badge(canvas, 182, 840, "fin", fill=GREEN, text_color=BG, size=20)
    canvas.text((276, 844), "detiene el bucle", font=font(19), fill=rgb(MUTED))
    canvas.text((182, 898), "<fin>", font=font(28, bold=True), fill=rgb(GREEN))

    # ------------------------------------------------------ flechas del bucle
    loop = AMBER
    arrow(canvas, (806, 341), (994, 341), color=loop, width=4, head=20)    # TL -> TR
    arrow(canvas, (1345, 450), (1345, 762), color=loop, width=4, head=20)  # TR -> BR
    arrow(canvas, (994, 871), (806, 871), color=loop, width=4, head=20)    # BR -> BL
    arrow(canvas, (475, 762), (475, 450), color=loop, width=4, head=20)    # BL -> TL

    draw_text_block(canvas, 182, 470,
                    "Cada vuelta añade una palabra y recalcula el contexto.",
                    font(21), MUTED, max_width=268)
    loop_mark(canvas, 516, 584, r=13, color=AMBER, width=3)
    canvas.text((542, 572), "el ciclo se repite", font=font(21), fill=rgb(AMBER))

    # ----------------------------------------------------------- máscara causal
    rounded_box(canvas, (850, 452, 1100, 592), radius=18, fill=CARD, outline=LINE)
    canvas.rounded_rectangle((850, 452, 856, 592), radius=4, fill=rgb(RED))
    canvas.text((870, 470), "Máscara causal", font=font(20, bold=True), fill=rgb(RED))
    canvas.text((870, 504), "solo ve el pasado", font=font(18), fill=rgb(MUTED))
    canvas.text((870, 530), "nunca el futuro", font=font(18), fill=rgb(MUTED))
    canvas.text((850, 606), "adosada al modelo", font=font(17), fill=rgb(FAINT))

    future_boxes = [(462, 524), (530, 592)]
    for (top, bottom) in future_boxes:
        dashed_box(canvas, (1140, top, 1202, bottom), FAINT, width=3, dash=8, gap=6)
        text_center(canvas, 1171, top + 8, "?", font(24, bold=True), FAINT)
        mid = (top + bottom) // 2
        arrow(canvas, (1104, mid), (1134, mid), color=FAINT, width=3, head=9)
        cross_mark(canvas, 1119, mid, size=11, color=RED, width=3)

    # ---------------------------------------------------------------- leyenda
    cross_mark(canvas, 162, 1066, size=12, color=RED, width=4)
    canvas.text((188, 1052), "prohibido mirar el futuro", font=font(22), fill=rgb(MUTED))
    canvas.ellipse((1024, 1058, 1040, 1074), fill=rgb(CARD))
    canvas.ellipse((1024, 1058, 1040, 1074), outline=rgb(GREEN), width=3)
    canvas.text((1056, 1052), "el token de fin cierra el bucle", font=font(22), fill=rgb(MUTED))

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

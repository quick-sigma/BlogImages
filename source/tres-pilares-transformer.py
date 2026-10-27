""""Los tres pilares del Transformer"

Diagrama propuesto por el estudio de diagramas a partir de una recomendación del
blog. Este archivo es autocontenido: se copia a la carpeta del trabajo, el agente
edita `draw()` y `diagram_render` lo ejecuta. La imagen se publica junto al AVIF
en `source/` del repositorio BlogImages, así que debe poder ejecutarse solo con
Pillow:

    python3 source.py            # escribe out.png
    DIAGRAM_OUT=versions/v1.png python3 source.py

Ubicación recomendada: "Debajo del encabezado «Los Tres Pilares Ocultos del Transformer»."
Contenido recomendado: "Resume los tres mecanismos de ingeniería que evitan que el Transformer profundo colapse, cada uno con su símil del blog.\nComponentes: tres tarjetas-columna: «Conexiones residuales (El cable de emergencia)» con una línea que salta una capa; «Normalización de capa (El ecualizador)» con una señal antes y después de reajustarse; «Codificación posicional (El GPS de ondas)» con ondas seno y coseno sobre tres posiciones; una franja inferior «Información estable en cada piso»; insignia «Hasta 90 capas».\nEstilo: estilo oscuro de la casa; fondo #0B0F19, tarjetas #0F172A con barra de acento superior; residual en cian #22D3EE, normalización en verde #34D399, posicional en ámbar #F59E0B; DejaVu Sans, título 48 px, títulos de tarjeta 26 px en negrita, cuerpo 21 px; iconos de línea fina en #94A3B8 dentro de cada tarjeta.\nPosicionamiento: tres columnas de igual ancho en una sola fila, de izquierda a derecha en el orden del blog; cada tarjeta con su icono arriba, el título, dos líneas de explicación y el símil entre paréntesis; la franja inferior cruza las tres columnas como conclusión; título general y subtítulo arriba.\nTextos en la imagen: título «Los tres pilares ocultos»; subtítulo «Cómo no colapsa un Transformer profundo»; títulos «Conexiones residuales», «Normalización de capa», «Codificación posicional»; símiles «El cable de emergencia», «El ecualizador», «El GPS de ondas»; etiquetas «la información original nunca se pierde», «media 0, desviación 1», «distancias relativas con seno y coseno», «Hasta 90 capas»."

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
TITLE = "Los tres pilares del Transformer"
LOCATION = "Debajo del encabezado «Los Tres Pilares Ocultos del Transformer»."
CONTENT = "Resume los tres mecanismos de ingeniería que evitan que el Transformer profundo colapse, cada uno con su símil del blog.\nComponentes: tres tarjetas-columna: «Conexiones residuales (El cable de emergencia)» con una línea que salta una capa; «Normalización de capa (El ecualizador)» con una señal antes y después de reajustarse; «Codificación posicional (El GPS de ondas)» con ondas seno y coseno sobre tres posiciones; una franja inferior «Información estable en cada piso»; insignia «Hasta 90 capas».\nEstilo: estilo oscuro de la casa; fondo #0B0F19, tarjetas #0F172A con barra de acento superior; residual en cian #22D3EE, normalización en verde #34D399, posicional en ámbar #F59E0B; DejaVu Sans, título 48 px, títulos de tarjeta 26 px en negrita, cuerpo 21 px; iconos de línea fina en #94A3B8 dentro de cada tarjeta.\nPosicionamiento: tres columnas de igual ancho en una sola fila, de izquierda a derecha en el orden del blog; cada tarjeta con su icono arriba, el título, dos líneas de explicación y el símil entre paréntesis; la franja inferior cruza las tres columnas como conclusión; título general y subtítulo arriba.\nTextos en la imagen: título «Los tres pilares ocultos»; subtítulo «Cómo no colapsa un Transformer profundo»; títulos «Conexiones residuales», «Normalización de capa», «Codificación posicional»; símiles «El cable de emergencia», «El ecualizador», «El GPS de ondas»; etiquetas «la información original nunca se pierde», «media 0, desviación 1», «distancias relativas con seno y coseno», «Hasta 90 capas»."
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
    canvas.text((MARGIN, 54), "Los tres pilares ocultos",
                font=font(48, bold=True), fill=rgb(TEXT))
    canvas.text((MARGIN, 120), "Cómo no colapsa un Transformer profundo",
                font=font(24), fill=rgb(MUTED))
    canvas.line((MARGIN, 172, W - MARGIN, 172), fill=rgb(LINE), width=2)
    badge(canvas, 1300, 194, "Hasta 90 capas", fill=AMBER, text_color=BG, size=19)

    cards = [(90, 590, CYAN), (650, 1150, GREEN), (1210, 1710, AMBER)]
    titles = ["Conexiones residuales", "Normalización de capa", "Codificación posicional"]
    metaphors = ["(El cable de emergencia)", "(El ecualizador)", "(El GPS de ondas)"]
    bodies = [
        "La entrada de una capa salta directamente a su salida y se suma al resultado.",
        "Calcula la media y la desviación de cada vector y lo reajusta a media 0 y desviación 1.",
        "Suma a cada palabra un vector de posición hecho de ondas seno y coseno.",
    ]
    consequences = [
        "Sin ella, la información se diluye capa tras capa.",
        "Sin ella, los valores se apagan o saturan.",
        "Sin ella, el orden de las palabras se pierde.",
    ]

    for index, (x0, x1, accent) in enumerate(cards):
        cy = (x0 + x1) // 2
        rounded_box(canvas, (x0, 250, x1, 890), radius=22, fill=CARD, outline=LINE)
        canvas.rounded_rectangle((x0, 250, x0 + 8, 890), radius=4, fill=rgb(accent))
        canvas.text((x0 + 40, 486), titles[index], font=font(26, bold=True), fill=rgb(TEXT))
        canvas.text((x0 + 40, 528), metaphors[index], font=font(21), fill=rgb(FAINT))
        draw_text_block(canvas, x0 + 40, 574, bodies[index], font(20), MUTED, max_width=420)
        canvas.line((x0 + 40, 745, x1 - 40, 745), fill=rgb(LINE), width=2)
        draw_text_block(canvas, x0 + 40, 763, consequences[index], font(19), FAINT, max_width=420)

        # ------------------------------------------------------------- iconos
        if index == 0:
            # cable que salta una capa y se suma
            canvas.rounded_rectangle((cy - 50, 350, cy + 50, 398), radius=10,
                                     fill=rgb(CARD_RAISED), outline=rgb(LINE), width=2)
            text_center(canvas, cy, 362, "capa", font(15), MUTED)
            canvas.line((cy - 185, 374, cy - 52, 374), fill=rgb(MUTED), width=3)
            canvas.line((cy + 52, 374, cy + 92, 374), fill=rgb(MUTED), width=3)
            canvas.line((cy - 185, 374, cy - 185, 314), fill=rgb(accent), width=3)
            canvas.line((cy - 185, 314, cy + 108, 314), fill=rgb(accent), width=3)
            canvas.line((cy + 108, 314, cy + 108, 360), fill=rgb(accent), width=3)
            canvas.ellipse((cy + 94, 360, cy + 122, 388), fill=rgb(BG), outline=rgb(accent), width=3)
            text_center(canvas, cy + 108, 366, "+", font(17, bold=True), accent)
            arrow(canvas, (cy + 122, 374), (cy + 185, 374), color=accent, width=3, head=11)
        elif index == 1:
            # señal caótica -> señal estable
            zig = [(cy - 190 + i * 16, 360 + (28 if i % 2 == 0 else -28)) for i in range(9)]
            canvas.line(zig, fill=rgb(MUTED), width=3, joint="curve")
            canvas.line((cy - 56, 360, cy - 22, 360), fill=rgb(MUTED), width=3)
            arrow(canvas, (cy - 30, 360), (cy - 4, 360), color=accent, width=3, head=10)
            flat = [(cy + 16 + i * 18, 360 + (6 if i % 2 == 0 else -6)) for i in range(9)]
            canvas.line(flat, fill=rgb(accent), width=3, joint="curve")
            canvas.text((cy - 178, 392), "antes", font=font(15), fill=rgb(FAINT))
            canvas.text((cy + 128, 392), "después", font=font(15), fill=rgb(FAINT))
            text_center(canvas, cy + 20, 420, "media 0 · desv. 1", font(14), MUTED)
        else:
            # ondas seno y coseno sobre las posiciones
            sin_pts = [(1270 + i * 4, 356 + 26 * math.sin((1270 + i * 4 - 1270) / 46)) for i in range(96)]
            cos_pts = [(1270 + i * 4, 356 + 15 * math.cos((1270 + i * 4 - 1270) / 46)) for i in range(96)]
            canvas.line(sin_pts, fill=rgb(accent), width=3, joint="curve")
            canvas.line(cos_pts, fill=mix(AMBER, BG, 0.45), width=3, joint="curve")
            canvas.line((1270, 404, 1660, 404), fill=rgb(LINE), width=2)
            for dot, label in zip((1300, 1460, 1620), ("1", "2", "3")):
                canvas.ellipse((dot - 5, 399, dot + 5, 409), fill=rgb(accent))
                text_center(canvas, dot, 414, label, font(15), FAINT)

    # ------------------------------------------------------------ franja final
    rounded_box(canvas, (90, 930, 1710, 1070), radius=22, fill=CARD, outline=LINE)
    canvas.rounded_rectangle((90, 930, 98, 1070), radius=4, fill=rgb(CYAN))
    text_center(canvas, 900, 976, "Información estable en cada piso",
                font(30, bold=True), TEXT)
    text_center(canvas, 900, 1024, "residual + normalización + posición, capa tras capa",
                font(19), MUTED)

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

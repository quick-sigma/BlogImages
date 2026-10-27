""""Cascada de gotas del Transformer"

Diagrama propuesto por el estudio de diagramas a partir de una recomendación del
blog. Este archivo es autocontenido: se copia a la carpeta del trabajo, el agente
edita `draw()` y `diagram_render` lo ejecuta. La imagen se publica junto al AVIF
en `source/` del repositorio BlogImages, así que debe poder ejecutarse solo con
Pillow:

    python3 source.py            # escribe out.png
    DIAGRAM_OUT=versions/v1.png python3 source.py

Ubicación recomendada: "Abajo del texto «Imagina la palabra \"El\" como una gota de agua que cae por una montaña de cristal»."
Contenido recomendado: "Metáfora central de la sección: cuatro gotas descienden por los niveles de la montaña de cristal, se miran entre sí mediante espejos (auto-atención) y al pie un embudo predice la siguiente palabra mientras un velo le oculta el futuro.\nComponentes: cuatro píldoras-gota («El», «perro», «ladra», «fuerte») arriba; tres tarjetas de capa apiladas («Nivel 1», «Nivel 2», «Nivel N») con un icono de espejo y la etiqueta «Auto-atención»; flechas cruzadas entre las gotas dentro de cada nivel; una tarjeta de embudo «Embudo de predicción» al pie; una tarjeta de salida «pero» bajo el embudo; un escudo lateral «Velo causal».\nEstilo: estilo oscuro de la casa; fondo #0B0F19, tarjetas #0F172A con barra de acento a la izquierda; gotas en cian #22D3EE, flechas de atención en ámbar #F59E0B, embudo en cian suave #38BDF8, escudo en rojo #F87171; DejaVu Sans, título 52 px en negrita, cuerpo 24 px; lienzo 1800×1200, margen 90 px, radio de tarjeta 18 px, líneas de 4 px.\nPosicionamiento: flujo vertical de arriba abajo; título y subtítulo arriba con línea divisoria; las cuatro gotas en fila superior; debajo, las tres capas apiladas y conectadas con flechas verticales; el embudo centrado al pie y la salida «pero» justo debajo; el escudo del velo a la derecha del embudo, con línea punteada hacia un hueco vacío «?» que representa el futuro.\nTextos en la imagen: título «La montaña de cristal del Transformer»; subtítulo «Las gotas bajan, se miran y acumulan contexto»; etiquetas «El», «perro», «ladra», «fuerte», «Nivel 1», «Nivel 2», «Nivel N», «Auto-atención», «Embudo de predicción», «Velo causal: no ve el futuro», «pero»; leyenda «→ flujo de información»."

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
TITLE = "Cascada de gotas del Transformer"
LOCATION = "Abajo del texto «Imagina la palabra \"El\" como una gota de agua que cae por una montaña de cristal»."
CONTENT = "Metáfora central de la sección: cuatro gotas descienden por los niveles de la montaña de cristal, se miran entre sí mediante espejos (auto-atención) y al pie un embudo predice la siguiente palabra mientras un velo le oculta el futuro.\nComponentes: cuatro píldoras-gota («El», «perro», «ladra», «fuerte») arriba; tres tarjetas de capa apiladas («Nivel 1», «Nivel 2», «Nivel N») con un icono de espejo y la etiqueta «Auto-atención»; flechas cruzadas entre las gotas dentro de cada nivel; una tarjeta de embudo «Embudo de predicción» al pie; una tarjeta de salida «pero» bajo el embudo; un escudo lateral «Velo causal».\nEstilo: estilo oscuro de la casa; fondo #0B0F19, tarjetas #0F172A con barra de acento a la izquierda; gotas en cian #22D3EE, flechas de atención en ámbar #F59E0B, embudo en cian suave #38BDF8, escudo en rojo #F87171; DejaVu Sans, título 52 px en negrita, cuerpo 24 px; lienzo 1800×1200, margen 90 px, radio de tarjeta 18 px, líneas de 4 px.\nPosicionamiento: flujo vertical de arriba abajo; título y subtítulo arriba con línea divisoria; las cuatro gotas en fila superior; debajo, las tres capas apiladas y conectadas con flechas verticales; el embudo centrado al pie y la salida «pero» justo debajo; el escudo del velo a la derecha del embudo, con línea punteada hacia un hueco vacío «?» que representa el futuro.\nTextos en la imagen: título «La montaña de cristal del Transformer»; subtítulo «Las gotas bajan, se miran y acumulan contexto»; etiquetas «El», «perro», «ladra», «fuerte», «Nivel 1», «Nivel 2», «Nivel N», «Auto-atención», «Embudo de predicción», «Velo causal: no ve el futuro», «pero»; leyenda «→ flujo de información»."
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
                dash: int = 14, gap: int = 9) -> None:
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
               dash: int = 10, gap: int = 8) -> None:
    """Rectángulo discontinuo."""
    x0, y0, x1, y1 = xy
    dashed_line(draw, (x0, y0), (x1, y0), color, width, dash, gap)
    dashed_line(draw, (x1, y0), (x1, y1), color, width, dash, gap)
    dashed_line(draw, (x1, y1), (x0, y1), color, width, dash, gap)
    dashed_line(draw, (x0, y1), (x0, y0), color, width, dash, gap)


def mesh(draw: ImageDraw.ImageDraw, points, color, width: int = 3,
         radius: int = 8, dot: str = CYAN) -> None:
    """Malla de líneas entre puntos y nodos redondos."""
    shade = rgb(color) if isinstance(color, str) else color
    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            draw.line((points[i], points[j]), fill=shade, width=width)
    for x, y in points:
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=rgb(dot))


def shield(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, color: str = RED) -> None:
    """Escudo de contorno con una cruz interior."""
    points = [(x, y), (x + w, y), (x + w, y + h * 0.55), (x + w / 2, y + h), (x, y + h * 0.55)]
    draw.polygon(points, fill=mix(color, BG, 0.86))
    draw.line(points + [points[0]], fill=rgb(color), width=4, joint="curve")
    cx, cy = x + w / 2, y + h / 2
    draw.line((cx - 12, cy - 12, cx + 12, cy + 12), fill=rgb(color), width=4)
    draw.line((cx - 12, cy + 12, cx + 12, cy - 12), fill=rgb(color), width=4)


def draw() -> Image.Image:
    """Compón el diagrama. Devuelve la imagen final."""
    image, canvas = new_canvas()

    # ---------------------------------------------------------------- cabecera
    canvas.text((MARGIN, 54), "La montaña de cristal del Transformer",
                font=font(54, bold=True), fill=rgb(TEXT))
    canvas.text((MARGIN, 130), "Las gotas bajan, se miran y acumulan contexto",
                font=font(26), fill=rgb(MUTED))
    canvas.line((MARGIN, 186, W - MARGIN, 186), fill=rgb(LINE), width=2)

    # ------------------------------------------------------------------ gotas
    lanes = [430, 610, 790, 970]
    droplets = ["El", "perro", "ladra", "fuerte"]
    pill_w, pill_h, pill_y = 150, 64, 232
    attention_line = mix(AMBER, BG, 0.5)
    for cx, label in zip(lanes, droplets):
        canvas.polygon([(cx, 202), (cx - 8, 220), (cx + 8, 220)], fill=rgb(CYAN))
        canvas.ellipse((cx - 8, 212, cx + 8, 228), fill=rgb(CYAN))
        rounded_box(canvas, (cx - pill_w // 2, pill_y, cx + pill_w // 2, pill_y + pill_h),
                    radius=pill_h // 2, fill=CARD_RAISED, outline=CYAN, width=2)
        text_center(canvas, cx, pill_y + 14, label, font(30, bold=True), TEXT)

    # ---------------------------------------------------------------- niveles
    card_x, card_w, card_h = 330, 740, 124
    card_tops = [340, 494, 648]
    level_labels = ["Nivel 1", "Nivel 2", "Nivel N"]
    stagger = [[0, 14, 4, 18], [10, 0, 16, 6], [4, 18, 8, 0]]
    for index, top in enumerate(card_tops):
        rounded_box(canvas, (card_x, top, card_x + card_w, top + card_h),
                    radius=20, fill=CARD, outline=LINE)
        canvas.rounded_rectangle((card_x, top, card_x + 8, top + card_h), radius=4, fill=rgb(CYAN))
        canvas.text((150, top + 16), level_labels[index], font=font(36, bold=True), fill=rgb(TEXT))
        canvas.text((150, top + 66), "Auto-atención", font=font(21), fill=rgb(MUTED))
        center_y = top + card_h // 2
        points = [(cx, center_y + dy) for cx, dy in zip(lanes, stagger[index])]
        mesh(canvas, points, attention_line, width=3, radius=9)

    # flechas de flujo entre bloques
    flow = CYAN_SOFT
    for cx in lanes:
        arrow(canvas, (cx, 298), (cx, 336), color=flow, width=3, head=10)
        arrow(canvas, (cx, 466), (cx, 490), color=flow, width=3, head=10)
        arrow(canvas, (cx, 620), (cx, 644), color=flow, width=3, head=10)
        arrow(canvas, (cx, 774), (cx, 800), color=flow, width=3, head=10)

    # ---------------------------------------------------------------- embudo
    funnel = [(400, 800), (1000, 800), (840, 970), (560, 970)]
    canvas.polygon(funnel, fill=rgb(CARD))
    canvas.line(funnel + [funnel[0]], fill=rgb(CYAN_SOFT), width=4, joint="curve")
    text_center(canvas, 700, 822, "Embudo de predicción", font(30, bold=True), TEXT)
    text_center(canvas, 700, 876, "analiza el rastro completo", font(20), MUTED)

    # ---------------------------------------------------------------- salida
    arrow(canvas, (700, 972), (700, 990), color=AMBER, width=4, head=12)
    rounded_box(canvas, (600, 994, 800, 1048), radius=27, fill=CARD_RAISED, outline=CYAN, width=2)
    text_center(canvas, 700, 1007, "pero", font(31, bold=True), CYAN)

    # ------------------------------------------------- hueco del futuro + velo
    dashed_box(canvas, (952, 864, 1032, 944), FAINT, width=3, dash=10, gap=8)
    text_center(canvas, 992, 874, "?", font(40, bold=True), FAINT)
    text_center(canvas, 992, 952, "futuro", font(18), FAINT)
    dashed_line(canvas, (1166, 904), (1046, 904), RED, width=3)
    canvas.polygon([(1042, 904), (1054, 896), (1054, 912)], fill=rgb(RED))

    # --------------------------------------------------------------- panel A
    px, pw = 1170, 530
    rounded_box(canvas, (px, 232, px + pw, 676), radius=22, fill=CARD, outline=LINE)
    canvas.rounded_rectangle((px, 232, px + 8, 676), radius=4, fill=rgb(CYAN))
    canvas.text((px + 32, 256), "Auto-atención", font=font(32, bold=True), fill=rgb(CYAN))
    canvas.line((px + 32, 302, px + pw - 32, 302), fill=rgb(LINE), width=2)

    mx, my, mw, mh = px + 34, 322, 72, 104
    canvas.rounded_rectangle((mx, my, mx + mw, my + mh), radius=10,
                             fill=rgb(CARD_RAISED), outline=rgb(CYAN), width=3)
    canvas.line((mx + 14, my + mh - 8, mx + mw - 14, my + 8), fill=rgb(CYAN_SOFT), width=3)
    canvas.line((mx + 14, my + mh - 34, mx + mw - 34, my + 8), fill=rgb("#155E75"), width=2)
    canvas.line((mx + mw // 2, my + mh, mx + mw // 2, my + mh + 18), fill=rgb(CYAN), width=3)
    canvas.line((mx + 14, my + mh + 18, mx + mw - 14, my + mh + 18), fill=rgb(CYAN), width=3)

    draw_text_block(canvas, px + 128, 324,
                    "En cada nivel las gotas se miran entre sí a través de los espejos. "
                    "Cada gota absorbe información contextual de las demás.",
                    font(22), MUTED, max_width=360)
    canvas.text((px + 32, 486), "«El» descubre que está cerca de «perro».",
                font=font(22), fill=rgb(FAINT))

    mirror_mesh = [(px + 70 + i * 112, 606 + dy) for i, dy in enumerate([0, 12, 4, 16])]
    mesh(canvas, mirror_mesh, attention_line, width=3, radius=7)

    # --------------------------------------------------------------- panel B
    rounded_box(canvas, (px, 700, px + pw, 1030), radius=22, fill=CARD, outline=LINE)
    canvas.rounded_rectangle((px, 700, px + 8, 1030), radius=4, fill=rgb(RED))
    canvas.text((px + 32, 722), "Velo causal", font=font(32, bold=True), fill=rgb(RED))
    canvas.text((px + 32, 764), "no ve el futuro", font=font(21), fill=rgb(FAINT))
    shield(canvas, px + 36, 802, 72, 88)
    draw_text_block(canvas, px + 128, 800,
                    "Solo ve las gotas que ya cayeron. Nunca las que caerán.",
                    font(22), MUTED, max_width=360)

    # mini leyenda pasado / futuro dentro del panel
    for i in range(4):
        dot_x = px + 44 + i * 28
        canvas.ellipse((dot_x - 6, 968, dot_x + 6, 980), fill=rgb(CYAN))
    canvas.text((px + 160, 960), "cayeron", font=font(18), fill=rgb(MUTED))
    dashed_box(canvas, (px + 268, 956, px + 300, 988), FAINT, width=2, dash=6, gap=5)
    text_center(canvas, px + 284, 960, "?", font(16, bold=True), FAINT)
    canvas.text((px + 312, 960), "futuro", font=font(18), fill=rgb(FAINT))

    # ---------------------------------------------------------------- leyenda
    arrow(canvas, (150, 1112), (226, 1112), color=CYAN_SOFT, width=4, head=12)
    canvas.text((242, 1098), "flujo de información", font=font(21), fill=rgb(MUTED))
    arrow(canvas, (520, 1112), (596, 1112), color=AMBER, width=4, head=12)
    canvas.text((612, 1098), "atención entre gotas", font=font(21), fill=rgb(MUTED))

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

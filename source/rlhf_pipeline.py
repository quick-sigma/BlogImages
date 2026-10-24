# pip install Pillow
"""
El pipeline de alineación RLHF en tres etapas.

Diagrama de flujo horizontal con tres tarjetas (SFT, Reward Model y PPO + KL),
cada una con su icono, su descripción y su output. Las flechas gruesas y el
degradado azul -> amarillo -> rojo conectan las etapas.

Salida: images/rlhf_pipeline.avif  (1800 x 1030, RGB, calidad 92)
        images/rlhf_pipeline_animated.avif  (900 x 515, 32 frames)
"""

from pathlib import Path
import math

from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ---------------------------------------------------------------------------
# 1. Lienzo y sistema de diseño
# ---------------------------------------------------------------------------
W, H = 1800, 1030

BG = "#060A12"
TEXT = "#E7EEF7"
MUTED = "#9FB0C7"
BODY = "#C7D2E0"
SLATE = "#64748B"
LINE = "#16233A"

BLUE = "#3B82F6"
BLUE_LIGHT = "#93C5FD"
YELLOW = "#FACC15"
YELLOW_LIGHT = "#FEF08A"
RED = "#EF4444"
RED_LIGHT = "#FCA5A5"

WHITE = "#F8FAFC"


def rgb(hex_color):
    """Convierte #RRGGBB en una tupla RGB."""
    value = hex_color.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def mix(c1, c2, t):
    """Interpola linealmente dos colores RGB."""
    t = max(0.0, min(1.0, t))
    return tuple(round(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


BG_RGB = rgb(BG)
TEXT_RGB = rgb(TEXT)
MUTED_RGB = rgb(MUTED)
BODY_RGB = rgb(BODY)
SLATE_RGB = rgb(SLATE)
LINE_RGB = rgb(LINE)

BLUE_RGB = rgb(BLUE)
BLUE_LIGHT_RGB = rgb(BLUE_LIGHT)
YELLOW_RGB = rgb(YELLOW)
YELLOW_LIGHT_RGB = rgb(YELLOW_LIGHT)
RED_RGB = rgb(RED)
RED_LIGHT_RGB = rgb(RED_LIGHT)
WHITE_RGB = rgb(WHITE)


# ---------------------------------------------------------------------------
# 2. Tipografía
# ---------------------------------------------------------------------------
def load_font(size, bold=False):
    """Usa Arial/Helvetica si existe; si no, una fuente del sistema."""
    candidates = (
        [
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/segoeuib.ttf",
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/Library/Fonts/Arial Bold.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
        if bold
        else [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/Library/Fonts/Arial.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
    )
    for name in candidates:
        if Path(name).exists():
            try:
                return ImageFont.truetype(name, size)
            except OSError:
                pass
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


F_TITLE = load_font(46, bold=True)
F_SUBTITLE = load_font(18)
F_CARD_TITLE = load_font(28, bold=True)
F_CARD_SUB = load_font(20)
F_BODY = load_font(18)
F_OUTPUT_LABEL = load_font(10, bold=True)
F_OUTPUT = load_font(20, bold=True)
F_STAGE_LABEL = load_font(12, bold=True)
F_WATERMARK = load_font(84, bold=True)
F_GLOSSARY = load_font(12)


# ---------------------------------------------------------------------------
# 3. Utilidades de dibujo
# ---------------------------------------------------------------------------
def text_with_shadow(draw, xy, text, font, fill, anchor="la",
                     shadow=(2, 5, 10), offset=(0, 2)):
    """Texto con una sombra sutil para mejorar el contraste."""
    draw.text(
        (xy[0] + offset[0], xy[1] + offset[1]),
        text, font=font, fill=shadow, anchor=anchor,
    )
    draw.text(xy, text, font=font, fill=fill, anchor=anchor)


def vertical_gradient(w, h, top_color, bottom_color):
    """Devuelve una imagen RGBA con un degradado vertical."""
    gradient = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(gradient)
    for y in range(h):
        t = y / max(1, h - 1)
        color = mix(top_color, bottom_color, t)
        gd.line([(0, y), (w, y)], fill=color + (255,))
    return gradient


def sample_stops(stops, t):
    """Muestrea una lista de paradas (posición, color) en t."""
    t = max(0.0, min(1.0, t))
    for i in range(len(stops) - 1):
        p0, c0 = stops[i]
        p1, c1 = stops[i + 1]
        if t <= p1:
            local = (t - p0) / (p1 - p0) if p1 > p0 else 0.0
            return mix(c0, c1, local)
    return stops[-1][1]


def multi_gradient(w, h, stops):
    """Degradado horizontal con varias paradas de color."""
    gradient = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(gradient)
    for x in range(w):
        color = sample_stops(stops, x / max(1, w - 1))
        gd.line([(x, 0), (x, h)], fill=color + (255,))
    return gradient


def gradient_text(image, xy, text, font, stops, x_start, x_end, anchor="lt"):
    """Dibuja texto relleno con un degradado horizontal de varias paradas."""
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).text(xy, text, font=font, fill=255, anchor=anchor)
    grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    for x in range(W):
        t = (x - x_start) / max(1, x_end - x_start)
        color = sample_stops(stops, t)
        gd.line([(x, 0), (x, H)], fill=color + (255,))
    grad.putalpha(mask)
    image.alpha_composite(grad)


def gradient_rule(draw, x0, x1, y, stops, alpha=110):
    """Línea horizontal de 1 px con degradado."""
    for x in range(x0, x1):
        color = sample_stops(stops, (x - x0) / max(1, x1 - x0 - 1))
        draw.point((x, y), fill=color + (alpha,))


def rounded_mask(w, h, radius):
    """Máscara redondeada para recortar degradados."""
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, w - 1, h - 1), radius=radius, fill=255
    )
    return mask


# ---------------------------------------------------------------------------
# 4. Iconos vectoriales (120 x 120)
# ---------------------------------------------------------------------------
def icon_book_hands(art):
    """Libro abierto sostenido por dos manos."""
    d = ImageDraw.Draw(art)

    # Páginas del libro.
    left_page = [(60, 26), (22, 18), (14, 56), (60, 66)]
    right_page = [(60, 26), (98, 18), (106, 56), (60, 66)]
    d.polygon(left_page, fill=(11, 31, 56, 255), outline=BLUE_LIGHT_RGB + (255,))
    d.polygon(right_page, fill=(9, 24, 44, 255), outline=BLUE_LIGHT_RGB + (255,))
    d.line(left_page + [left_page[0]], fill=BLUE_LIGHT_RGB + (255,), width=3)
    d.line(right_page + [right_page[0]], fill=BLUE_LIGHT_RGB + (255,), width=3)
    d.line([(60, 26), (60, 66)], fill=(191, 219, 254, 255), width=3)

    # Renglones de las páginas.
    for i in range(3):
        y = 29 + i * 9
        d.line([(20 + i * 2, y), (54, y + 6)], fill=BLUE_RGB + (170,), width=2)
        d.line([(100 - i * 2, y), (66, y + 6)], fill=BLUE_RGB + (170,), width=2)

    # Manos a los lados, con los dedos sobre las páginas.
    skin = (238, 190, 152, 255)
    skin_light = (255, 219, 186, 255)

    d.ellipse((0, 40, 26, 84), fill=skin, outline=skin_light, width=2)
    for y in (44, 54, 64):
        d.rounded_rectangle((16, y, 40, y + 9), radius=4,
                            fill=skin, outline=skin_light, width=1)
    d.rounded_rectangle((18, 74, 34, 83), radius=4,
                        fill=skin, outline=skin_light, width=1)

    d.ellipse((94, 40, 120, 84), fill=skin, outline=skin_light, width=2)
    for y in (44, 54, 64):
        d.rounded_rectangle((80, y, 104, y + 9), radius=4,
                            fill=skin, outline=skin_light, width=1)
    d.rounded_rectangle((86, 74, 102, 83), radius=4,
                        fill=skin, outline=skin_light, width=1)


def icon_scale(art):
    """Balanza de la justicia, ligeramente inclinada."""
    d = ImageDraw.Draw(art)

    d.rounded_rectangle((36, 102, 84, 108), radius=3,
                        fill=(42, 35, 6, 255), outline=YELLOW_RGB + (255,), width=2)
    d.polygon([(54, 94), (66, 94), (70, 102), (50, 102)],
              fill=(42, 35, 6, 255), outline=YELLOW_RGB + (255,))

    d.line([(60, 94), (60, 26)], fill=YELLOW_RGB + (255,), width=4)
    d.ellipse((54, 18, 66, 30), fill=YELLOW_LIGHT_RGB + (255,),
              outline=YELLOW_RGB + (255,), width=2)

    d.line([(18, 44), (102, 36)], fill=YELLOW_RGB + (255,), width=4)
    d.ellipse((54, 34, 66, 46), fill=YELLOW_LIGHT_RGB + (255,),
              outline=YELLOW_RGB + (255,), width=2)

    # Cadenas.
    d.line([(18, 44), (10, 72)], fill=YELLOW_RGB + (210,), width=2)
    d.line([(18, 44), (26, 72)], fill=YELLOW_RGB + (210,), width=2)
    d.line([(102, 36), (94, 64)], fill=YELLOW_RGB + (210,), width=2)
    d.line([(102, 36), (110, 64)], fill=YELLOW_RGB + (210,), width=2)

    # Platos.
    for box, top_y in (((4, 68, 32, 78), 68), ((88, 60, 116, 70), 60)):
        d.ellipse(box, fill=(42, 35, 6, 255), outline=YELLOW_RGB + (255,), width=2)
        d.line([(box[0], top_y), (box[2], top_y)], fill=YELLOW_LIGHT_RGB + (255,), width=2)
    d.ellipse((14, 66, 22, 72), fill=YELLOW_LIGHT_RGB + (255,))
    d.ellipse((98, 58, 106, 64), fill=YELLOW_LIGHT_RGB + (255,))


def icon_trophy_spring(art):
    """Trofeo sobre un resorte: recompensa contenida por KL."""
    d = ImageDraw.Draw(art)

    gold = (245, 158, 11, 255)
    gold_light = (253, 230, 138, 255)
    gold_dark = (180, 83, 9, 255)
    cyan = (103, 232, 249, 255)
    cyan_dark = (14, 116, 144, 255)

    # Copa.
    cup = [(40, 16), (80, 16), (76, 40), (68, 48), (52, 48), (44, 40)]
    d.polygon(cup, fill=gold, outline=gold_light)
    d.line(cup + [cup[0]], fill=gold_light, width=2)
    d.line([(38, 16), (82, 16)], fill=gold_light, width=3)

    # Asas.
    d.arc((26, 18, 46, 42), 90, 270, fill=gold_light, width=3)
    d.arc((74, 18, 94, 42), 270, 90, fill=gold_light, width=3)

    # Pie y base.
    d.rectangle((56, 48, 64, 58), fill=gold_dark, outline=gold_light, width=1)
    d.rounded_rectangle((46, 58, 74, 64), radius=2,
                        fill=gold_dark, outline=gold_light, width=1)

    # Estrella central.
    star = []
    for i in range(10):
        angle = -math.pi / 2 + i * math.pi / 5
        radius = 7 if i % 2 == 0 else 3
        star.append((60 + radius * math.cos(angle),
                     30 + radius * math.sin(angle)))
    d.polygon(star, fill=(255, 247, 204, 255), outline=gold_light)
    d.line([(48, 22), (54, 22)], fill=(255, 251, 235, 255), width=2)

    # Resorte.
    for i in range(5):
        y = 66 + i * 7
        d.ellipse((44, y, 76, y + 12), outline=cyan, width=2)
    d.rounded_rectangle((44, 104, 76, 110), radius=2,
                        fill=cyan_dark, outline=cyan, width=2)


ICONS = {
    "book": icon_book_hands,
    "scale": icon_scale,
    "trophy": icon_trophy_spring,
}


# ---------------------------------------------------------------------------
# 5. Etapas del pipeline
# ---------------------------------------------------------------------------
STAGE_STOPS = [(0.0, BLUE_RGB), (0.5, YELLOW_RGB), (1.0, RED_RGB)]

STAGES = [
    {
        "number": "01",
        "label": "FASE 1",
        "title": "Fase 1: SFT",
        "subtitle": "(El Aprendiz)",
        "body1": "Humanos escriben respuestas ideales",
        "body2": "→ Modelo imita",
        "output": "Modelo instructivo",
        "color": BLUE_RGB,
        "light": BLUE_LIGHT_RGB,
        "icon": "book",
    },
    {
        "number": "02",
        "label": "FASE 2",
        "title": "Fase 2: Reward Model",
        "subtitle": "(El Juez)",
        "body1": "Humanos rankean respuestas",
        "body2": "→ Modelo pequeño aprende a puntuar",
        "output": "Función de recompensa",
        "color": YELLOW_RGB,
        "light": YELLOW_LIGHT_RGB,
        "icon": "scale",
    },
    {
        "number": "03",
        "label": "FASE 3",
        "title": "Fase 3: PPO + KL",
        "subtitle": "(El Resorte)",
        "body1": "Modelo genera → Juez puntúa",
        "body2": "→ Resorte KL previene reward hacking",
        "output": "Modelo alineado (ChatGPT)",
        "color": RED_RGB,
        "light": RED_LIGHT_RGB,
        "icon": "trophy",
    },
]

CARD_X = (60, 650, 1240)
CARD_Y = 220
CARD_W = 500
CARD_H = 620


# ---------------------------------------------------------------------------
# 6. Fondo
# ---------------------------------------------------------------------------
image = Image.new("RGBA", (W, H), BG_RGB + (255,))
draw = ImageDraw.Draw(image)

# Rejilla de puntos.
for gy in range(28, H - 18, 44):
    for gx in range(28, W - 18, 44):
        draw.ellipse((gx, gy, gx + 2, gy + 2), fill=(16, 27, 43, 255))

# Halos de las tres etapas.
bg_glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
gd = ImageDraw.Draw(bg_glow)
gd.ellipse((30, 230, 590, 830), fill=BLUE_RGB + (18,))
gd.ellipse((620, 230, 1180, 830), fill=YELLOW_RGB + (14,))
gd.ellipse((1210, 230, 1770, 830), fill=RED_RGB + (18,))
gd.ellipse((560, -180, 1240, 210), fill=(255, 255, 255, 8))
bg_glow = bg_glow.filter(ImageFilter.GaussianBlur(110))
image = Image.alpha_composite(image, bg_glow)

draw = ImageDraw.Draw(image)

# Marco exterior.
draw.rounded_rectangle(
    (22, 22, W - 22, H - 22),
    radius=26,
    outline=LINE_RGB + (190,),
    width=1,
)

# ---------------------------------------------------------------------------
# 7. Titular con "RLHF" en degradado
# ---------------------------------------------------------------------------
prefix = "El Pipeline de Alineación "
accent = "RLHF"
prefix_w = draw.textlength(prefix, font=F_TITLE)
accent_w = draw.textlength(accent, font=F_TITLE)
title_x = (W - prefix_w - accent_w) / 2

text_with_shadow(
    draw,
    (title_x, 44),
    prefix,
    F_TITLE,
    TEXT_RGB + (255,),
    anchor="lt",
)
# Sombra del acento y relleno degradado.
draw.text(
    (title_x + prefix_w, 46),
    accent,
    font=F_TITLE,
    fill=(2, 5, 10, 255),
    anchor="lt",
)
gradient_text(
    image,
    (title_x + prefix_w, 44),
    accent,
    F_TITLE,
    STAGE_STOPS,
    title_x + prefix_w,
    title_x + prefix_w + accent_w,
    anchor="lt",
)
draw = ImageDraw.Draw(image)

draw.text(
    (W // 2, 108),
    "De la imitación supervisada a la optimización con retroalimentación humana",
    font=F_SUBTITLE,
    fill=MUTED_RGB + (255,),
    anchor="mt",
)

gradient_rule(draw, W // 2 - 150, W // 2 + 150, 148, STAGE_STOPS, alpha=180)


# ---------------------------------------------------------------------------
# 8. Tarjetas
# ---------------------------------------------------------------------------
def draw_card(base, stage, x, y):
    """Dibuja una tarjeta de etapa completa."""
    w, h = CARD_W, CARD_H

    # Halo del borde.
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.rounded_rectangle(
        (x, y, x + w, y + h),
        radius=24,
        outline=stage["color"] + (130,),
        width=6,
    )
    glow = glow.filter(ImageFilter.GaussianBlur(20))
    base = Image.alpha_composite(base, glow)

    # Relleno con un leve tinte del color de la etapa.
    top = mix((12, 21, 36), stage["color"], 0.055)
    bottom = (7, 13, 23)
    card = vertical_gradient(w, h, top, bottom)
    card.putalpha(rounded_mask(w, h, 24))
    base.alpha_composite(card, (x, y))

    d = ImageDraw.Draw(base)

    # Borde nítido y línea superior de acento.
    d.rounded_rectangle(
        (x, y, x + w, y + h),
        radius=24,
        outline=stage["color"] + (235,),
        width=2,
    )
    accent_glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    agd = ImageDraw.Draw(accent_glow)
    agd.line([(x + 30, y + 4), (x + w - 30, y + 4)],
             fill=stage["color"] + (140,), width=5)
    accent_glow = accent_glow.filter(ImageFilter.GaussianBlur(6))
    base = Image.alpha_composite(base, accent_glow)
    d = ImageDraw.Draw(base)
    d.line([(x + 30, y + 4), (x + w - 30, y + 4)],
           fill=stage["color"] + (255,), width=2)

    # Número de etapa como marca de agua.
    wm = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(wm).text(
        (x + w - 24, y + 12),
        stage["number"],
        font=F_WATERMARK,
        fill=stage["color"] + (28,),
        anchor="rt",
    )
    base = Image.alpha_composite(base, wm)
    d = ImageDraw.Draw(base)

    # Etiqueta de fase.
    d.ellipse((x + 24, y + 34, x + 32, y + 42), fill=stage["color"] + (255,))
    d.text(
        (x + 40, y + 29),
        stage["label"],
        font=F_STAGE_LABEL,
        fill=stage["light"] + (255,),
        anchor="lt",
    )

    # Círculo del icono.
    icon_cx, icon_cy = x + w // 2, y + 130
    circle_fill = mix((9, 16, 28), stage["color"], 0.10)
    circle_edge = mix((9, 16, 28), stage["color"], 0.38)
    d.ellipse(
        (icon_cx - 68, icon_cy - 68, icon_cx + 68, icon_cy + 68),
        fill=circle_fill + (255,),
        outline=circle_edge + (255,),
        width=1,
    )

    # Icono con glow.
    icon_layer = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
    art = Image.new("RGBA", (120, 120), (0, 0, 0, 0))
    ICONS[stage["icon"]](art)
    icon_layer.alpha_composite(art, (20, 20))
    icon_glow = icon_layer.filter(ImageFilter.GaussianBlur(8))
    base.alpha_composite(icon_glow, (icon_cx - 80, icon_cy - 80))
    base.alpha_composite(icon_glow, (icon_cx - 80, icon_cy - 80))
    base.alpha_composite(icon_layer, (icon_cx - 80, icon_cy - 80))
    d = ImageDraw.Draw(base)

    # Título y subtítulo.
    d.text(
        (x + 32, y + 220),
        stage["title"],
        font=F_CARD_TITLE,
        fill=TEXT_RGB + (255,),
        anchor="lt",
    )
    d.text(
        (x + 32, y + 258),
        stage["subtitle"],
        font=F_CARD_SUB,
        fill=stage["light"] + (255,),
        anchor="lt",
    )

    # Separador.
    divider = mix((9, 16, 28), stage["color"], 0.30)
    d.line([(x + 32, y + 298), (x + w - 32, y + 298)],
           fill=divider + (255,), width=1)
    d.line([(x + 32, y + 298), (x + 86, y + 298)],
           fill=stage["color"] + (255,), width=2)

    # Cuerpo.
    d.text(
        (x + 32, y + 320),
        stage["body1"],
        font=F_BODY,
        fill=BODY_RGB + (255,),
        anchor="lt",
    )
    d.text(
        (x + 32, y + 348),
        stage["body2"],
        font=F_BODY,
        fill=stage["light"] + (255,),
        anchor="lt",
    )

    # Caja de output.
    box = (x + 28, y + 440, x + w - 28, y + 560)
    box_fill = mix((9, 16, 28), stage["color"], 0.12)
    box_edge = mix((9, 16, 28), stage["color"], 0.48)
    d.rounded_rectangle(
        box,
        radius=14,
        fill=box_fill + (255,),
        outline=box_edge + (255,),
        width=1,
    )
    d.rounded_rectangle(
        (x + 44, y + 458, x + 48, y + 542),
        radius=2,
        fill=stage["color"] + (255,),
    )
    d.text(
        (x + 62, y + 476),
        "OUTPUT",
        font=F_OUTPUT_LABEL,
        fill=stage["light"] + (255,),
        anchor="lt",
    )
    d.text(
        (x + 62, y + 504),
        stage["output"],
        font=F_OUTPUT,
        fill=TEXT_RGB + (255,),
        anchor="lt",
    )

    return base


for stage, x in zip(STAGES, CARD_X):
    image = draw_card(image, stage, x, CARD_Y)

draw = ImageDraw.Draw(image)

# ---------------------------------------------------------------------------
# 9. Flechas gruesas entre etapas
# ---------------------------------------------------------------------------
def draw_flow_arrow(base, x, y, source_color, target_color):
    """Flecha gruesa con degradado y brillo."""
    aw, ah = 80, 64
    points = [
        (0, 22), (50, 22), (50, 6), (80, 32),
        (50, 58), (50, 42), (0, 42),
    ]

    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.polygon([(x + px, y + py) for px, py in points],
               fill=target_color + (110,))
    glow = glow.filter(ImageFilter.GaussianBlur(12))
    base = Image.alpha_composite(base, glow)

    stops = [(0.0, source_color),
             (0.5, mix(source_color, WHITE_RGB, 0.35)),
             (1.0, target_color)]
    layer = multi_gradient(aw, ah, stops)
    mask = Image.new("L", (aw, ah), 0)
    ImageDraw.Draw(mask).polygon(points, fill=255)
    layer.putalpha(mask)
    base.alpha_composite(layer, (x, y))

    d = ImageDraw.Draw(base)
    # Reflejo superior para dar sensación de movimiento.
    d.line([(2, 23), (49, 23)], fill=(255, 255, 255, 120), width=2)
    d.line([(51, 10), (74, 31)], fill=(255, 255, 255, 110), width=2)
    return base


image = draw_flow_arrow(image, 565, CARD_Y + CARD_H // 2 - 32,
                        BLUE_RGB, YELLOW_RGB)
image = draw_flow_arrow(image, 1155, CARD_Y + CARD_H // 2 - 32,
                        YELLOW_RGB, RED_RGB)

draw = ImageDraw.Draw(image)

# ---------------------------------------------------------------------------
# 10. Pie de figura
# ---------------------------------------------------------------------------
gradient_rule(draw, 60, 1740, 910, STAGE_STOPS, alpha=100)

draw.text(
    (W // 2, 945),
    "RLHF: Reinforcement Learning from Human Feedback  ·  "
    "SFT: Supervised Fine-Tuning  ·  "
    "PPO: Proximal Policy Optimization  ·  KL: Kullback–Leibler",
    font=F_GLOSSARY,
    fill=SLATE_RGB + (255,),
    anchor="mm",
)

# ---------------------------------------------------------------------------
# 11. Exportación AVIF
# ---------------------------------------------------------------------------
output_dir = Path("images")
output_dir.mkdir(exist_ok=True)
output_path = output_dir / "rlhf_pipeline.avif"
preview_path = output_dir / "rlhf_pipeline.png"
animated_path = output_dir / "rlhf_pipeline_animated.avif"

final_image = image.convert("RGB")
final_image.save(preview_path)
final_image.save(output_path, format="AVIF", quality=92)


def add_energy_pulse(base, px, py, glow_color, fade):
    """Añade un pulso de energía con estela sobre una flecha."""
    if fade <= 0.02:
        return base

    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for dx, radius, alpha in ((-20, 6, 45), (-11, 9, 75), (0, 15, 130)):
        a = int(alpha * fade)
        gd.ellipse(
            (px + dx - radius, py - radius, px + dx + radius, py + radius),
            fill=glow_color + (a,),
        )
    glow = glow.filter(ImageFilter.GaussianBlur(8))
    base = Image.alpha_composite(base, glow)

    d = ImageDraw.Draw(base)
    core = int(235 * fade)
    d.ellipse((px - 3, py - 3, px + 3, py + 3), fill=(255, 255, 255, core))
    return base


# Animación opcional: un pulso recorre las dos flechas.
FRAME_COUNT = 32
frames = []
arrow_y = CARD_Y + CARD_H // 2
for i in range(FRAME_COUNT):
    phase = i / (FRAME_COUNT - 1)
    fade = math.sin(math.pi * phase)
    frame = image.copy()
    frame = add_energy_pulse(frame, 572 + 66 * phase, arrow_y, YELLOW_RGB, fade)
    frame = add_energy_pulse(frame, 1162 + 66 * phase, arrow_y, RED_RGB, fade)
    frames.append(frame.convert("RGB").resize((900, 515), Image.LANCZOS))

frames[0].save(
    animated_path,
    format="AVIF",
    save_all=True,
    append_images=frames[1:],
    duration=80,
    loop=0,
    quality=85,
)

print(f"Imagen guardada en: {output_path}")
print(f"Animación guardada en: {animated_path}")
print(f"Dimensiones: {final_image.size[0]}x{final_image.size[1]} | Modo: {final_image.mode}")

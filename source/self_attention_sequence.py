# pip install Pillow
"""
Self-attention: la secuencia se mira a sí misma.

Dos contextos para la misma palabra «banco». Las flechas muestran qué tokens
reciben más atención y el grosor codifica el peso. Debajo de cada oración
emerge el vector contextual correspondiente, construido como una suma
ponderada de los valores de la secuencia.

Salida: images/self_attention_banco.avif  (1800 x 1200, RGB, calidad 90)
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# 1. Lienzo y sistema de diseño
# ---------------------------------------------------------------------------
W, H = 1800, 1200

BG = "#0B0F19"
CARD_BG = "#0F172A"
CYAN = "#22D3EE"
CYAN_SOFT = "#38BDF8"
AMBER = "#F59E0B"
AMBER_SOFT = "#D97706"
SLATE = "#64748B"
TEXT = "#E2E8F0"
MUTED = "#94A3B8"
LINE = "#1E293B"


def rgb(hex_color):
    value = hex_color.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def mix(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return tuple(round(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


BG_RGB = rgb(BG)
CARD_RGB = rgb(CARD_BG)
CYAN_RGB = rgb(CYAN)
CYAN_SOFT_RGB = rgb(CYAN_SOFT)
AMBER_RGB = rgb(AMBER)
AMBER_SOFT_RGB = rgb(AMBER_SOFT)
SLATE_RGB = rgb(SLATE)
TEXT_RGB = rgb(TEXT)
MUTED_RGB = rgb(MUTED)
LINE_RGB = rgb(LINE)

# ---------------------------------------------------------------------------
# 2. Tipografía
# ---------------------------------------------------------------------------
def load_font(size, bold=False):
    candidates = (
        [
            "C:/Windows/Fonts/arialbd.ttf",
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/Library/Fonts/Arial Bold.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
        if bold
        else [
            "C:/Windows/Fonts/arial.ttf",
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


F_MAIN = load_font(32, bold=True)
F_SUB = load_font(15)
F_CONTEXT = load_font(13, bold=True)
F_TOKEN = load_font(34)
F_TOKEN_BOLD = load_font(36, bold=True)
F_WEIGHT = load_font(12, bold=True)
F_CARD_EYEBROW = load_font(11, bold=True)
F_CARD_TITLE = load_font(19, bold=True)
F_CARD_FORMULA = load_font(16)
F_CARD_NOTE = load_font(12)
F_CARD_LABEL = load_font(10, bold=True)
F_FOOTER = load_font(13)


def text_with_shadow(draw, xy, text, font, fill, anchor="la",
                     shadow=(5, 8, 14), offset=(0, 2)):
    draw.text(
        (xy[0] + offset[0], xy[1] + offset[1]),
        text, font=font, fill=shadow, anchor=anchor,
    )
    draw.text(xy, text, font=font, fill=fill, anchor=anchor)


# ---------------------------------------------------------------------------
# 3. Curvas de atención y flechas
# ---------------------------------------------------------------------------
def bezier(p0, p1, p2, p3, steps=90):
    points = []
    for i in range(steps + 1):
        t = i / steps
        u = 1.0 - t
        x = (u ** 3) * p0[0] + 3 * (u ** 2) * t * p1[0] + 3 * u * (t ** 2) * p2[0] + (t ** 3) * p3[0]
        y = (u ** 3) * p0[1] + 3 * (u ** 2) * t * p1[1] + 3 * u * (t ** 2) * p2[1] + (t ** 3) * p3[1]
        points.append((x, y))
    return points


def attention_arrow(draw, p0, p1, p2, p3, color, width, head):
    """Curva Bézier con una punta de flecha que apunta hacia el token."""
    points = bezier(p0, p1, p2, p3)
    draw.line(points, fill=color, width=width, joint="curve")
    x_end, y_end = points[-1]
    draw.polygon(
        [
            (x_end, y_end + head * 0.65),
            (x_end - head * 0.50, y_end - head * 0.35),
            (x_end + head * 0.50, y_end - head * 0.35),
        ],
        fill=color,
    )


# ---------------------------------------------------------------------------
# 4. Tokens y tarjeta del vector contextual
# ---------------------------------------------------------------------------
def draw_token(draw, cx, cy, text, font, color, capsule=None):
    """Dibuja una palabra; si capsule está definido, la resalta."""
    if capsule is not None:
        bbox = draw.textbbox((cx, cy), text, font=font, anchor="mm")
        draw.rounded_rectangle(
            (bbox[0] - 16, bbox[1] - 10, bbox[2] + 16, bbox[3] + 10),
            radius=12,
            fill=CARD_RGB,
            outline=capsule,
            width=2,
        )
    draw.text((cx, cy), text, font=font, fill=color, anchor="mm")


def draw_context_card(image, draw, x, y, w, h, accent, formula, note):
    """Tarjeta que representa el vector contextual resultante."""
    draw.rounded_rectangle(
        (x, y, x + w, y + h),
        radius=18,
        fill=CARD_RGB,
        outline=accent,
        width=1,
    )

    draw.text((x + 32, y + 22), "VECTOR CONTEXTUAL DE «BANCO»", font=F_CARD_EYEBROW, fill=accent)
    draw.text(
        (x + 32, y + 46),
        "banco_ctx = suma ponderada",
        font=F_CARD_TITLE,
        fill=TEXT_RGB,
    )
    draw.text(
        (x + 32, y + 82),
        formula,
        font=F_CARD_FORMULA,
        fill=TEXT_RGB,
    )
    draw.text(
        (x + 32, y + 112),
        note,
        font=F_CARD_NOTE,
        fill=MUTED_RGB,
    )

    # Pequeño vector resultante: barras de distinta magnitud.
    bars_x = x + w - 200
    bars_base = y + h - 28
    heights = (34, 58, 44, 72, 48, 84, 56, 68)
    draw.text(
        (bars_x + 76, y + 22),
        "v_ctx",
        font=F_CARD_LABEL,
        fill=accent,
        anchor="ma",
    )
    for index, bar_height in enumerate(heights):
        bx = bars_x + index * 20
        bar_color = mix(accent, (255, 255, 255), 0.12 + 0.03 * (index % 3))
        draw.rounded_rectangle(
            (bx, bars_base - bar_height, bx + 12, bars_base),
            radius=3,
            fill=bar_color,
        )
    draw.line(
        [(bars_x, bars_base + 2), (bars_x + 152, bars_base + 2)],
        fill=LINE_RGB,
        width=1,
    )


# ---------------------------------------------------------------------------
# 5. Fondo y cabecera
# ---------------------------------------------------------------------------
image = Image.new("RGBA", (W, H), BG_RGB + (255,))
draw = ImageDraw.Draw(image)

text_with_shadow(
    draw,
    (900, 50),
    "Self-Attention: la secuencia se mira a sí misma",
    F_MAIN,
    TEXT_RGB,
    anchor="mm",
)
draw.text(
    (900, 90),
    "Una misma palabra, dos contextos: el vector de «banco» cambia según las palabras que la rodean.",
    font=F_SUB,
    fill=MUTED_RGB,
    anchor="mm",
)
draw.line([(70, 122), (1730, 122)], fill=LINE_RGB, width=1)

# ---------------------------------------------------------------------------
# 6. Fila 1: El banco está cerca del río
# ---------------------------------------------------------------------------
draw.text(
    (80, 160),
    "CONTEXTO 1 · GEOGRAFÍA",
    font=F_CONTEXT,
    fill=CYAN_RGB,
    anchor="la",
)

row1_y = 330
row1_tokens = [
    ("El", 520, F_TOKEN, MUTED_RGB, None),
    ("banco", 780, F_TOKEN_BOLD, TEXT_RGB, CYAN_RGB),
    ("está", 1000, F_TOKEN, (203, 213, 225), None),
    ("cerca", 1200, F_TOKEN, (125, 211, 252), None),
    ("del", 1390, F_TOKEN, MUTED_RGB, None),
    ("río", 1570, F_TOKEN_BOLD, CYAN_RGB, None),
]
for token, cx, font, color, capsule in row1_tokens:
    draw_token(draw, cx, row1_y, token, font, color, capsule)

# Arcos de atención de «banco»: río (alta), cerca (media), El (baja).
attention_arrow(
    draw, (800, 298), (940, 180), (1490, 180), (1570, 304),
    CYAN_RGB, width=8, head=17,
)
attention_arrow(
    draw, (780, 298), (890, 240), (1120, 240), (1200, 304),
    CYAN_SOFT_RGB, width=5, head=13,
)
attention_arrow(
    draw, (760, 298), (660, 250), (540, 250), (520, 304),
    SLATE_RGB, width=3, head=11,
)

# Pesos bajo las palabras atendidas.
for label, cx, color in (
    ("α = 0.58", 1570, CYAN_RGB),
    ("α = 0.24", 1200, CYAN_SOFT_RGB),
    ("α = 0.08", 520, SLATE_RGB),
):
    draw.text((cx, 372), label, font=F_WEIGHT, fill=color, anchor="mm")

# Conector vertical: de banco al vector contextual.
draw.line(
    [(780, 362), (780, 409)],
    fill=CYAN_RGB,
    width=2,
)
draw.ellipse((775, 357, 785, 367), fill=CYAN_RGB)
draw.text((792, 383), "v_ctx", font=F_CARD_LABEL, fill=CYAN_RGB, anchor="lm")

draw_context_card(
    image,
    draw,
    280, 410, 1240, 180,
    accent=CYAN_RGB,
    formula="= 0.58 · v(río) + 0.24 · v(cerca) + 0.08 · v(El) + 0.10 · v(resto)",
    note="El contexto «río» domina la representación.",
)

# ---------------------------------------------------------------------------
# 7. Fila 2: Voy al banco a cobrar
# ---------------------------------------------------------------------------
draw.line([(70, 630), (1730, 630)], fill=LINE_RGB, width=1)
draw.text(
    (80, 670),
    "CONTEXTO 2 · FINANZAS",
    font=F_CONTEXT,
    fill=AMBER_RGB,
    anchor="la",
)

row2_y = 830
row2_tokens = [
    ("Voy", 470, F_TOKEN, MUTED_RGB, None),
    ("al", 650, F_TOKEN, (203, 213, 225), None),
    ("banco", 780, F_TOKEN_BOLD, TEXT_RGB, AMBER_RGB),
    ("a", 930, F_TOKEN, MUTED_RGB, None),
    ("cobrar", 1110, F_TOKEN_BOLD, AMBER_RGB, None),
]
for token, cx, font, color, capsule in row2_tokens:
    draw_token(draw, cx, row2_y, token, font, color, capsule)

# Arcos de atención de «banco»: cobrar (alta), Voy (media), a (baja).
attention_arrow(
    draw, (800, 798), (900, 700), (1050, 700), (1110, 804),
    AMBER_RGB, width=8, head=17,
)
attention_arrow(
    draw, (760, 798), (650, 730), (520, 730), (470, 804),
    AMBER_SOFT_RGB, width=5, head=13,
)
attention_arrow(
    draw, (780, 798), (850, 770), (900, 770), (930, 804),
    SLATE_RGB, width=3, head=11,
)

for label, cx, color in (
    ("α = 0.64", 1110, AMBER_RGB),
    ("α = 0.16", 470, AMBER_SOFT_RGB),
    ("α = 0.07", 930, SLATE_RGB),
):
    draw.text((cx, 872), label, font=F_WEIGHT, fill=color, anchor="mm")

draw.line(
    [(780, 862), (780, 909)],
    fill=AMBER_RGB,
    width=2,
)
draw.ellipse((775, 857, 785, 867), fill=AMBER_RGB)
draw.text((792, 883), "v_ctx", font=F_CARD_LABEL, fill=AMBER_RGB, anchor="lm")

draw_context_card(
    image,
    draw,
    280, 910, 1240, 180,
    accent=AMBER_RGB,
    formula="= 0.64 · v(cobrar) + 0.16 · v(Voy) + 0.07 · v(a) + 0.13 · v(resto)",
    note="El contexto «cobrar» domina la representación.",
)

# ---------------------------------------------------------------------------
# 8. Pie de figura
# ---------------------------------------------------------------------------
draw.line([(70, 1125), (1730, 1125)], fill=LINE_RGB, width=1)
draw.text(
    (900, 1152),
    "El grosor de cada flecha representa el peso de atención que «banco» asigna a cada palabra.",
    font=F_FOOTER,
    fill=MUTED_RGB,
    anchor="mm",
)
draw.text(
    (900, 1178),
    "El vector contextual es la suma ponderada de los valores de la secuencia.",
    font=F_FOOTER,
    fill=SLATE_RGB,
    anchor="mm",
)

# ---------------------------------------------------------------------------
# 9. Exportación AVIF
# ---------------------------------------------------------------------------
output_dir = Path("images")
output_dir.mkdir(exist_ok=True)
output_path = output_dir / "self_attention_banco.avif"

final_image = image.convert("RGB")
final_image.save(output_path, format="AVIF", quality=90)

print(f"Imagen guardada en: {output_path}")
print(f"Dimensiones: {final_image.size[0]}x{final_image.size[1]} | Modo: {final_image.mode}")
